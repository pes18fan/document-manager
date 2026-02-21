import "./ResultDisplay.css";

function ResultDisplay({ result, loading }) {
  if (loading) {
    return (
      <div className="result-placeholder">
        <div className="loading-indicator">
          <span className="loading-dot" />
          <span className="loading-dot" />
          <span className="loading-dot" />
        </div>
        <p className="placeholder-text">Processing your document...</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="result-placeholder">
        <div className="placeholder-icon">
          <svg
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            <line x1="3" y1="9" x2="21" y2="9" />
            <line x1="9" y1="21" x2="9" y2="9" />
          </svg>
        </div>
        <p className="placeholder-text">
          Upload a document and run OCR to see results here
        </p>
      </div>
    );
  }

  const confidencePercent = typeof result.avg_conf === "number"
    ? result.avg_conf.toFixed(1)
    : "N/A";

  const confidenceClass =
    result.avg_conf >= 80
      ? "confidence--high"
      : result.avg_conf >= 50
        ? "confidence--medium"
        : "confidence--low";

  function handleCopy() {
    if (result.text) {
      navigator.clipboard.writeText(result.text);
    }
  }

  return (
    <div className="result">
      <div className="result-header">
        <div className={`confidence-badge ${confidenceClass}`}>
          Confidence: {confidencePercent}%
        </div>
        <button className="copy-button" onClick={handleCopy} type="button">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
          </svg>
          Copy text
        </button>
      </div>
      <pre className="result-text">{result.text || "(no text detected)"}</pre>
    </div>
  );
}

export default ResultDisplay;
