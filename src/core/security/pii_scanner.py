"""
PII Scanner - Detects personally identifiable information in text.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PIIType(Enum):
    """Types of PII that can be detected."""

    CHINA_ID = "china_id"  # Chinese ID card (18 digits)
    PHONE = "phone"  # Chinese mobile phone (11 digits)
    BANK_CARD = "bank_card"  # Bank card (16-19 digits)
    EMAIL = "email"  # Email address


@dataclass
class PIIMatch:
    """Represents a PII match found in text."""

    pii_type: PIIType
    value: str
    start: int
    end: int
    masked_value: str

    def __post_init__(self):
        if not self.masked_value:
            self.masked_value = self._mask_value()

    def _mask_value(self) -> str:
        """Mask the PII value for safe display."""
        if self.pii_type == PIIType.EMAIL:
            # Mask email: first char + *** + domain
            parts = self.value.split("@")
            if len(parts) == 2:
                name = parts[0]
                domain = parts[1]
                if len(name) > 1:
                    return f"{name[0]}***@{domain}"
                return f"***@{domain}"
            return "***@***"

        if self.pii_type == PIIType.CHINA_ID:
            # Mask ID: first 6 + *** + last 4
            if len(self.value) >= 10:
                return f"{self.value[:6]}****{self.value[-4:]}"
            return "**********"

        if self.pii_type == PIIType.PHONE:
            # Mask phone: first 3 + **** + last 4
            if len(self.value) >= 7:
                return f"{self.value[:3]}****{self.value[-4:]}"
            return "***-****-****"

        if self.pii_type == PIIType.BANK_CARD:
            # Mask bank card: first 4 + **** + last 4
            if len(self.value) >= 8:
                return f"{self.value[:4]}****{self.value[-4:]}"
            return "****-****-****-****"

        return "****"


class PIIScanner:
    """Scanner for detecting PII in text."""

    # Chinese ID card: 18 digits, first digit cannot be 0
    CHINA_ID_PATTERN = r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b"

    # Chinese mobile phone: 11 digits, starting with 1
    PHONE_PATTERN = r"\b1[3-9]\d{9}\b"

    # Bank card: 16-19 digits, optionally with spaces or dashes
    # Avoid matching China IDs by excluding the 19/20 year pattern at positions 6-7
    BANK_CARD_PATTERN = r"\b(?:(?![12]\d{5}(?:19|20)\d{2})\d){16,19}\b|\b(?:\d{4}[\s-]){3,4}\d{4}\b"

    # Email: standard email pattern
    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

    def __init__(self):
        """Initialize the PII scanner with compiled patterns."""
        self._patterns: dict[PIIType, re.Pattern] = {
            PIIType.CHINA_ID: re.compile(self.CHINA_ID_PATTERN),
            PIIType.PHONE: re.compile(self.PHONE_PATTERN),
            PIIType.BANK_CARD: re.compile(self.BANK_CARD_PATTERN),
            PIIType.EMAIL: re.compile(self.EMAIL_PATTERN),
        }

    def scan(self, text: str, pii_types: Optional[list[PIIType]] = None) -> list[PIIMatch]:
        """
        Scan text for PII.

        Args:
            text: Text to scan
            pii_types: Specific PII types to scan for. If None, scans for all types.

        Returns:
            List of PII matches found in the text
        """
        if pii_types is None:
            pii_types = list(PIIType)

        matches: list[PIIMatch] = []
        for pii_type in pii_types:
            pattern = self._patterns.get(pii_type)
            if pattern is None:
                continue

            for match in pattern.finditer(text):
                # Normalize bank card: remove spaces and dashes
                value = match.group()
                if pii_type == PIIType.BANK_CARD:
                    value = value.replace(" ", "").replace("-", "")

                matches.append(
                    PIIMatch(
                        pii_type=pii_type,
                        value=value,
                        start=match.start(),
                        end=match.end(),
                        masked_value="",  # Will be computed in __post_init__
                    )
                )

        # Sort by position
        matches.sort(key=lambda m: m.start)
        return matches

    def contains_pii(self, text: str, pii_types: Optional[list[PIIType]] = None) -> bool:
        """
        Check if text contains any PII.

        Args:
            text: Text to check
            pii_types: Specific PII types to check for. If None, checks all types.

        Returns:
            True if any PII is found
        """
        return len(self.scan(text, pii_types)) > 0

    def get_pii_summary(self, text: str) -> dict[PIIType, int]:
        """
        Get a summary of PII counts by type.

        Args:
            text: Text to analyze

        Returns:
            Dictionary mapping PII type to count
        """
        matches = self.scan(text)
        summary: dict[PIIType, int] = {pt: 0 for pt in PIIType}
        for match in matches:
            summary[match.pii_type] += 1
        return summary


# Default scanner instance
default_scanner = PIIScanner()
