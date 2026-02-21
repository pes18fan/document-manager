import { useRef, useState } from "react";
import "./FileUpload.css";

function FileUpload({ file, preview, onFileSelect, onClear }) {
  const inputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);

  function handleDrag(e) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  }

  function handleChange(e) {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  }

  function handleBrowseClick() {
    inputRef.current?.click();
  }

  if (file && preview) {
    return (
      <div className="file-preview">
        <div className="preview-image-wrapper">
          <img src={preview} alt="Document preview" className="preview-image" />
        </div>
        <div className="file-info">
          <span className="file-name" title={file.name}>
            {file.name}
          </span>
          <span className="file-size">
            {(file.size / 1024).toFixed(1)} KB
          </span>
        </div>
        <button className="clear-button" onClick={onClear} type="button">
          Remove
        </button>
      </div>
    );
  }

  return (
    <div
      className={`dropzone ${dragActive ? "dropzone--active" : ""}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={handleBrowseClick}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        onChange={handleChange}
        className="file-input"
      />
      <div className="dropzone-content">
        <div className="dropzone-icon">
          <svg
            width="40"
            height="40"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>
        <p className="dropzone-text">
          Drag and drop an image here, or{" "}
          <span className="browse-link">browse</span>
        </p>
        <p className="dropzone-hint">
          Supports JPG, PNG, TIF and other image formats
        </p>
      </div>
    </div>
  );
}

export default FileUpload;
