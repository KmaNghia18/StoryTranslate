"""
API router for translation endpoints.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import traceback

from app.services.text_service import translate_text, get_supported_languages
from app.services.image_service import translate_image

router = APIRouter(prefix="/api/translate", tags=["translate"])


class TextTranslateRequest(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str = "vi"
    use_gemini: bool = False
    gemini_api_key: str | None = None


class TextTranslateResponse(BaseModel):
    translated_text: str
    source_lang: str
    target_lang: str


class DetectionInfo(BaseModel):
    text: str
    translated_text: str
    confidence: float


class ImageTranslateResponse(BaseModel):
    detections: list[DetectionInfo]
    message: str


@router.post("/text", response_model=TextTranslateResponse)
async def translate_text_endpoint(request: TextTranslateRequest):
    """Translate text from source language to target language."""
    try:
        result = translate_text(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            use_gemini=request.use_gemini,
            gemini_api_key=request.gemini_api_key,
        )
        return TextTranslateResponse(
            translated_text=result,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image")
async def translate_image_endpoint(
    file: UploadFile = File(...),
    source_lang: str = Form(default="auto"),
    target_lang: str = Form(default="vi"),
    use_manga_ocr: bool = Form(default=False),
    use_gemini: bool = Form(default=False),
    gemini_api_key: str = Form(default=""),
):
    """Translate text in an image. Returns the translated image."""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        image_bytes = await file.read()

        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # Process image
        result_bytes, detections = translate_image(
            image_bytes=image_bytes,
            source_lang=source_lang,
            target_lang=target_lang,
            use_manga_ocr=use_manga_ocr,
            use_gemini=use_gemini,
            gemini_api_key=gemini_api_key if gemini_api_key else None,
        )

        # Return translated image
        return Response(
            content=result_bytes,
            media_type="image/png",
            headers={
                "X-Detections-Count": str(len(detections)),
                "X-Detections": str(
                    [
                        {
                            "original": d["text"],
                            "translated": d.get("translated_text", ""),
                            "confidence": d["confidence"],
                        }
                        for d in detections
                    ]
                ),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_languages():
    """Get list of supported languages."""
    return get_supported_languages()
