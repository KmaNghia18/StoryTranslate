"""
Image translation pipeline:
1. OCR - detect text regions
2. Translate text
3. Inpaint - remove original text using OpenCV
4. Render - draw translated text using Pillow
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import os

from app.services.ocr_service import detect_text, detect_text_manga
from app.services.text_service import translate_text


def translate_image(
    image_bytes: bytes,
    source_lang: str = "auto",
    target_lang: str = "vi",
    use_manga_ocr: bool = False,
    use_gemini: bool = False,
    gemini_api_key: str | None = None,
    on_progress: callable = None,
) -> tuple[bytes, list[dict]]:
    """
    Full pipeline: OCR → Translate → Inpaint → Render.
    
    Args:
        on_progress: callback(progress_int, step_str) for progress updates
    
    Returns:
        tuple of (translated_image_bytes, detection_details)
    """
    def report(progress: int, step: str):
        if on_progress:
            on_progress(progress, step)

    # Step 1: OCR
    report(5, "Đang nhận diện chữ trên ảnh (OCR)...")
    if use_manga_ocr:
        detections = detect_text_manga(image_bytes)
    else:
        detections = detect_text(image_bytes, source_lang)

    report(30, f"Nhận diện được {len(detections)} đoạn text")

    if not detections:
        report(100, "Không tìm thấy text trên ảnh")
        return image_bytes, []

    # Step 2: Translate each detected text
    total = len(detections)
    for i, det in enumerate(detections):
        pct = 30 + int((i / total) * 40)  # 30% -> 70%
        report(pct, f"Đang dịch đoạn {i+1}/{total}...")
        translated = translate_text(
            det["text"],
            source_lang=source_lang,
            target_lang=target_lang,
            use_gemini=use_gemini,
            gemini_api_key=gemini_api_key,
        )
        det["translated_text"] = translated

    # Step 3 & 4: Inpaint + Render
    report(75, "Đang xóa chữ cũ (Inpainting)...")
    result_bytes = _inpaint_and_render(image_bytes, detections)
    report(95, "Đang render chữ mới lên ảnh...")

    report(100, "Hoàn thành!")
    return result_bytes, detections


def _inpaint_and_render(image_bytes: bytes, detections: list[dict]) -> bytes:
    """Remove original text and render translated text."""

    # Load image with OpenCV for inpainting
    nparr = np.frombuffer(image_bytes, np.uint8)
    cv_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if cv_image is None:
        raise ValueError("Could not decode image")

    h, w = cv_image.shape[:2]

    # Create mask for inpainting (mark text regions)
    mask = np.zeros((h, w), dtype=np.uint8)

    for det in detections:
        pts = np.array(det["bbox"], dtype=np.int32)
        # Expand the bounding box slightly for better inpainting
        center = pts.mean(axis=0)
        expanded_pts = ((pts - center) * 1.1 + center).astype(np.int32)
        cv2.fillPoly(mask, [expanded_pts], 255)

    # Inpaint - remove text
    inpainted = cv2.inpaint(cv_image, mask, inpaintRadius=7, flags=cv2.INPAINT_TELEA)

    # Convert to PIL for text rendering
    pil_image = Image.fromarray(cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_image)

    # Render translated text
    for det in detections:
        translated = det.get("translated_text", "")
        if not translated:
            continue

        bbox = det["bbox"]
        pts = np.array(bbox, dtype=np.int32)
        x_min, y_min = pts.min(axis=0)
        x_max, y_max = pts.max(axis=0)

        box_w = int(x_max - x_min)
        box_h = int(y_max - y_min)

        if box_w <= 0 or box_h <= 0:
            continue

        # Calculate font size to fit the bounding box
        font = _get_fitted_font(translated, box_w, box_h)

        # Get text color from surrounding area (sample from original image)
        text_color = _sample_text_color(cv_image, pts)

        # Draw text centered in bounding box
        text_bbox = draw.textbbox((0, 0), translated, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]

        text_x = int(x_min + (box_w - text_w) / 2)
        text_y = int(y_min + (box_h - text_h) / 2)

        # Draw text with outline for better readability
        outline_color = (255, 255, 255) if sum(text_color) < 384 else (0, 0, 0)
        _draw_text_with_outline(
            draw, (text_x, text_y), translated, font, text_color, outline_color
        )

    # Convert back to bytes
    output = io.BytesIO()
    pil_image.save(output, format="PNG", quality=95)
    output.seek(0)
    return output.read()


def _get_fitted_font(text: str, box_w: int, box_h: int) -> ImageFont.FreeTypeFont:
    """Get a font that fits the text within the bounding box."""
    # Try to find a good font
    font_paths = [
        # Windows fonts
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/msyh.ttc",  # Microsoft YaHei (CJK support)
        "C:/Windows/Fonts/malgun.ttf",  # Malgun Gothic (Korean)
        "C:/Windows/Fonts/meiryo.ttc",  # Meiryo (Japanese)
        # Linux fonts
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]

    font_path = None
    for fp in font_paths:
        if os.path.exists(fp):
            font_path = fp
            break

    # Binary search for best font size
    min_size = 8
    max_size = max(box_h, 60)
    best_size = min_size

    for size in range(max_size, min_size - 1, -1):
        try:
            if font_path:
                font = ImageFont.truetype(font_path, size)
            else:
                font = ImageFont.load_default(size)
        except Exception:
            font = ImageFont.load_default()

        dummy = Image.new("RGB", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy)
        text_bbox = dummy_draw.textbbox((0, 0), text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]

        if text_w <= box_w and text_h <= box_h:
            best_size = size
            break

    try:
        if font_path:
            return ImageFont.truetype(font_path, best_size)
        else:
            return ImageFont.load_default(best_size)
    except Exception:
        return ImageFont.load_default()


def _sample_text_color(cv_image: np.ndarray, pts: np.ndarray) -> tuple:
    """Sample the dominant text color from the original image region."""
    try:
        x_min, y_min = pts.min(axis=0).astype(int)
        x_max, y_max = pts.max(axis=0).astype(int)

        # Clamp to image bounds
        h, w = cv_image.shape[:2]
        x_min = max(0, x_min)
        y_min = max(0, y_min)
        x_max = min(w, x_max)
        y_max = min(h, y_max)

        region = cv_image[y_min:y_max, x_min:x_max]
        if region.size == 0:
            return (0, 0, 0)

        # Get the darkest color as likely text color
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        min_idx = np.unravel_index(gray.argmin(), gray.shape)
        bgr = region[min_idx[0], min_idx[1]]
        return (int(bgr[2]), int(bgr[1]), int(bgr[0]))  # BGR to RGB

    except Exception:
        return (0, 0, 0)


def _draw_text_with_outline(
    draw: ImageDraw.Draw,
    position: tuple,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill_color: tuple,
    outline_color: tuple,
    outline_width: int = 1,
):
    """Draw text with an outline for better readability."""
    x, y = position
    # Draw outline
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    # Draw text
    draw.text(position, text, font=font, fill=fill_color)
