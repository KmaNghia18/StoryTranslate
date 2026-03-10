"""
OCR service using EasyOCR with singleton pattern.
Manga OCR optional for manga/manhwa (requires separate install).
"""

import easyocr
import numpy as np
from PIL import Image
import io
import threading

# Singleton OCR readers
_readers: dict[str, easyocr.Reader] = {}
_lock = threading.Lock()


def get_reader(languages: list[str]) -> easyocr.Reader:
    """Get or create an EasyOCR reader (singleton per language combo)."""
    key = ",".join(sorted(languages))
    if key not in _readers:
        with _lock:
            if key not in _readers:
                _readers[key] = easyocr.Reader(languages, gpu=False)
    return _readers[key]


def detect_text(
    image_bytes: bytes,
    source_lang: str = "en",
) -> list[dict]:
    """
    Detect text in an image and return bounding boxes with text.
    
    Returns list of:
    {
        "bbox": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
        "text": "detected text",
        "confidence": 0.95
    }
    """
    # Map language codes to EasyOCR language codes
    lang_map = {
        "auto": ["en"],
        "en": ["en"],
        "vi": ["vi"],
        "zh-CN": ["ch_sim"],
        "zh-TW": ["ch_tra"],
        "ja": ["ja"],
        "ko": ["ko"],
        "th": ["th"],
        "fr": ["fr"],
        "de": ["de"],
        "es": ["es"],
        "ru": ["ru"],
        "pt": ["pt"],
        "id": ["id"],
    }

    ocr_langs = lang_map.get(source_lang, ["en"])

    # Convert bytes to numpy array
    image = Image.open(io.BytesIO(image_bytes))
    image_np = np.array(image)

    reader = get_reader(ocr_langs)
    results = reader.readtext(image_np)

    detections = []
    for bbox, text, confidence in results:
        if confidence > 0.3:  # Filter low confidence
            detections.append({
                "bbox": bbox,
                "text": text,
                "confidence": float(confidence),
            })

    return detections


def detect_text_manga(image_bytes: bytes) -> list[dict]:
    """
    Detect text using Manga OCR (specialized for manga/manhwa).
    Falls back to EasyOCR if manga-ocr is not installed.
    """
    try:
        from manga_ocr import MangaOcr

        # Use EasyOCR for detection (bounding boxes)
        # Then Manga OCR for better text recognition
        image = Image.open(io.BytesIO(image_bytes))
        image_np = np.array(image)

        reader = get_reader(["ja", "en"])
        results = reader.readtext(image_np)

        mocr = MangaOcr()
        detections = []

        for bbox, _, confidence in results:
            if confidence > 0.2:
                # Crop region and use Manga OCR for text
                pts = np.array(bbox, dtype=np.int32)
                x_min, y_min = pts.min(axis=0)
                x_max, y_max = pts.max(axis=0)

                # Add padding
                pad = 5
                x_min = max(0, x_min - pad)
                y_min = max(0, y_min - pad)
                x_max = min(image_np.shape[1], x_max + pad)
                y_max = min(image_np.shape[0], y_max + pad)

                crop = image.crop((x_min, y_min, x_max, y_max))
                text = mocr(crop)

                detections.append({
                    "bbox": bbox,
                    "text": text,
                    "confidence": float(confidence),
                })

        return detections

    except ImportError:
        # Fallback to EasyOCR
        print("manga-ocr not installed, falling back to EasyOCR")
        return detect_text(image_bytes, "ja")
