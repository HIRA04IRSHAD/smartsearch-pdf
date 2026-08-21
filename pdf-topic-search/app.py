from flask import Flask, jsonify, request
import fitz
import os
import time
import uuid
from dotenv import load_dotenv
from google import genai
from flask_cors import CORS
from heading_detector import detect_headings_by_font

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# in-memory storage: pdf_id -> {"doc": ..., "chapter_ranges": ...}
pdf_store = {}


def build_chapter_ranges(toc, total_pages):
    ranges = []
    for i, entry in enumerate(toc):
        level, title, start_page = entry
        if i + 1 < len(toc):
            end_page = toc[i + 1][2] - 1
        else:
            end_page = total_pages
        ranges.append({"title": title, "start_page": start_page, "end_page": end_page})
    return ranges


def get_chapter_for_page(page_num, chapter_ranges):
    for ch in chapter_ranges:
        if ch["start_page"] <= page_num <= ch["end_page"]:
            return ch["title"]
    return "Unknown"


def search_word(doc, chapter_ranges, search_term):
    """
    Searches for a word across all pages and returns a bigger,
    sentence-aware context window so the AI explanation has enough
    information to work with.
    """
    results = []
    search_term_lower = search_term.lower()

    for page_index in range(doc.page_count):
        page = doc[page_index]
        text = page.get_text()

        if search_term_lower in text.lower():
            actual_page_num = page_index + 1
            lower_text = text.lower()
            idx = lower_text.find(search_term_lower)

            # bigger window: 200 chars before and after instead of 60
            start = max(0, idx - 200)
            end = min(len(text), idx + 200)
            raw_context = text[start:end].replace("\n", " ").strip()

            # trim to the nearest sentence boundary so it's not a mid-sentence fragment
            first_period = raw_context.find(". ")
            if first_period != -1 and first_period < 100:
                raw_context = raw_context[first_period + 2:]

            last_period = raw_context.rfind(". ")
            if last_period != -1 and last_period > len(raw_context) - 100:
                raw_context = raw_context[:last_period + 1]

            chapter = get_chapter_for_page(actual_page_num, chapter_ranges)

            results.append({
                "page": actual_page_num,
                "chapter": chapter,
                "context": raw_context
            })

    return results


def get_topic_explanation(word, context, chapter, max_retries=1):
    """
    Sends the word + context to Gemini and asks for a short, beginner-friendly
    topic label + explanation, grounded strictly in the given context.
    """
    prompt = f"""A first-year engineering student is reading a textbook and came across this word in the text below. Help them understand it.

Word: "{word}"
Chapter: {chapter}
Text from the book: "{context}"

Instructions:
- Base your answer ONLY on how the word is used in the text above, not general dictionary meanings.
- If the text doesn't give enough context to be sure, say so honestly instead of guessing.
- Explain in very simple, beginner-friendly language, as if teaching a first-year student who is new to this topic.
- Keep the explanation to 1-2 short sentences, no jargon without explaining it.

Respond in this exact format, nothing else:
Topic: <short topic/subject area, 2-5 words>
Explanation: <1-2 simple sentences>
"""

    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            error_str = str(e)

            # rate limit: don't burn more quota retrying immediately
            if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                raise Exception(
                    "RATE_LIMIT: You're sending requests too fast. Please wait about 30 seconds and try again."
                )

            # server busy (503): safe to retry once after a short wait
            if attempt < max_retries:
                print(f"Gemini call failed (attempt {attempt + 1}), retrying...")
                time.sleep(3)
            else:
                raise


@app.route("/search", methods=["GET"])
def search():
    word = request.args.get("word", "")
    pdf_id = request.args.get("pdf_id", "")

    if not word:
        return jsonify({"error": "Please provide a 'word' query parameter"}), 400

    if not pdf_id or pdf_id not in pdf_store:
        return jsonify({"error": "Invalid or missing pdf_id. Please upload a PDF first."}), 400

    entry = pdf_store[pdf_id]
    results = search_word(entry["doc"], entry["chapter_ranges"], word)

    return jsonify({
        "word": word,
        "total_matches": len(results),
        "results": results
    })


@app.route("/explain", methods=["GET"])
def explain():
    word = request.args.get("word", "")
    context = request.args.get("context", "")
    chapter = request.args.get("chapter", "")

    if not word or not context:
        return jsonify({"error": "word and context are required"}), 400

    try:
        explanation = get_topic_explanation(word, context, chapter)
        return jsonify({
            "word": word,
            "chapter": chapter,
            "explanation": explanation
        })
    except Exception as e:
        print(f"Explain error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/upload", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    # generate a unique id and save the file
    pdf_id = str(uuid.uuid4())
    save_path = os.path.join(UPLOAD_FOLDER, f"{pdf_id}.pdf")
    file.save(save_path)

    # process the pdf
    uploaded_doc = fitz.open(save_path)
    uploaded_toc = uploaded_doc.get_toc()

    if not uploaded_toc:
        uploaded_toc = detect_headings_by_font(uploaded_doc)

    uploaded_chapter_ranges = build_chapter_ranges(uploaded_toc, uploaded_doc.page_count)

    # store in memory for later search/explain calls
    pdf_store[pdf_id] = {
        "doc": uploaded_doc,
        "chapter_ranges": uploaded_chapter_ranges
    }

    return jsonify({
        "pdf_id": pdf_id,
        "filename": file.filename,
        "total_pages": uploaded_doc.page_count,
        "chapters_found": len(uploaded_chapter_ranges)
    })


if __name__ == "__main__":
    app.run(debug=True)