"""
API router for translation endpoints.
Includes SSE (Server-Sent Events) for image translation progress.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
import traceback
import threading
import asyncio
import json

from app.services.text_service import translate_text, get_supported_languages
from app.services.image_service import translate_image
from app.services.task_store import (
    create_task, get_task, update_task, complete_task, fail_task,
    TaskStatus,
)

router = APIRouter(prefix="/api/translate", tags=["translate"])


def _parse_bool(value: str) -> bool:
    """Parse a string to boolean (form fields send strings)."""
    return value.lower() in ("true", "1", "yes", "on")


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
    use_manga_ocr: str = Form(default="false"),
    use_gemini: str = Form(default="false"),
    gemini_api_key: str = Form(default=""),
):
    """Translate text in an image. Returns the translated image."""
    try:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        result_bytes, detections = translate_image(
            image_bytes=image_bytes,
            source_lang=source_lang,
            target_lang=target_lang,
            use_manga_ocr=_parse_bool(use_manga_ocr),
            use_gemini=_parse_bool(use_gemini),
            gemini_api_key=gemini_api_key if gemini_api_key else None,
        )

        return Response(
            content=result_bytes,
            media_type="image/png",
            headers={
                "X-Detections-Count": str(len(detections)),
                "X-Detections": json.dumps(
                    [
                        {
                            "original": d["text"],
                            "translated": d.get("translated_text", ""),
                            "confidence": d["confidence"],
                        }
                        for d in detections
                    ],
                    ensure_ascii=False,
                ),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image/async")
async def translate_image_async_endpoint(
    file: UploadFile = File(...),
    source_lang: str = Form(default="auto"),
    target_lang: str = Form(default="vi"),
    use_manga_ocr: str = Form(default="false"),
    use_gemini: str = Form(default="false"),
    gemini_api_key: str = Form(default=""),
):
    """Start async image translation. Returns task_id for progress tracking."""
    try:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        task_id = create_task()
        _use_manga = _parse_bool(use_manga_ocr)
        _use_gem = _parse_bool(use_gemini)
        _gem_key = gemini_api_key if gemini_api_key else None

        def process():
            try:
                def on_progress(progress: int, step: str):
                    update_task(task_id, progress, step)

                result_bytes, detections = translate_image(
                    image_bytes=image_bytes,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    use_manga_ocr=_use_manga,
                    use_gemini=_use_gem,
                    gemini_api_key=_gem_key,
                    on_progress=on_progress,
                )
                complete_task(task_id, result_bytes, detections)
            except Exception as e:
                traceback.print_exc()
                fail_task(task_id, str(e))

        thread = threading.Thread(target=process, daemon=True)
        thread.start()

        return {"task_id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/image/progress/{task_id}")
async def get_image_progress(task_id: str):
    """SSE endpoint for real-time progress of image translation."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_stream():
        last_progress = -1
        while True:
            task = get_task(task_id)
            if not task:
                break

            if task.progress != last_progress:
                last_progress = task.progress
                data = {
                    "progress": task.progress,
                    "step": task.step,
                    "status": task.status.value,
                }
                if task.status == TaskStatus.FAILED:
                    data["error"] = task.error
                if task.status == TaskStatus.COMPLETED:
                    data["detections"] = [
                        {
                            "original": d["text"],
                            "translated": d.get("translated_text", ""),
                            "confidence": d["confidence"],
                        }
                        for d in task.detections
                    ]
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                break

            await asyncio.sleep(0.3)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/image/result/{task_id}")
async def get_image_result(task_id: str):
    """Get the result image for a completed task."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status == TaskStatus.FAILED:
        raise HTTPException(status_code=500, detail=task.error or "Task failed")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=202, detail="Task still processing")

    return Response(
        content=task.result,
        media_type="image/png",
    )


@router.get("/languages")
async def get_languages():
    """Get list of supported languages."""
    return get_supported_languages()
