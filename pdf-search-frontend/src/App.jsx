import { useState } from "react";
import "./App.css";

const BACKEND_URL = "http://127.0.0.1:5000";

function App() {
  const [pdfId, setPdfId] = useState(null);
  const [pdfInfo, setPdfInfo] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  const [word, setWord] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // explanations[index] = { topic, explanation } or { error }
  const [explanations, setExplanations] = useState({});
  const [explainLoading, setExplainLoading] = useState({});

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setUploadError("");
    setPdfId(null);
    setPdfInfo(null);
    setResults([]);
    setExplanations({});

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${BACKEND_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      if (data.error) {
        setUploadError(data.error);
      } else {
        setPdfId(data.pdf_id);
        setPdfInfo(data);
      }
    } catch (err) {
      setUploadError("Could not upload file. Is the backend running?");
    } finally {
      setUploading(false);
    }
  };

  const handleSearch = async () => {
    if (!word.trim() || !pdfId) return;

    setLoading(true);
    setError("");
    setResults([]);
    setExplanations({});

    try {
      const response = await fetch(
        `${BACKEND_URL}/search?word=${encodeURIComponent(word)}&pdf_id=${pdfId}`
      );
      const data = await response.json();

      if (data.error) {
        setError(data.error);
      } else {
        setResults(data.results);
      }
    } catch (err) {
      setError("Could not connect to backend. Is Flask running?");
    } finally {
      setLoading(false);
    }
  };

  const handleExplain = async (index, row) => {
    setExplainLoading((prev) => ({ ...prev, [index]: true }));

    try {
      const response = await fetch(
        `${BACKEND_URL}/explain?word=${encodeURIComponent(
          word
        )}&context=${encodeURIComponent(
          row.context
        )}&chapter=${encodeURIComponent(row.chapter)}`
      );
      const data = await response.json();

      if (data.error) {
        setExplanations((prev) => ({ ...prev, [index]: { error: data.error } }));
      } else {
        // parse "Topic: ...\nExplanation: ..." into separate fields
        const raw = data.explanation || "";
        const topicMatch = raw.match(/Topic:\s*(.+)/i);
        const explanationMatch = raw.match(/Explanation:\s*(.+)/is);

        setExplanations((prev) => ({
          ...prev,
          [index]: {
            topic: topicMatch ? topicMatch[1].trim() : "",
            explanation: explanationMatch ? explanationMatch[1].trim() : raw,
          },
        }));
      }
    } catch (err) {
      setExplanations((prev) => ({
        ...prev,
        [index]: { error: "Could not fetch explanation." },
      }));
    } finally {
      setExplainLoading((prev) => ({ ...prev, [index]: false }));
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  return (
    <div className="container">
      <h1>PDF Topic Search</h1>
      <p className="subtitle">
        Upload a PDF, search a word, and see where it appears — with a
        topic-aware explanation.
      </p>

      <div className="upload-section">
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileUpload}
          disabled={uploading}
        />
        {uploading && <p className="status-text">Uploading and processing PDF...</p>}
        {uploadError && <p className="error">{uploadError}</p>}
        {pdfInfo && (
          <p className="status-text">
            Loaded "{pdfInfo.filename}" — {pdfInfo.total_pages} pages,{" "}
            {pdfInfo.chapters_found} chapters detected.
          </p>
        )}
      </div>

      {pdfId && (
        <>
          <div className="search-bar">
            <input
              type="text"
              placeholder="Enter a word to search..."
              value={word}
              onChange={(e) => setWord(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <button onClick={handleSearch} disabled={loading}>
              {loading ? "Searching..." : "Search"}
            </button>
          </div>

          {error && <p className="error">{error}</p>}

          {results.length > 0 && (
            <p className="match-count">
              Found {results.length} match{results.length > 1 ? "es" : ""}
            </p>
          )}

          {results.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>Page</th>
                  <th>Chapter</th>
                  <th>Context</th>
                  <th>Explanation</th>
                </tr>
              </thead>
              <tbody>
                {results.map((row, index) => (
                  <tr key={index}>
                    <td>{row.page}</td>
                    <td>{row.chapter}</td>
                    <td className="context-cell">{row.context}</td>
                    <td>
                      {explanations[index] ? (
                        explanations[index].error ? (
                          <span className="error">{explanations[index].error}</span>
                        ) : (
                          <div className="explanation-box">
                            <div className="explanation-topic">
                              {explanations[index].topic}
                            </div>
                            <div className="explanation-text">
                              {explanations[index].explanation}
                            </div>
                          </div>
                        )
                      ) : (
                        <button
                          className="explain-btn"
                          onClick={() => handleExplain(index, row)}
                          disabled={explainLoading[index]}
                        >
                          {explainLoading[index] ? "Loading..." : "Explain"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  );
}

export default App;