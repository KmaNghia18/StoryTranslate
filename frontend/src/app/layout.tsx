import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "StoryTranslate - Dịch Truyện & Dịch Ảnh",
  description:
    "Web app dịch truyện novel và dịch ảnh tự động. Hỗ trợ OCR, nhận diện chữ trên ảnh, và dịch đa ngôn ngữ.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body>
        <nav className="navbar">
          <Link href="/" className="navbar-brand">
            <svg
              viewBox="0 0 28 28"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <rect
                x="2"
                y="2"
                width="24"
                height="24"
                rx="6"
                stroke="url(#grad)"
                strokeWidth="2.5"
              />
              <path
                d="M8 10h12M8 14h8M8 18h10"
                stroke="url(#grad)"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <defs>
                <linearGradient id="grad" x1="2" y1="2" x2="26" y2="26">
                  <stop stopColor="#7c5bf5" />
                  <stop offset="1" stopColor="#00d4aa" />
                </linearGradient>
              </defs>
            </svg>
            StoryTranslate
          </Link>
          <ul className="navbar-links">
            <li>
              <Link href="/text">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                >
                  <path d="M2 3h12v1.5H2V3zm0 3.5h8v1.5H2V6.5zm0 3.5h10v1.5H2V10zm0 3.5h6v1.5H2V13.5z" />
                </svg>
                <span>Dịch Văn Bản</span>
              </Link>
            </li>
            <li>
              <Link href="/image">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                >
                  <path d="M2 3a1 1 0 011-1h10a1 1 0 011 1v10a1 1 0 01-1 1H3a1 1 0 01-1-1V3zm2 8l2.5-3 2 2.5L11 7l2 4H4z" />
                </svg>
                <span>Dịch Ảnh</span>
              </Link>
            </li>
          </ul>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}
