import unicodedata
import re


class TextNormalizer:
    """
    Utility to normalize and clean extracted text from PDFs.
    Handles ligatures, special characters, and formatting issues.
    """

    # Common PDF ligatures and their replacements
    LIGATURES = {
        '\ufb00': 'ff',  # ﬀ
        '\ufb01': 'fi',  # ﬁ
        '\ufb02': 'fl',  # ﬂ
        '\ufb03': 'ffi', # ﬃ
        '\ufb04': 'ffl', # ﬄ
        '\ufb05': 'ft',  # ﬅ
        '\ufb06': 'st',  # ﬆ
        # Additional ligatures
        'ﬀ': 'ff',
        'ﬁ': 'fi',
        'ﬂ': 'fl',
        'ﬃ': 'ffi',
        'ﬄ': 'ffl',
        'ﬅ': 'ft',
        'ﬆ': 'st',
    }

    @staticmethod
    def normalize_ligatures(text: str) -> str:
        """
        Replace PDF ligatures with standard characters.

        Args:
            text: Text containing ligatures

        Returns:
            Text with ligatures replaced
        """
        for ligature, replacement in TextNormalizer.LIGATURES.items():
            text = text.replace(ligature, replacement)
        return text

    @staticmethod
    def normalize_unicode(text: str, form='NFKC') -> str:
        """
        Normalize unicode characters to a standard form.

        Args:
            text: Text to normalize
            form: Normalization form (NFKC, NFC, NFKD, NFD)

        Returns:
            Normalized text
        """
        return unicodedata.normalize(form, text)

    @staticmethod
    def clean_whitespace(text: str) -> str:
        """
        Clean up excessive whitespace while preserving paragraph structure.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)

        # Replace multiple newlines with maximum 2 (paragraph break)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)

        return text.strip()

    @staticmethod
    def remove_soft_hyphens(text: str) -> str:
        """
        Remove soft hyphens (used for word breaking in PDFs).

        Args:
            text: Text containing soft hyphens

        Returns:
            Text without soft hyphens
        """
        # Soft hyphen at end of line followed by continuation
        text = re.sub(r'-\s*\n\s*', '', text)

        # Unicode soft hyphen
        text = text.replace('\u00ad', '')

        return text

    @staticmethod
    def fix_common_ocr_errors(text: str) -> str:
        """
        Fix common OCR errors and character misrecognitions.

        Args:
            text: Text to fix

        Returns:
            Fixed text
        """
        fixes = {
            # Common OCR confusions
            r'\bl\b': 'I',  # lowercase l confused with I (context-dependent)
            r'\bO\b': '0',  # O confused with zero (context-dependent)
        }

        # Apply fixes cautiously
        # Note: These are commented out by default as they can cause issues
        # Uncomment if needed for specific cases
        # for pattern, replacement in fixes.items():
        #     text = re.sub(pattern, replacement, text)

        return text

    @staticmethod
    def normalize(text: str,
                  ligatures: bool = True,
                  unicode_norm: bool = True,
                  whitespace: bool = True,
                  soft_hyphens: bool = True,
                  ocr_errors: bool = False) -> str:
        """
        Apply all normalization steps.

        Args:
            text: Text to normalize
            ligatures: Replace ligatures
            unicode_norm: Normalize unicode
            whitespace: Clean whitespace
            soft_hyphens: Remove soft hyphens
            ocr_errors: Fix common OCR errors

        Returns:
            Fully normalized text
        """
        if ligatures:
            text = TextNormalizer.normalize_ligatures(text)

        if unicode_norm:
            text = TextNormalizer.normalize_unicode(text)

        if soft_hyphens:
            text = TextNormalizer.remove_soft_hyphens(text)

        if whitespace:
            text = TextNormalizer.clean_whitespace(text)

        if ocr_errors:
            text = TextNormalizer.fix_common_ocr_errors(text)

        return text
