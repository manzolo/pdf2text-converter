import os
import fitz  # PyMuPDF
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class PDFChunker:
    """
    Utility to chunk large PDF files for processing.
    """

    def __init__(self, chunk_size_mb: int = 10):
        """
        Initialize chunker.

        Args:
            chunk_size_mb: Target size for each chunk in MB
        """
        self.chunk_size_mb = chunk_size_mb
        self.chunk_size_bytes = chunk_size_mb * 1024 * 1024

    def create_chunks(self, file_path: str) -> List[Dict]:
        """
        Create logical chunks of a PDF based on page count and file size.

        Args:
            file_path: Path to PDF file

        Returns:
            List of chunk info dictionaries with start_page and end_page
        """
        doc = fitz.open(file_path)
        total_pages = doc.page_count
        file_size = os.path.getsize(file_path)

        # Estimate pages per chunk
        avg_page_size = file_size / total_pages if total_pages > 0 else file_size
        pages_per_chunk = max(1, int(self.chunk_size_bytes / avg_page_size))

        chunks = []
        current_page = 0

        while current_page < total_pages:
            end_page = min(current_page + pages_per_chunk - 1, total_pages - 1)

            chunks.append({
                "start_page": current_page,
                "end_page": end_page,
                "page_count": end_page - current_page + 1,
                "estimated_size_mb": (end_page - current_page + 1) * avg_page_size / (1024 * 1024)
            })

            current_page = end_page + 1

        doc.close()

        logger.info(f"Created {len(chunks)} chunks for {total_pages} pages")
        return chunks

    def get_page_count(self, file_path: str) -> int:
        """Get total page count of PDF"""
        doc = fitz.open(file_path)
        count = doc.page_count
        doc.close()
        return count

    def estimate_processing_time(self, file_path: str, seconds_per_page: float = 2.0) -> Dict:
        """
        Estimate processing time for a PDF.

        Args:
            file_path: Path to PDF
            seconds_per_page: Estimated seconds to process each page

        Returns:
            Dictionary with time estimates
        """
        page_count = self.get_page_count(file_path)
        total_seconds = page_count * seconds_per_page

        return {
            "pages": page_count,
            "estimated_seconds": round(total_seconds, 2),
            "estimated_minutes": round(total_seconds / 60, 2)
        }
