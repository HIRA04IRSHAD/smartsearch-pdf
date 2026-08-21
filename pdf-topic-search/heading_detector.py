import fitz
import re

def detect_headings_by_font(doc):
    font_sizes = {}

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    size = round(span["size"])
                    text = span["text"].strip()
                    if text:
                        font_sizes[size] = font_sizes.get(size, 0) + len(text)

    if not font_sizes:
        return []

    body_size = max(font_sizes, key=font_sizes.get)

    # --- First pass: collect all candidate lines ---
    candidates = []  # list of (text, page_num, size)
    text_occurrence_count = {}  # text -> how many times it repeats across pages

    for page_index in range(doc.page_count):
        page = doc[page_index]
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                line_text = ""
                max_size = 0

                for span in line["spans"]:
                    line_text += span["text"]
                    max_size = max(max_size, round(span["size"]))

                line_text = line_text.strip()
                if not line_text:
                    continue

                text_occurrence_count[line_text] = text_occurrence_count.get(line_text, 0) + 1
                candidates.append((line_text, page_index + 1, max_size))

    # --- Filtering rules ---
    headings = []
    max_repeats_allowed = doc.page_count * 0.05  # if a line repeats on more than 5% of pages, treat as watermark/boilerplate

    for line_text, page_num, size in candidates:
        # rule 1: font must be clearly bigger than body text
        if size < body_size + 3:
            continue

        # rule 2: must be a reasonably short line (headings aren't paragraphs)
        if not (3 < len(line_text) < 80):
            continue

        # rule 3: skip lines that look like TOC entries (dots or page ranges)
        if re.search(r"\.{3,}", line_text) or re.search(r"\d+\s*[-–]\s*\d+$", line_text):
            continue

        # rule 4: skip repeated boilerplate (watermarks, headers/footers)
        if text_occurrence_count[line_text] > max_repeats_allowed:
            continue

        # rule 5: skip lines that are mostly numbers/symbols
        letters = sum(c.isalpha() for c in line_text)
        if letters < len(line_text) * 0.5:
            continue

        headings.append([1, line_text, page_num])

    return merge_adjacent_headings(headings)

def merge_adjacent_headings(headings):
    """
    Merges consecutive heading candidates that are on the same page
    (they're likely parts of a single multi-line title).
    """
    if not headings:
        return []

    merged = [headings[0]]

    for current in headings[1:]:
        last = merged[-1]
        # if same page as the previous heading, merge the text together
        if current[2] == last[2]:
            merged[-1] = [last[0], last[1] + " " + current[1], last[2]]
        else:
            merged.append(current)

    return merged

if __name__ == "__main__":
    doc = fitz.open("test.pdf")
    headings = detect_headings_by_font(doc)

    print(f"Detected {len(headings)} potential headings:\n")
    for h in headings[:60]:
        level, title, page = h
        print(f"Page {page} | {title}")

    doc.close()