import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from typing import Dict, List, AsyncGenerator
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from app.utils.chunking import PDFChunker
from app.utils.text_normalizer import TextNormalizer
from app.utils.text_filter import TextFilter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    AI-powered PDF text extraction processor with support for large files.
    """

    def __init__(self):
        self.extraction_method = os.getenv("EXTRACTION_METHOD", "tesseract")
        self.use_gpu = os.getenv("USE_GPU", "false") == "true"
        self.chunk_size_mb = int(os.getenv("CHUNK_SIZE_MB", "10"))
        self.chunker = PDFChunker(chunk_size_mb=self.chunk_size_mb)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.normalizer = TextNormalizer()
        self.text_filter = TextFilter(min_repetition_threshold=3)

        logger.info(f"PDF Processor initialized - Method: {self.extraction_method}, GPU: {self.use_gpu}")

    def get_info(self) -> Dict:
        """Get processor information"""
        return {
            "extraction_method": self.extraction_method,
            "gpu_enabled": self.use_gpu,
            "chunk_size_mb": self.chunk_size_mb
        }

    async def process_pdf(
        self,
        file_path: str,
        use_ocr: bool = True,
        chunk_processing: bool = True,
        language: str = "eng",
        remove_repetitive: bool = True,
        remove_copyright: bool = True
    ) -> Dict:
        """
        Process a PDF file and extract text.

        Args:
            file_path: Path to the PDF file
            use_ocr: Whether to use OCR for image-based content
            chunk_processing: Process in chunks for large files
            language: OCR language code
            remove_repetitive: Remove repeated headers/footers
            remove_copyright: Remove copyright notices

        Returns:
            Dictionary with extracted text and metadata
        """
        logger.info(f"Processing PDF: {file_path}")

        # Check if file should be chunked
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        if chunk_processing and file_size_mb > self.chunk_size_mb:
            return await self._process_chunked(file_path, use_ocr, language, remove_repetitive, remove_copyright)
        else:
            return await self._process_whole(file_path, use_ocr, language, remove_repetitive, remove_copyright)

    async def _process_whole(
        self,
        file_path: str,
        use_ocr: bool,
        language: str,
        remove_repetitive: bool,
        remove_copyright: bool
    ) -> Dict:
        """Process entire PDF at once"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._extract_text_sync,
            file_path,
            use_ocr,
            language,
            remove_repetitive,
            remove_copyright
        )

    async def _process_chunked(
        self,
        file_path: str,
        use_ocr: bool,
        language: str,
        remove_repetitive: bool,
        remove_copyright: bool
    ) -> Dict:
        """Process PDF in chunks for large files"""
        logger.info(f"Processing file in chunks: {file_path}")

        chunks = self.chunker.create_chunks(file_path)
        all_text = []
        total_pages = 0
        chunks_processed = 0

        for chunk_info in chunks:
            logger.info(f"Processing chunk {chunks_processed + 1}/{len(chunks)}: pages {chunk_info['start_page']}-{chunk_info['end_page']}")

            # Process chunk
            result = await self._process_page_range(
                file_path,
                chunk_info['start_page'],
                chunk_info['end_page'],
                use_ocr,
                language,
                remove_repetitive,
                remove_copyright
            )

            all_text.append(result['text'])
            total_pages += result['pages']
            chunks_processed += 1

        combined_text = "\n\n".join(all_text)

        return {
            "text": combined_text,
            "pages": total_pages,
            "total_chars": len(combined_text),
            "chunks_processed": chunks_processed,
            "metadata": {
                "file_size_mb": os.path.getsize(file_path) / (1024 * 1024),
                "chunked": True
            }
        }

    async def _process_page_range(
        self,
        file_path: str,
        start_page: int,
        end_page: int,
        use_ocr: bool,
        language: str,
        remove_repetitive: bool,
        remove_copyright: bool
    ) -> Dict:
        """Process a specific range of pages"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._extract_text_range_sync,
            file_path,
            start_page,
            end_page,
            use_ocr,
            language,
            remove_repetitive,
            remove_copyright
        )

    def _extract_text_sync(
        self,
        file_path: str,
        use_ocr: bool,
        language: str,
        remove_repetitive: bool,
        remove_copyright: bool
    ) -> Dict:
        """Synchronous text extraction from entire PDF"""
        doc = fitz.open(file_path)
        page_texts = []
        total_pages = doc.page_count

        # Extract text from all pages
        for page_num in range(total_pages):
            page = doc[page_num]
            text = self._extract_page_text(page, use_ocr, language)
            page_texts.append(text)

        doc.close()

        # Apply filtering if enabled
        if remove_repetitive or remove_copyright:
            page_texts = self.text_filter.filter_document(
                page_texts,
                remove_repetitive=remove_repetitive,
                remove_copyright=remove_copyright
            )

        # Add page markers and combine
        all_text = []
        for idx, text in enumerate(page_texts):
            if text.strip():
                all_text.append(f"--- Page {idx + 1} ---\n{text}")

        combined_text = "\n\n".join(all_text)

        return {
            "text": combined_text,
            "pages": total_pages,
            "total_chars": len(combined_text),
            "metadata": {
                "file_size_mb": os.path.getsize(file_path) / (1024 * 1024),
                "chunked": False
            }
        }

    def _extract_text_range_sync(
        self,
        file_path: str,
        start_page: int,
        end_page: int,
        use_ocr: bool,
        language: str,
        remove_repetitive: bool,
        remove_copyright: bool
    ) -> Dict:
        """Synchronous text extraction from page range"""
        doc = fitz.open(file_path)
        page_texts = []

        # Extract text from page range
        for page_num in range(start_page, min(end_page + 1, doc.page_count)):
            page = doc[page_num]
            text = self._extract_page_text(page, use_ocr, language)
            page_texts.append(text)

        doc.close()

        # Apply filtering if enabled
        if remove_repetitive or remove_copyright:
            page_texts = self.text_filter.filter_document(
                page_texts,
                remove_repetitive=remove_repetitive,
                remove_copyright=remove_copyright
            )

        # Add page markers and combine
        all_text = []
        for idx, text in enumerate(page_texts):
            if text.strip():
                page_num = start_page + idx
                all_text.append(f"--- Page {page_num + 1} ---\n{text}")

        combined_text = "\n\n".join(all_text)

        return {
            "text": combined_text,
            "pages": end_page - start_page + 1,
            "total_chars": len(combined_text)
        }

    def _extract_page_text(self, page, use_ocr: bool, language: str) -> str:
        """Extract text from a single page"""
        # First, try to extract text directly
        text = page.get_text()

        # If no text found or very little text, use OCR
        if use_ocr and len(text.strip()) < 50:
            text = self._ocr_page(page, language)

        # Normalize the extracted text
        text = self.normalizer.normalize(
            text,
            ligatures=True,
            unicode_norm=True,
            whitespace=True,
            soft_hyphens=True,
            ocr_errors=False
        )

        return text

    def _ocr_page(self, page, language: str) -> str:
        """Perform OCR on a page"""
        try:
            # Render page to image
            mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
            pix = page.get_pixmap(matrix=mat)

            # Convert to PIL Image
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))

            # Perform OCR
            custom_config = f'--oem 3 --psm 6 -l {language}'
            text = pytesseract.image_to_string(image, config=custom_config)

            return text
        except Exception as e:
            logger.error(f"OCR failed: {str(e)}")
            return ""

    async def process_pdf_stream(
        self,
        file_path: str,
        use_ocr: bool,
        language: str
    ) -> AsyncGenerator[Dict, None]:
        """
        Process PDF and stream results page by page.
        Useful for real-time feedback on large files.
        """
        doc = fitz.open(file_path)
        total_pages = doc.page_count

        for page_num in range(total_pages):
            page = doc[page_num]

            # Extract text in executor to not block
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                self.executor,
                self._extract_page_text,
                page,
                use_ocr,
                language
            )

            yield {
                "page": page_num + 1,
                "total_pages": total_pages,
                "text": text,
                "progress": round((page_num + 1) / total_pages * 100, 2)
            }

        doc.close()
