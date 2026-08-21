# 📖 PDF Topic Search

> Search a word across any PDF and get more than a page number — get the **chapter**, the **surrounding context**, and an on-demand **AI-generated topic explanation** grounded in exactly how the word is used there.

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)
![Gemini API](https://img.shields.io/badge/Gemini_API-Free_Tier-4285F4?logo=googlegemini&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🧠 The Problem

Ctrl+F tells you *where* a word appears in a PDF. It doesn't tell you *what it means there*.

Textbook PDFs are full of words that mean completely different things depending on where they show up. Take the word **"drop"**:

- In a **Database Management** chapter → a SQL command (`DROP TABLE`)
- In a **UI/Programming** chapter → drag-and-drop, drop-down menus
- In a **Software Economics** chapter → falling hardware prices

A student searching a 700-page textbook has no fast way to know *which* meaning applies to *which* occurrence — until now.

## ✨ The Solution

Upload any PDF, search a word, and get a table of every occurrence with:

| Page | Chapter | Context | AI Explanation |
|------|---------|---------|-----------------|
| 530 | Chapter-09 | "...using a **drop**-down list, a set of option buttons..." | **Topic: UI/Programming concept** — refers to a UI element that expands to show selectable options. |
| 25 | Chapter-01 | "...their prices **dropped** dramatically..." | **Topic: Computer Hardware Costs** — describes hardware becoming cheaper over time. |

The AI explanation is only generated **on demand** (when you click "Explain"), keeping the free-tier API quota efficient instead of burning it on every search result.

---

## 🏗️ Architecture

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
1. Try to read the PDF's embedded bookmarks/TOC (`doc.get_toc()`) — fast and accurate when available.
2. **Fallback:** if no TOC exists, detect headings by analyzing font sizes across the document — text noticeably larger than the body-text size, filtered to remove watermarks, boilerplate, and TOC-page artifacts, then merged across adjacent lines.
3. Convert chapter start-pages into page **ranges**, so any matched page can be mapped to its chapter.

**How the AI explanation stays cheap:**
- `/search` returns raw matches instantly — no AI call.
- `/explain` is called only when the user clicks a specific row's "Explain" button, sending just that occurrence's word + surrounding context + chapter to Gemini.
- Automatic retry logic handles transient `503` (server busy) errors; `429` (rate limit) errors are surfaced clearly instead of silently retried, since retrying burns quota faster.

---

## 🚀 Features

- 📤 **Upload any PDF** — processed and indexed in memory per upload (unique ID per session)
- 🔍 **Instant word search** across every page, with chapter mapping
- 🧭 **Dual chapter-detection strategy** — embedded TOC first, font-size heuristic fallback second
- 🤖 **On-demand AI disambiguation** via Gemini — topic label + beginner-friendly explanation, grounded strictly in the surrounding text (not generic dictionary definitions)
- ⚡ **Quota-conscious design** — AI calls happen only when explicitly requested, with retry/backoff for transient errors
- 🎨 **Clean React UI** — upload status, match count, per-row explain buttons with loading states

---

## 🛠️ Tech Stack

**Backend**
- [Flask](https://flask.palletsprojects.com/) — lightweight Python web framework
- [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) — PDF parsing, text extraction, TOC/font analysis
- [google-genai](https://pypi.org/project/google-genai/) — Gemini API client
- [python-dotenv](https://pypi.org/project/python-dotenv/) — environment variable management
- [flask-cors](https://pypi.org/project/Flask-Cors/) — cross-origin support for the React frontend

**Frontend**
- [React](https://react.dev/) (via [Vite](https://vitejs.dev/)) — UI
- Plain CSS — no framework overhead

**AI**
- [Gemini API](https://aistudio.google.com/) (free tier, `gemini-flash-latest`)

All tools used are **free-tier / open-source** — no paid APIs or subscriptions required.

---

## 📦 Project Structure

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

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- A free [Gemini API key](https://aistudio.google.com/apikey)

### 1. Clone the repo
```bash
git clone https://github.com/<your-username>/PDFProj.git
cd PDFProj
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
Open a **new terminal**:
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
4. Click "Explain" on any result to get an AI-generated, context-specific explanation

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload a PDF (`multipart/form-data`, field: `file`). Returns `pdf_id`, page count, chapters found. |
| `GET`  | `/search?word=<term>&pdf_id=<id>` | Search a word across the uploaded PDF. Returns all matches with page, chapter, and context. |
| `GET`  | `/explain?word=<term>&context=<text>&chapter=<name>` | Get an AI-generated topic + explanation for a specific occurrence. |

---

## 📸 Screenshots

> _Add screenshots here once you have final polished ones — search results table, explain-in-action, and the upload screen work well._

| Search Results | AI Explanation |
|---|---|
| _screenshot here_ | _screenshot here_ |

---

## 🗺️ Possible Future Improvements

- Persistent storage (SQLite/PostgreSQL) instead of in-memory PDF storage
- Multi-word / phrase search
- Highlight matched word directly on a rendered PDF page
- Deploy backend (Render) + frontend (Vercel) for a live demo link
- User accounts to save previously uploaded PDFs

---

## 📄 License

MIT — free to use, modify, and share.

---

*Built as a portfolio project demonstrating PDF processing, information retrieval, and practical LLM API integration — using entirely free-tier tools.*
