import Link from "next/link";

export default function HomePage() {
  return (
    <section className="hero">
      <div className="hero-badge">
        <span className="dot"></span>
        Powered by AI & OCR
      </div>

      <h1>
        Dịch Truyện<br />
        <span className="gradient-text">Thông Minh</span>
      </h1>

      <p>
        Dịch truyện novel đa ngôn ngữ và dịch ảnh tự động - nhận diện chữ trên ảnh, 
        xóa chữ cũ và thay bằng bản dịch. Miễn phí, nhanh chóng.
      </p>

      <div className="features-grid">
        <Link href="/text" className="feature-card">
          <div className="feature-icon text-icon">📝</div>
          <h3>Dịch Văn Bản</h3>
          <p>
            Dịch truyện novel, light novel với chất lượng cao. 
            Hỗ trợ Google Translate miễn phí và Gemini AI cho bản dịch tốt hơn.
          </p>
          <div className="feature-tags">
            <span className="feature-tag">Google Translate</span>
            <span className="feature-tag">Gemini AI</span>
            <span className="feature-tag">12+ Ngôn ngữ</span>
            <span className="feature-tag">Miễn phí</span>
          </div>
        </Link>

        <Link href="/image" className="feature-card">
          <div className="feature-icon image-icon">🖼️</div>
          <h3>Dịch Ảnh</h3>
          <p>
            Tự động nhận diện chữ trên ảnh (manga, manhwa, manhua), 
            xóa chữ cũ và chèn bản dịch. OCR + AI Inpainting.
          </p>
          <div className="feature-tags">
            <span className="feature-tag">EasyOCR</span>
            <span className="feature-tag">AI Inpainting</span>
            <span className="feature-tag">Manga/Manhwa</span>
            <span className="feature-tag">Download ảnh</span>
          </div>
        </Link>
      </div>
    </section>
  );
}
