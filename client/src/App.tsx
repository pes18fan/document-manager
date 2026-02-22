import { useState, useRef, type ChangeEvent } from "react";

const API_URL = "http://127.0.0.1:8000";

interface OcrResult {
  text: string;
  avg_conf: number;
  words: { text: string; conf: number; bbox: number[] }[];
}

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<OcrResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0] ?? null;
    setFile(selected);
    setResult(null);
    setError(null);

    if (selected) {
      const url = URL.createObjectURL(selected);
      setPreview(url);
    } else {
      setPreview(null);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped) {
      setFile(dropped);
      setResult(null);
      setError(null);
      setPreview(URL.createObjectURL(dropped));
    }
  }

  async function handleSubmit() {
    if (!file) {
      setError("Please select an image file first.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const form = new FormData();
      form.append("file", file);

      const res = await fetch(`${API_URL}/ocr`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }

      const data: OcrResult = await res.json();
      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleClear() {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function confidenceColor(conf: number): string {
    if (conf >= 80) return "text-green-600";
    if (conf >= 50) return "text-yellow-600";
    return "text-red-600";
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-3xl px-6 py-4">
          <h1 className="text-xl font-semibold tracking-tight">
            Nepali Document OCR
          </h1>
          <p className="text-sm text-gray-500">
            Upload a document image to extract Nepali text
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-8 space-y-6">
        {/* Upload area */}
        <div
          className="rounded-lg border-2 border-dashed border-gray-300 bg-white p-8 text-center transition hover:border-gray-400 cursor-pointer"
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
          />

          {preview ? (
            <img
              src={preview}
              alt="Preview"
              className="mx-auto max-h-64 rounded object-contain"
            />
          ) : (
            <div className="space-y-2 text-gray-400">
              <svg
                className="mx-auto h-10 w-10"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M12 16v-8m0 0l-3 3m3-3l3 3M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1"
                />
              </svg>
              <p className="text-sm">
                Click or drag and drop an image here
              </p>
            </div>
          )}
        </div>

        {file && (
          <p className="text-sm text-gray-500 text-center">
            Selected: <span className="font-medium">{file.name}</span>
          </p>
        )}

        {/* Actions */}
        <div className="flex gap-3 justify-center">
          <button
            onClick={handleSubmit}
            disabled={!file || loading}
            className="rounded-md bg-gray-900 px-5 py-2 text-sm font-medium text-white transition hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? "Processing..." : "Run OCR"}
          </button>
          <button
            onClick={handleClear}
            className="rounded-md border border-gray-300 bg-white px-5 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50"
          >
            Clear
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="text-center text-sm text-gray-500">
            <div className="mx-auto mb-2 h-6 w-6 animate-spin rounded-full border-2 border-gray-300 border-t-gray-900" />
            Running OCR on your document...
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-4">
            {/* Confidence */}
            <div className="rounded-md border border-gray-200 bg-white px-4 py-3">
              <span className="text-sm text-gray-500">
                Average Confidence:{" "}
              </span>
              <span
                className={`font-semibold ${confidenceColor(result.avg_conf)}`}
              >
                {result.avg_conf.toFixed(1)}%
              </span>
            </div>

            {/* Extracted text */}
            <div className="rounded-md border border-gray-200 bg-white">
              <div className="flex items-center justify-between border-b border-gray-200 px-4 py-2">
                <span className="text-sm font-medium text-gray-700">
                  Extracted Text
                </span>
                <button
                  onClick={() =>
                    navigator.clipboard.writeText(result.text)
                  }
                  className="text-xs text-gray-500 hover:text-gray-900 transition"
                >
                  Copy
                </button>
              </div>
              <pre className="whitespace-pre-wrap px-4 py-3 text-sm leading-relaxed">
                {result.text || (
                  <span className="text-gray-400 italic">
                    No text detected.
                  </span>
                )}
              </pre>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
