# PDF Topic Search

> Search a word across any PDF and get more than a page number: get the chapter, the surrounding context, and an on demand AI generated topic explanation grounded in exactly how the word is used there.

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)
![Gemini API](https://img.shields.io/badge/Gemini_API-Free_Tier-4285F4?logo=googlegemini&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

## The Problem

Ctrl+F tells you where a word appears in a PDF. It doesn't tell you what it means there.

Textbook PDFs are full of words that mean completely different things depending on where they show up. Take the word "drop":

- In a Database Management chapter, it's a SQL command (`DROP TABLE`)
- In a UI/Programming chapter, it's drag and drop, drop down menus
- In a Software Economics chapter, it's falling hardware prices

A student searching a 700 page textbook has no fast way to know which meaning applies to which occurrence, until now.

## The Solution

Upload any PDF and search a word. You get every occurrence listed with its page, chapter, and the surrounding text, so you can quickly scan and judge for yourself which occurrence matches the topic you're actually studying.

If the context snippet alone isn't enough to be sure, click "Explain" on that specific row. This sends just that occurrence (word plus its surrounding text plus chapter) to an AI model, which returns a short topic label and a one to two line explanation of what the word means in that exact context, not a generic dictionary definition.

So the workflow looks like:
1. Search the word
2. Scan the context column for each occurrence
3. If a row's context looks like a possible match for your topic, click "Explain" to get a small, focused summary confirming (or ruling out) that it's the right meaning
4. Use that summary to finalize which occurrence is actually relevant to what you're studying

This keeps things fast (search itself needs no AI call) and keeps the AI's free quota efficient, since it's only used for the specific rows you actually want confirmed.

---

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  React Frontend │  HTTP   │   Flask Backend   │  HTTP   │   Gemini API    │
│   (Vite, 5173)  │────────▶│  (Flask, 5000)    │────────▶│  (on-demand)    │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                      │
                                      ▼
                             ┌──────────────────┐
                             │  PyMuPDF (fitz)   │
                             │  - TOC extraction │
                             │  - Font-based     │
                             │    heading        │
                             │    fallback       │
                             └──────────────────┘
```

**How chapter detection works:**
1. Try to read the PDF's embedded Table of Contents, or TOC (the bookmarks panel you see in a PDF reader's sidebar), using `doc.get_toc()`. This is fast and accurate when the PDF has it.
2. Fallback: if no TOC exists, detect headings by analyzing font sizes across the document. Text noticeably larger than the body text size is treated as a heading candidate, filtered to remove watermarks, boilerplate, and TOC page artifacts, then merged across adjacent lines.
3. Convert chapter start pages into page ranges, so any matched page can be mapped back to its chapter.

**How the AI explanation stays cheap:**
- `/search` returns raw matches instantly, with no AI call involved.
- `/explain` is called only when the user clicks a specific row's "Explain" button, sending just that occurrence's word, surrounding context, and chapter to Gemini.
- Automatic retry logic handles transient `503` (server busy) errors. `429` (rate limit) errors are surfaced clearly instead of silently retried, since retrying just burns quota faster.

---

## Features

- Upload any PDF, processed and indexed in memory per upload with a unique ID per session
- Instant word search across every page, with chapter mapping
- Dual chapter detection strategy: embedded TOC first, font size heuristic fallback second
- On demand AI disambiguation via Gemini: topic label plus a beginner friendly explanation, grounded strictly in the surrounding text rather than generic dictionary definitions
- Quota conscious design: AI calls happen only when explicitly requested, with retry/backoff for transient errors
- Clean React UI with upload status, match count, and per row explain buttons with loading states

---

## Tech Stack

**Backend**
- [Flask](https://flask.palletsprojects.com/): lightweight Python web framework
- [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/): PDF parsing, text extraction, TOC/font analysis
- [google-genai](https://pypi.org/project/google-genai/): Gemini API client
- [python-dotenv](https://pypi.org/project/python-dotenv/): environment variable management
- [flask-cors](https://pypi.org/project/Flask-Cors/): cross origin support for the React frontend

**Frontend**
- [React](https://react.dev/) (via [Vite](https://vitejs.dev/)) for the UI
- Plain CSS, no framework overhead

**AI**
- [Gemini API](https://aistudio.google.com/) (free tier, `gemini-flash-latest`)

All tools used are free tier or open source. No paid APIs or subscriptions required.

---

## Project Structure

```
PDFProj/
├── pdf-topic-search/          # Flask backend
│   ├── app.py                 # Main server: routes, search, Gemini integration
│   ├── heading_detector.py    # Font-based TOC fallback
│   ├── uploads/                # Uploaded PDFs (gitignored)
│   ├── .env                    # GEMINI_API_KEY (gitignored, never commit this)
│   └── .gitignore
│
└── pdf-search-frontend/        # React (Vite) frontend
    ├── src/
    │   ├── App.jsx              # Upload, search, and explain UI
    │   ├── App.css
    │   └── main.jsx
    └── .gitignore
```

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- A free [Gemini API key](https://aistudio.google.com/apikey)

### 1. Clone the repo
```bash
git clone https://github.com/<your-username>/smartsearch-pdf.git
cd smartsearch-pdf
```

### 2. Backend setup
```bash
cd pdf-topic-search
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install flask pymupdf flask-cors python-dotenv google-genai
```

Create a `.env` file inside `pdf-topic-search/`:
```
GEMINI_API_KEY=your_api_key_here
```

Run the backend:
```bash
python app.py
```
Server runs at `http://127.0.0.1:5000`

### 3. Frontend setup
Open a new terminal:
```bash
cd pdf-search-frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`

### 4. Use it
1. Open `http://localhost:5173` in your browser
2. Upload a PDF
3. Search a word
4. Click "Explain" on any result to get an AI generated, context specific explanation

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload a PDF (`multipart/form-data`, field: `file`). Returns `pdf_id`, page count, chapters found. |
| `GET`  | `/search?word=<term>&pdf_id=<id>` | Search a word across the uploaded PDF. Returns all matches with page, chapter, and context. |
| `GET`  | `/explain?word=<term>&context=<text>&chapter=<name>` | Get an AI generated topic and explanation for a specific occurrence. |

---

## Possible Future Improvements

- Persistent storage (SQLite/PostgreSQL) instead of in memory PDF storage
- Multi word / phrase search
- Highlight the matched word directly on a rendered PDF page
- Deploy backend (Render) and frontend (Vercel) for a live demo link
- User accounts to save previously uploaded PDFs

---

## License

This project uses the MIT License, one of the most common open source licenses. In short, it means anyone can use, copy, modify, and share this code, for free, for any purpose (including commercial), as long as the original copyright notice is kept. It also means the code comes with no warranty; you use it as is.

---

*Built as a portfolio project demonstrating PDF processing, information retrieval, and practical LLM API integration, using entirely free tier tools.*