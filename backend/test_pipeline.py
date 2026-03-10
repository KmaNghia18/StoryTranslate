"""Test the image translation pipeline step by step."""
from PIL import Image, ImageDraw, ImageFont
import io
from app.services.ocr_service import detect_text
from app.services.image_service import translate_image

# Create a test image with big text
img = Image.new('RGB', (400, 200), color='white')
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 32)
except Exception:
    font = ImageFont.load_default()
draw.text((50, 70), 'Hello World!', fill='black', font=font)
buf = io.BytesIO()
img.save(buf, format='PNG')
image_bytes = buf.getvalue()

# Test OCR
print('=== OCR Test ===')
dets = detect_text(image_bytes, 'en')
print(f'Found {len(dets)} detections')
for d in dets:
    print(f'  Text: {d["text"]!r}  Conf: {d["confidence"]:.2f}')
    print(f'  BBox: {d["bbox"]}')

# Test full pipeline
print()
print('=== Full Pipeline (en -> vi) ===')
result, details = translate_image(image_bytes, 'en', 'vi')
print(f'Result size: {len(result)} bytes')
print(f'Detections: {len(details)}')
for d in details:
    orig = d["text"]
    trans = d.get("translated_text", "?")
    print(f'  "{orig}" -> "{trans}"')

# Save result
with open('C:/tmp/test_result.png', 'wb') as f:
    f.write(result)
print('\nResult saved to C:/tmp/test_result.png')
