from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
import os
import uuid
import aiofiles
from pathlib import Path
import json

from app.services.pdf_processor import PDFProcessor

router = APIRouter()

UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize PDF processor
pdf_processor = PDFProcessor()


@router.post("/extract")
async def extract_text_from_pdf(
    file: UploadFile = File(...),
    use_ocr: bool = True,
    chunk_processing: bool = True,
    language: str = "eng",
    remove_repetitive: bool = True,
    remove_copyright: bool = True
):
    """
    Extract text from a PDF file using AI.

    Args:
        file: PDF file to process
        use_ocr: Whether to use OCR for image-based PDFs
        chunk_processing: Process large files in chunks
        language: OCR language (eng, ita, fra, deu, spa, etc.)
        remove_repetitive: Remove repeated headers/footers
        remove_copyright: Remove copyright notices

    Returns:
        JSON with extracted text and metadata
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Check file size
    max_size = int(os.getenv("MAX_FILE_SIZE_MB", "500")) * 1024 * 1024

    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}.pdf"

    try:
        # Save uploaded file
        total_size = 0
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):  # Read 1MB at a time
                total_size += len(content)
                if total_size > max_size:
                    await out_file.close()
                    file_path.unlink()
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size is {max_size // (1024*1024)}MB"
                    )
                await out_file.write(content)

        # Process PDF
        result = await pdf_processor.process_pdf(
            file_path=str(file_path),
            use_ocr=use_ocr,
            chunk_processing=chunk_processing,
            language=language,
            remove_repetitive=remove_repetitive,
            remove_copyright=remove_copyright
        )

        # Cleanup
        file_path.unlink()

        return JSONResponse(content={
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "pages": result["pages"],
            "total_chars": result["total_chars"],
            "chunks_processed": result.get("chunks_processed", 1),
            "text": result["text"],
            "metadata": result.get("metadata", {})
        })

    except Exception as e:
        # Cleanup on error
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@router.post("/extract-stream")
async def extract_text_stream(
    file: UploadFile = File(...),
    use_ocr: bool = True,
    language: str = "eng"
):
    """
    Extract text from a PDF file and stream results as they're processed.
    Useful for very large files.

    Returns:
        Streaming JSON response with chunks of extracted text
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}.pdf"

    try:
        # Save uploaded file
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):
                await out_file.write(content)

        # Stream processing
        async def generate():
            async for chunk in pdf_processor.process_pdf_stream(
                file_path=str(file_path),
                use_ocr=use_ocr,
                language=language
            ):
                yield json.dumps(chunk) + "\n"

            # Cleanup after streaming
            file_path.unlink()

        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson"
        )

    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@router.get("/status")
async def get_status():
    """Get API status and configuration"""
    return {
        "status": "ready",
        "processor": pdf_processor.get_info(),
        "max_file_size_mb": int(os.getenv("MAX_FILE_SIZE_MB", "500")),
        "chunk_size_mb": int(os.getenv("CHUNK_SIZE_MB", "10"))
    }
