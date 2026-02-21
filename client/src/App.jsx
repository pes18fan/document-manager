import { useState, useEffect } from "react";
import Header from "./components/Header";
import FileUpload from "./components/FileUpload";
import ResultDisplay from "./components/ResultDisplay";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/ocr";

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("theme") || "dark";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  function toggleTheme() {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  }

  function handleFileSelect(selectedFile) {
    setFile(selectedFile);
    setResult(null);
    setError(null);

    if (selectedFile) {
      const url = URL.createObjectURL(selectedFile);
      setPreview(url);
    } else {
      setPreview(null);
    }
  }

  function handleClear() {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
  }

  async function handleOcr() {
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const form = new FormData();
      form.append("file", file);

      const res = await fetch(API_URL, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        throw new Error(`Server responded with ${res.status}`);
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message || "Failed to process the image");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <Header theme={theme} onToggleTheme={toggleTheme} />
      <main className="main">
        <div className="container">
          <div className="layout">
            <section className="panel upload-panel">
              <h2 className="panel-title">Upload Document</h2>
              <FileUpload
                file={file}
                preview={preview}
                onFileSelect={handleFileSelect}
                onClear={handleClear}
              />
              <button
                className="ocr-button"
                onClick={handleOcr}
                disabled={!file || loading}
              >
                {loading ? (
                  <>
                    <span className="spinner" />
                    Processing...
                  </>
                ) : (
                  "Run OCR"
                )}
              </button>
              {error && <p className="error-message">{error}</p>}
            </section>

            <section className="panel result-panel">
              <h2 className="panel-title">Result</h2>
              <ResultDisplay result={result} loading={loading} />
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
