from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

from app.api import routes

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="PDF2Text Converter API",
    description="AI-powered PDF text extraction with support for large files",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.router, prefix="/api")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "extraction_method": os.getenv("EXTRACTION_METHOD", "tesseract"),
        "gpu_enabled": os.getenv("USE_GPU", "false") == "true",
        "max_file_size_mb": int(os.getenv("MAX_FILE_SIZE_MB", "500")),
        "chunk_size_mb": int(os.getenv("CHUNK_SIZE_MB", "10"))
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "PDF2Text Converter API",
        "docs": "/docs",
        "health": "/health"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )
