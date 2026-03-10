"use client";

import { useState, useRef } from "react";

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

export default function TextPage() {
  const [sourceText, setSourceText] = useState("");
  const [translatedText, setTranslatedText] = useState("");
  const [sourceLang, setSourceLang] = useState("auto");
  const [targetLang, setTargetLang] = useState("vi");
  const [loading, setLoading] = useState(false);
  const [useGemini, setUseGemini] = useState(false);
  const [geminiKey, setGeminiKey] = useState("");
  const [toast, setToast] = useState<{ message: string; type: string } | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const showToast = (message: string, type: string = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleTranslate = async () => {
    if (!sourceText.trim()) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/translate/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: sourceText,
          source_lang: sourceLang,
          target_lang: targetLang,
          use_gemini: useGemini,
          gemini_api_key: geminiKey || null,
        }),
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Translation failed");
      }

      const data = await res.json();
      setTranslatedText(data.translated_text);
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Lỗi dịch thuật", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!translatedText) return;
    await navigator.clipboard.writeText(translatedText);
    showToast("Đã copy bản dịch! ✓");
  };

  const handleClear = () => {
    setSourceText("");
    setTranslatedText("");
    textareaRef.current?.focus();
  };

  const handleSwapLangs = () => {
    if (sourceLang === "auto") return;
    const tempLang = sourceLang;
    setSourceLang(targetLang);
    setTargetLang(tempLang);
    setSourceText(translatedText);
    setTranslatedText(sourceText);
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>
          Dịch <span className="gradient-text">Văn Bản</span>
        </h1>
        <p>Dịch truyện novel, light novel đa ngôn ngữ với AI</p>
      </div>

      {/* Options */}
      <div className="options-bar">
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
              placeholder="Nhập Gemini API Key..."
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
            />
          </div>
        )}
      </div>

      {/* Translation Panel */}
      <div className="translate-panel">
        {/* Source */}
        <div className="panel-box">
          <div className="panel-header">
            <span className="panel-label">Nguồn</span>
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

          <textarea
            ref={textareaRef}
            className="text-area"
            placeholder="Nhập hoặc dán văn bản cần dịch..."
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
          />

          <div className="panel-footer">
            <span className="char-count">{sourceText.length} ký tự</span>
            <div className="panel-actions">
              {sourceText && (
                <button className="btn-icon" onClick={handleClear} title="Xóa">
                  ✕
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Target */}
        <div className="panel-box">
          <div className="panel-header">
            <span className="panel-label">Bản dịch</span>
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

          <textarea
            className="text-area"
            placeholder="Bản dịch sẽ hiển thị ở đây..."
            value={translatedText}
            readOnly
          />

          <div className="panel-footer">
            <span className="char-count">{translatedText.length} ký tự</span>
            <div className="panel-actions">
              {translatedText && (
                <button className="btn-icon" onClick={handleCopy} title="Copy">
                  📋
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="actions-bar">
        <button
          className="btn btn-secondary"
          onClick={handleSwapLangs}
          disabled={sourceLang === "auto"}
          title="Đổi ngôn ngữ"
        >
          ⇄ Đổi
        </button>
        <button
          className="btn btn-primary"
          onClick={handleTranslate}
          disabled={loading || !sourceText.trim()}
        >
          {loading ? (
            <>
              <span className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }}></span>
              Đang dịch...
            </>
          ) : (
            "✦ Dịch ngay"
          )}
        </button>
      </div>

      {/* Toast */}
      {toast && <div className={`toast ${toast.type}`}>{toast.message}</div>}
    </div>
  );
}
