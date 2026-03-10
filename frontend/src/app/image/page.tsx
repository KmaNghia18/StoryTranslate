"use client";

import { useState, useRef, useCallback } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const LANGUAGES = [
  { code: "auto", name: "Tự động phát hiện" },
  { code: "vi", name: "🇻🇳 Tiếng Việt" },
  { code: "en", name: "🇺🇸 English" },
  { code: "zh-CN", name: "🇨🇳 中文 (简体)" },
  { code: "zh-TW", name: "🇹🇼 中文 (繁體)" },
  { code: "ja", name: "🇯🇵 日本語" },
  { code: "ko", name: "🇰🇷 한국어" },
  { code: "th", name: "🇹🇭 ไทย" },
  { code: "fr", name: "🇫🇷 Français" },
  { code: "de", name: "🇩🇪 Deutsch" },
  { code: "es", name: "🇪🇸 Español" },
  { code: "ru", name: "🇷🇺 Русский" },
  { code: "id", name: "🇮🇩 Indonesia" },
];

const TARGET_LANGUAGES = LANGUAGES.filter((l) => l.code !== "auto");

interface Detection {
  original: string;
  translated: string;
  confidence: number;
}

export default function ImagePage() {
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [sourcePreview, setSourcePreview] = useState<string>("");
  const [resultPreview, setResultPreview] = useState<string>("");
  const [sourceLang, setSourceLang] = useState("auto");
  const [targetLang, setTargetLang] = useState("vi");
  const [loading, setLoading] = useState(false);
  const [useMangaOcr, setUseMangaOcr] = useState(false);
  const [useGemini, setUseGemini] = useState(false);
  const [geminiKey, setGeminiKey] = useState("");
  const [detections, setDetections] = useState<Detection[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: string } | null>(null);
  const [progress, setProgress] = useState(0);
  const [progressStep, setProgressStep] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const showToast = (message: string, type: string = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleFile = useCallback((file: File) => {
    if (!file.type.startsWith("image/")) {
      showToast("Vui lòng chọn file ảnh!", "error");
      return;
    }

    setSourceFile(file);
    setResultPreview("");
    setDetections([]);
    setProgress(0);
    setProgressStep("");

    const reader = new FileReader();
    reader.onload = (e) => {
      setSourcePreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragOver(false);
  }, []);

  const handleTranslate = async () => {
    if (!sourceFile) return;

    setLoading(true);
    setDetections([]);
    setProgress(0);
    setProgressStep("Đang tải ảnh lên...");

    try {
      // Step 1: Upload and start async processing
      const formData = new FormData();
      formData.append("file", sourceFile);
      formData.append("source_lang", sourceLang);
      formData.append("target_lang", targetLang);
      formData.append("use_manga_ocr", String(useMangaOcr));
      formData.append("use_gemini", String(useGemini));
      formData.append("gemini_api_key", geminiKey);

      const startRes = await fetch(`${API_BASE}/api/translate/image/async`, {
        method: "POST",
        body: formData,
      });

      if (!startRes.ok) {
        const error = await startRes.json();
        throw new Error(error.detail || "Failed to start translation");
      }

      const { task_id } = await startRes.json();

      // Step 2: Listen for progress via SSE
      await new Promise<void>((resolve, reject) => {
        const eventSource = new EventSource(
          `${API_BASE}/api/translate/image/progress/${task_id}`
        );

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setProgress(data.progress);
            setProgressStep(data.step);

            if (data.status === "failed") {
              eventSource.close();
              reject(new Error(data.error || "Translation failed"));
            }

            if (data.status === "completed") {
              if (data.detections) {
                setDetections(data.detections);
              }
              eventSource.close();
              resolve();
            }
          } catch {
            // Ignore parse errors
          }
        };

        eventSource.onerror = () => {
          eventSource.close();
          // Don't reject on error - might just be connection closed after completion
          resolve();
        };
      });

      // Step 3: Fetch the result image
      const resultRes = await fetch(
        `${API_BASE}/api/translate/image/result/${task_id}`
      );

      if (!resultRes.ok) {
        throw new Error("Failed to fetch result image");
      }

      const blob = await resultRes.blob();
      const url = URL.createObjectURL(blob);
      setResultPreview(url);
      showToast("Dịch ảnh thành công! ✓");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Lỗi dịch ảnh", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!resultPreview) return;
    const a = document.createElement("a");
    a.href = resultPreview;
    a.download = `translated_${sourceFile?.name || "image"}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleReset = () => {
    setSourceFile(null);
    setSourcePreview("");
    setResultPreview("");
    setDetections([]);
    setProgress(0);
    setProgressStep("");
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>
          Dịch <span className="gradient-text">Ảnh</span>
        </h1>
        <p>Tự động nhận diện chữ trên ảnh, xóa và thay bằng bản dịch</p>
      </div>

      {/* Options */}
      <div className="options-bar">
        <div className="option-group">
          <span className="option-label">Ngôn ngữ nguồn</span>
          <select
            className="lang-select"
            value={sourceLang}
            onChange={(e) => setSourceLang(e.target.value)}
          >
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.name}
              </option>
            ))}
          </select>
        </div>

        <div className="option-group">
          <span className="option-label">Dịch sang</span>
          <select
            className="lang-select"
            value={targetLang}
            onChange={(e) => setTargetLang(e.target.value)}
          >
            {TARGET_LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.name}
              </option>
            ))}
          </select>
        </div>

        <div className="option-group">
          <span className="option-label">Manga OCR</span>
          <label className="toggle">
            <input
              type="checkbox"
              checked={useMangaOcr}
              onChange={(e) => setUseMangaOcr(e.target.checked)}
            />
            <span className="toggle-slider"></span>
          </label>
        </div>

        <div className="option-group">
          <span className="option-label">Gemini AI</span>
          <label className="toggle">
            <input
              type="checkbox"
              checked={useGemini}
              onChange={(e) => setUseGemini(e.target.checked)}
            />
            <span className="toggle-slider"></span>
          </label>
        </div>

        {useGemini && (
          <div className="option-group">
            <input
              type="password"
              className="gemini-input"
              placeholder="Gemini API Key..."
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
            />
          </div>
        )}
      </div>

      {/* Upload Zone */}
      {!sourcePreview && (
        <div
          className={`upload-zone ${dragOver ? "drag-over" : ""}`}
          onClick={() => fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <div className="upload-icon">🖼️</div>
          <div className="upload-text">Kéo & thả ảnh vào đây</div>
          <div className="upload-hint">
            hoặc click để chọn file • PNG, JPG, WEBP
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            style={{ display: "none" }}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
            }}
          />
        </div>
      )}

      {/* Image Preview */}
      {sourcePreview && (
        <>
          <div className="image-preview-grid">
            <div className="image-preview-box">
              <div className="preview-header">
                <span className="preview-label">Ảnh gốc</span>
                <button className="btn-icon" onClick={handleReset} title="Đổi ảnh">
                  ✕
                </button>
              </div>
              <div className="preview-body">
                <img src={sourcePreview} alt="Original" />
              </div>
            </div>

            <div className="image-preview-box">
              <div className="preview-header">
                <span className="preview-label">Ảnh đã dịch</span>
                {resultPreview && (
                  <button className="btn-icon" onClick={handleDownload} title="Tải về">
                    ⬇
                  </button>
                )}
              </div>
              <div className="preview-body">
                {loading ? (
                  <div className="spinner-overlay">
                    <div className="progress-container">
                      <div className="progress-bar-wrapper">
                        <div
                          className="progress-bar-fill"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                      <div className="progress-info">
                        <span className="progress-percent">{progress}%</span>
                        <span className="progress-step">{progressStep}</span>
                      </div>
                    </div>
                  </div>
                ) : resultPreview ? (
                  <img src={resultPreview} alt="Translated" />
                ) : (
                  <span style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
                    Nhấn &quot;Dịch ảnh&quot; để bắt đầu
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="actions-bar">
            <button
              className="btn btn-primary"
              onClick={handleTranslate}
              disabled={loading || !sourceFile}
            >
              {loading ? (
                <>
                  <span
                    className="spinner"
                    style={{ width: 18, height: 18, borderWidth: 2 }}
                  ></span>
                  Đang xử lý... {progress}%
                </>
              ) : (
                "✦ Dịch ảnh"
              )}
            </button>
            {resultPreview && (
              <button className="btn btn-secondary" onClick={handleDownload}>
                ⬇ Tải về
              </button>
            )}
          </div>

          {/* Detections List */}
          {detections.length > 0 && (
            <div className="detections-list">
              <h3>📋 Chi tiết nhận diện ({detections.length} đoạn)</h3>
              {detections.map((d, i) => (
                <div key={i} className="detection-item">
                  <span className="original">{d.original}</span>
                  <span className="arrow">→</span>
                  <span className="translated">{d.translated}</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Toast */}
      {toast && <div className={`toast ${toast.type}`}>{toast.message}</div>}
    </div>
  );
}
