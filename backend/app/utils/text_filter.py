import re
from typing import List, Set, Dict
from collections import Counter


class TextFilter:
    """
    Utility to filter out repetitive text like headers, footers, and copyright notices.
    """

    def __init__(self, min_repetition_threshold: int = 3):
        """
        Initialize the text filter.

        Args:
            min_repetition_threshold: Minimum number of times a line must appear
                                     to be considered repetitive
        """
        self.min_repetition_threshold = min_repetition_threshold

    def detect_repetitive_lines(self, pages: List[str]) -> Set[str]:
        """
        Detect lines that appear frequently across multiple pages.

        Args:
            pages: List of page texts

        Returns:
            Set of repetitive lines to filter out
        """
        line_counter = Counter()

        # Count occurrences of each line across all pages
        for page in pages:
            lines = page.split('\n')
            unique_lines = set(lines)  # Count once per page
            for line in unique_lines:
                line_stripped = line.strip()
                # Only consider lines that aren't too long (likely not headers/footers)
                if line_stripped and len(line_stripped) < 200:
                    line_counter[line_stripped] += 1

        # Find lines that appear on many pages
        total_pages = len(pages)
        threshold = max(self.min_repetition_threshold, total_pages * 0.05)  # At least 5% of pages

        repetitive_lines = {
            line for line, count in line_counter.items()
            if count >= threshold
        }

        return repetitive_lines

    def is_copyright_line(self, line: str) -> bool:
        """
        Check if a line is a copyright notice.

        Args:
            line: Text line to check

        Returns:
            True if line appears to be copyright notice
        """
        line_lower = line.lower().strip()

        copyright_patterns = [
            r'©.*\d{4}',  # © 2020, © Copyright 2020, etc.
            r'copyright.*\d{4}',
            r'all rights reserved',
            r'tutti i diritti riservati',
            r'tous droits réservés',
            r'alle rechte vorbehalten',
            r'todos los derechos reservados',
        ]

        for pattern in copyright_patterns:
            if re.search(pattern, line_lower):
                return True

        return False

    def is_page_number(self, line: str) -> bool:
        """
        Check if a line is just a page number.

        Args:
            line: Text line to check

        Returns:
            True if line appears to be a page number
        """
        line_stripped = line.strip()

        # Check if it's just digits
        if line_stripped.isdigit():
            return True

        # Check patterns like "Page 1", "- 1 -", etc.
        page_patterns = [
            r'^page\s+\d+$',
            r'^pagina\s+\d+$',
            r'^\d+\s*/\s*\d+$',  # 1/100
            r'^-\s*\d+\s*-$',  # - 1 -
        ]

        for pattern in page_patterns:
            if re.match(pattern, line_stripped, re.IGNORECASE):
                return True

        return False

    def is_header_footer_candidate(self, line: str) -> bool:
        """
        Check if a line looks like a typical header/footer.

        Args:
            line: Text line to check

        Returns:
            True if line looks like header/footer
        """
        line_stripped = line.strip()

        # Empty or very short lines
        if len(line_stripped) < 3:
            return True

        # Page numbers
        if self.is_page_number(line_stripped):
            return True

        # Copyright
        if self.is_copyright_line(line_stripped):
            return True

        # Common publisher names or markers
        publisher_markers = [
            '© erickson',
            '© edizioni',
            'www.',
            'http://',
            'https://',
        ]

        line_lower = line_stripped.lower()
        for marker in publisher_markers:
            if marker in line_lower:
                return True

        return False

    def filter_page(self, page_text: str, repetitive_lines: Set[str], remove_copyright: bool = True) -> str:
        """
        Filter repetitive content from a single page.

        Args:
            page_text: Text of the page
            repetitive_lines: Set of lines to remove
            remove_copyright: Whether to remove copyright notices

        Returns:
            Filtered page text
        """
        lines = page_text.split('\n')
        filtered_lines = []

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines initially (we'll add them back for structure)
            if not line_stripped:
                continue

            # Check if line is in repetitive set
            if line_stripped in repetitive_lines:
                continue

            # Check if it's a copyright line (if enabled)
            if remove_copyright and self.is_copyright_line(line):
                continue

            # Check if it's a page number
            if self.is_page_number(line):
                continue

            # Keep the line
            filtered_lines.append(line)

        # Join with single newline and clean up excessive spacing
        result = '\n'.join(filtered_lines)

        # Ensure proper paragraph spacing
        result = re.sub(r'\n\s*\n\s*\n+', '\n\n', result)

        return result.strip()

    def filter_document(
        self,
        pages: List[str],
        remove_repetitive: bool = True,
        remove_copyright: bool = True,
        min_threshold: int = None
    ) -> List[str]:
        """
        Filter repetitive content from all pages.

        Args:
            pages: List of page texts
            remove_repetitive: Remove lines that appear on multiple pages
            remove_copyright: Remove copyright notices
            min_threshold: Override default repetition threshold

        Returns:
            List of filtered page texts
        """
        if min_threshold:
            self.min_repetition_threshold = min_threshold

        # Detect repetitive lines if enabled
        repetitive_lines = set()
        if remove_repetitive:
            repetitive_lines = self.detect_repetitive_lines(pages)

        # Filter each page
        filtered_pages = []
        for page in pages:
            filtered = self.filter_page(page, repetitive_lines, remove_copyright)
            if filtered:  # Only add non-empty pages
                filtered_pages.append(filtered)

        return filtered_pages

    def get_repetitive_patterns(self, pages: List[str]) -> Dict[str, int]:
        """
        Get a report of repetitive patterns found in the document.

        Args:
            pages: List of page texts

        Returns:
            Dictionary mapping repetitive lines to their occurrence count
        """
        line_counter = Counter()

        for page in pages:
            lines = page.split('\n')
            unique_lines = set(lines)
            for line in unique_lines:
                line_stripped = line.strip()
                if line_stripped and len(line_stripped) < 200:
                    if self.is_header_footer_candidate(line_stripped):
                        line_counter[line_stripped] += 1

        # Return lines that appear on multiple pages
        return {
            line: count for line, count in line_counter.items()
            if count >= self.min_repetition_threshold
        }
