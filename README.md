<div align="center">

# PDF Topic Search

**Search a word across any PDF and get more than a page number.**
Get the chapter, the surrounding context, and an on demand AI generated topic explanation grounded in exactly how the word is used there.

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)
![Gemini API](https://img.shields.io/badge/Gemini_API-Free_Tier-4285F4?logo=googlegemini&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

</div>

---

## The Problem

Ctrl+F tells you where a word appears in a PDF. It doesn't tell you what it means there.

Textbook PDFs are full of words that mean completely different things depending on where they show up. Take the word **"drop"**:

| Chapter | What "drop" means there |
|---|---|
| Database Management | A SQL command, `DROP TABLE` |
| UI / Programming | Drag and drop, drop down menus |
| Software Economics | Falling hardware prices |

A student searching a 700 page textbook has no fast way to know which meaning applies to which occurrence, until now.

## The Solution

Upload any PDF and search a word. Every occurrence comes back with its page, chapter, and surrounding text, so you can scan and judge for yourself which occurrence matches what you're studying. If a snippet alone isn't enough, one click gets you an AI generated summary grounded in that exact context.

| Step | What happens |
|---|---|
| 1. Search | Type the word, get every occurrence instantly. No AI call yet, so it's fast. |
| 2. Scan | Read the context column for each row and shortlist the ones that look relevant. |
| 3. Explain | Click "Explain" on a shortlisted row to get a focused topic label and a one to two line summary of what the word means there. |
| 4. Finalize | Use that summary to confirm or rule out the occurrence, and move on to studying the right one. |

This keeps search itself instant and keeps the free AI quota efficient, since it's only spent on the rows you actually want confirmed.

<div align="center">

| Search Results | AI Explanation |
|---|---|
| Page, chapter, and context for every match | Topic + plain language meaning, on click |

</div>

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
                             │  TOC extraction   │
                             │  + font-based     │
                             │  heading fallback │
                             └──────────────────┘
```

**How chapter detection works**

| Step | Approach |
|---|---|
| 1 | Try to read the PDF's embedded Table of Contents (TOC), the bookmarks panel visible in most PDF readers, via `doc.get_toc()`. Fast and accurate when present. |
| 2 | Fallback: if no TOC exists, detect headings by font size. Text noticeably larger than body text is treated as a heading candidate, then filtered to remove watermarks, boilerplate, and TOC page artifacts, and merged across adjacent lines. |
| 3 | Convert chapter start pages into page ranges, so any matched page maps back to its chapter. |

**How the AI explanation stays cheap**

| Behavior | Why |
|---|---|
| `/search` never calls the AI | Keeps search instant regardless of how many matches there are. |
| `/explain` is called only on click | Only the rows the student actually wants confirmed use up quota. |
| `503` errors retry automatically | Server busy errors are transient, so a short backoff usually resolves them. |
| `429` errors are surfaced, not retried | Rate limit errors mean quota is already gone; retrying immediately would waste more of it. |

---

## Features

| Feature | Details |
|---|---|
| PDF upload | Any PDF is processed and indexed in memory per upload, with a unique ID per session. |
| Instant word search | Every page is searched, with results mapped to their chapter. |
| Dual chapter detection | Embedded TOC first, font size heuristic as a fallback. |
| On demand AI disambiguation | Topic label plus a beginner friendly explanation, grounded strictly in the surrounding text rather than a generic dictionary definition. |
| Quota conscious design | AI calls happen only when requested, with retry/backoff for transient errors. |
| Clean React UI | Upload status, match count, and per row explain buttons with loading states. |

---

## Tech Stack

| Layer | Tools |
|---|---|
| Backend | [Flask](https://flask.palletsprojects.com/), [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/), [google-genai](https://pypi.org/project/google-genai/), [python-dotenv](https://pypi.org/project/python-dotenv/), [flask-cors](https://pypi.org/project/Flask-Cors/) |
| Frontend | [React](https://react.dev/) via [Vite](https://vitejs.dev/), plain CSS |
| AI | [Gemini API](https://aistudio.google.com/), free tier, `gemini-flash-latest` |

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

**Prerequisites**

| Requirement | Notes |
|---|---|
| Python 3.10+ | For the Flask backend |
| Node.js 18+ | For the React frontend |
| Gemini API key | Free, from [Google AI Studio](https://aistudio.google.com/apikey) |

**1. Clone the repo**
```bash
git clone https://github.com/<your-username>/smartsearch-pdf.git
cd smartsearch-pdf
```

**2. Backend setup**
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

**3. Frontend setup** (in a new terminal)
```bash
cd pdf-search-frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`

**4. Use it**

| Step | Action |
|---|---|
| 1 | Open `http://localhost:5173` |
| 2 | Upload a PDF |
| 3 | Search a word |
| 4 | Click "Explain" on any result for a context specific summary |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload` | Upload a PDF (`multipart/form-data`, field: `file`). Returns `pdf_id`, page count, chapters found. |
| `GET` | `/search?word=<term>&pdf_id=<id>` | Search a word across the uploaded PDF. Returns all matches with page, chapter, and context. |
| `GET` | `/explain?word=<term>&context=<text>&chapter=<name>` | Get an AI generated topic and explanation for a specific occurrence. |

---

## Possible Future Improvements

| Idea | Impact |
|---|---|
| Persistent storage (SQLite/PostgreSQL) | Uploaded PDFs survive server restarts |
| Multi word / phrase search | More flexible queries |
| Highlight matched word on a rendered PDF page | Visual confirmation, no more guessing from a snippet |
| Deploy backend (Render) and frontend (Vercel) | A live, shareable demo link |
| User accounts | Save and revisit previously uploaded PDFs |

---

## License

This project uses the **MIT License**, one of the most common open source licenses. In short: anyone can use, copy, modify, and share this code, for free, for any purpose including commercial use, as long as the original copyright notice is kept. The code comes with no warranty; you use it as is.

---

<div align="center">

*Built as a portfolio project demonstrating PDF processing, information retrieval, and practical LLM API integration, using entirely free tier tools.*

</div>