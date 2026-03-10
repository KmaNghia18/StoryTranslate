"""Quick test for image translation pipeline."""
import sys
import traceback

# Test 1: Imports
print("=== TEST 1: Imports ===")
try:
    from app.services.text_service import translate_text
    from app.services.ocr_service import detect_text
    from app.services.image_service import translate_image
    print("OK: All imports successful")
except Exception as e:
    print(f"FAIL: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 2: Create test image
print("\n=== TEST 2: Create test image ===")
from PIL import Image, ImageDraw
import io

img = Image.new('RGB', (300, 100), color='white')
draw = ImageDraw.Draw(img)
draw.text((20, 30), 'Hello World Test', fill='black')
buf = io.BytesIO()
img.save(buf, format='PNG')
image_bytes = buf.getvalue()
print(f"OK: Test image {len(image_bytes)} bytes")

# Test 3: OCR
print("\n=== TEST 3: OCR ===")
try:
    detections = detect_text(image_bytes, "en")
    print(f"OK: Found {len(detections)} text regions")
    for d in detections:
        print(f"  - '{d['text']}' (conf: {d['confidence']:.2f})")
except Exception as e:
    print(f"FAIL: {e}")
    traceback.print_exc()

# Test 4: Text translation
print("\n=== TEST 4: Text translation ===")
try:
    result = translate_text("Hello World", source_lang="en", target_lang="vi")
    print(f"OK: 'Hello World' -> '{result}'")
except Exception as e:
    print(f"FAIL: {e}")
    traceback.print_exc()

# Test 5: Full pipeline
print("\n=== TEST 5: Full pipeline ===")
try:
    result_bytes, dets = translate_image(
        image_bytes=image_bytes,
        source_lang="en",
        target_lang="vi",
    )
    print(f"OK: Result {len(result_bytes)} bytes, {len(dets)} detections")
except Exception as e:
    print(f"FAIL: {e}")
    traceback.print_exc()

print("\n=== DONE ===")
