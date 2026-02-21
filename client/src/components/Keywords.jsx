import "./Keywords.css";

function Keywords({ keywords, loading }) {
  if (loading) {
    return (
      <div className="keywords-placeholder">
        <div className="keywords-loading">
          <span className="keywords-loading-dot" />
          <span className="keywords-loading-dot" />
          <span className="keywords-loading-dot" />
        </div>
        <p className="keywords-placeholder-text">Extracting keywords...</p>
      </div>
    );
  }

  if (!keywords) {
    return (
      <div className="keywords-placeholder">
        <div className="keywords-placeholder-icon">
          <svg
            width="36"
            height="36"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="4" y1="9" x2="20" y2="9" />
            <line x1="4" y1="15" x2="20" y2="15" />
            <line x1="10" y1="3" x2="8" y2="21" />
            <line x1="16" y1="3" x2="14" y2="21" />
          </svg>
        </div>
        <p className="keywords-placeholder-text">
          Keywords will appear here after OCR
        </p>
      </div>
    );
  }

  if (keywords.length === 0) {
    return (
      <div className="keywords-placeholder">
        <p className="keywords-placeholder-text">No keywords found</p>
      </div>
    );
  }

  const maxCount = keywords[0].count;

  return (
    <div className="keywords-list">
      {keywords.map(({ word, count }, i) => (
        <div className="keyword-item" key={i}>
          <div className="keyword-info">
            <span className="keyword-rank">{i + 1}</span>
            <span className="keyword-word">{word}</span>
          </div>
          <div className="keyword-bar-wrapper">
            <div
              className="keyword-bar"
              style={{ width: `${(count / maxCount) * 100}%` }}
            />
          </div>
          <span className="keyword-count">{count}</span>
        </div>
      ))}
    </div>
  );
}

export default Keywords;
