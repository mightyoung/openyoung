"""
PII Scanner - Detects personally identifiable information in text.

Supports:
- Chinese PII: ID cards, phone numbers, bank cards
- International PII: SSN, EU national IDs, passports, UK NIN, etc.
- Luhn validation for bank card numbers
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PIIType(Enum):
    """Types of PII that can be detected."""

    # Chinese PII
    CHINA_ID = "china_id"  # Chinese ID card (18 digits)
    CHINA_PASSPORT = "china_passport"  # Chinese passport number
    PHONE = "phone"  # Chinese mobile phone (11 digits)
    BANK_CARD = "bank_card"  # Bank card (16-19 digits)

    # International PII
    US_SSN = "us_ssn"  # US Social Security Number
    UK_NIN = "uk_nin"  # UK National Insurance Number
    EU_NATIONAL_ID = "eu_national_id"  # EU national ID cards
    PASSPORT = "passport"  # General passport numbers

    # Common
    EMAIL = "email"  # Email address
    IP_ADDRESS = "ip_address"  # IP address


@dataclass
class PIIMatch:
    """Represents a PII match found in text."""

    pii_type: PIIType
    value: str
    start: int
    end: int
    masked_value: str
    is_valid: bool = True  # Whether the PII passes validation (e.g., Luhn for bank cards)

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

        if self.pii_type == PIIType.CHINA_PASSPORT:
            # Mask passport: first 2 + *** + last 2
            if len(self.value) >= 6:
                return f"{self.value[:2]}****{self.value[-2:]}"
            return "******"

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

        if self.pii_type == PIIType.US_SSN:
            # Mask SSN: first 3 + ** + last 4
            if len(self.value) >= 9:
                return f"{self.value[:3]}***{self.value[-4:]}"
            return "***-**-****"

        if self.pii_type == PIIType.UK_NIN:
            # Mask UK NIN: first 2 + *** + last 4
            if len(self.value) >= 9:
                return f"{self.value[:2]}***{self.value[-4:]}"
            return "******"

        if self.pii_type == PIIType.PASSPORT:
            # Passport: first 3 + **** + last 2 (for alphanumeric passports)
            if len(self.value) >= 7:
                return f"{self.value[:3]}****{self.value[-2:]}"
            return "****"

        if self.pii_type == PIIType.EU_NATIONAL_ID:
            # EU National ID: first 2 + **** + last 3
            if len(self.value) >= 8:
                return f"{self.value[:2]}****{self.value[-3:]}"
            return "****"

        if self.pii_type == PIIType.IP_ADDRESS:
            # Mask last octet
            parts = self.value.split(".")
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.{parts[2]}.***"
            return "***.***.***.***"

        return "****"


class PIIScanner:
    """Scanner for detecting PII in text."""

    # ==================== Chinese PII Patterns ====================

    # Chinese ID card: 18 digits, first digit cannot be 0
    CHINA_ID_PATTERN = r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b"

    # Chinese mobile phone: 11 digits, starting with 1
    PHONE_PATTERN = r"\b1[3-9]\d{9}\b"

    # Chinese passport: G/E followed by 8 digits
    CHINA_PASSPORT_PATTERN = r"\b[G,E]\d{8}\b"

    # Bank card: 16-19 digits, optionally with spaces or dashes
    # Avoid matching China IDs by excluding the 19/20 year pattern at positions 6-7
    BANK_CARD_PATTERN = r"\b(?:(?![12]\d{5}(?:19|20)\d{2})\d){16,19}\b|\b(?:\d{4}[\s-]){3,4}\d{4}\b"

    # ==================== International PII Patterns ====================

    # US SSN: XXX-XX-XXXX or XXXXXXXXX (9 digits)
    US_SSN_PATTERN = r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b"

    # UK National Insurance Number: QQ 12 34 56 C (two letters, space, two digits, space, two digits, space, letter)
    UK_NIN_PATTERN = r"\b[A-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-Z]\b"

    # EU National ID cards (sample patterns for major EU countries)
    # Germany: 9 digits followed by letter
    EU_GERMAN_ID_PATTERN = r"\b\d{9}[A-Z]\b"
    # France: 2 letters + 6 digits + 2 letters
    EU_FRENCH_ID_PATTERN = r"\b[A-Z]{2}\d{6}[A-Z]{2}\b"
    # Italy: 2 letters + 7 digits + letter
    EU_ITALY_ID_PATTERN = r"\b[A-Z]{2}\d{7}[A-Z]\b"
    # Spain: 3 letters + 6 digits + 1 letter (DNI/NIE)
    EU_SPAIN_ID_PATTERN = r"\b[A-Z]\d{8}[A-Z]\b|\b\d{8}[A-Z]\b"
    # Generic EU ID pattern: 2-3 letters followed by 5-9 digits
    EU_GENERIC_ID_PATTERN = r"\b[A-Z]{2,3}\d{5,9}\b"

    # Passport: General passport number pattern (6-9 alphanumeric characters)
    PASSPORT_PATTERN = r"\b[A-Z]{1,2}\d{6,9}\b"

    # IP Address: IPv4
    IP_V4_PATTERN = r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"

    # Email: standard email pattern
    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

    def __init__(self, validate_bank_cards: bool = True):
        """Initialize the PII scanner with compiled patterns.

        Args:
            validate_bank_cards: If True, validates bank card numbers using Luhn algorithm.
        """
        self._validate_bank_cards = validate_bank_cards
        self._patterns: dict[PIIType, re.Pattern] = {
            PIIType.CHINA_ID: re.compile(self.CHINA_ID_PATTERN),
            PIIType.CHINA_PASSPORT: re.compile(self.CHINA_PASSPORT_PATTERN),
            PIIType.PHONE: re.compile(self.PHONE_PATTERN),
            PIIType.BANK_CARD: re.compile(self.BANK_CARD_PATTERN),
            PIIType.US_SSN: re.compile(self.US_SSN_PATTERN),
            PIIType.UK_NIN: re.compile(self.UK_NIN_PATTERN),
            PIIType.EU_NATIONAL_ID: re.compile(f"{self.EU_GERMAN_ID_PATTERN}|{self.EU_FRENCH_ID_PATTERN}|{self.EU_ITALY_ID_PATTERN}|{self.EU_SPAIN_ID_PATTERN}|{self.EU_GENERIC_ID_PATTERN}"),
            PIIType.PASSPORT: re.compile(self.PASSPORT_PATTERN),
            PIIType.IP_ADDRESS: re.compile(self.IP_V4_PATTERN),
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
                    is_valid = self._validate_luhn(value) if self._validate_bank_cards else True
                else:
                    is_valid = True

                matches.append(
                    PIIMatch(
                        pii_type=pii_type,
                        value=value,
                        start=match.start(),
                        end=match.end(),
                        masked_value="",  # Will be computed in __post_init__
                        is_valid=is_valid,
                    )
                )

        # Sort by position
        matches.sort(key=lambda m: m.start)
        return matches

    @staticmethod
    def _validate_luhn(card_number: str) -> bool:
        """Validate a bank card number using the Luhn algorithm.

        Args:
            card_number: Card number as a string (digits only)

        Returns:
            True if the card number passes Luhn validation
        """
        if not card_number.isdigit() or len(card_number) < 13 or len(card_number) > 19:
            return False

        digits = [int(d) for d in card_number]
        checksum = 0

        # Process from right to left
        for i in range(len(digits) - 1, -1, -1):
            d = digits[i]
            # Double every second digit from the right (which is every odd position from right, 0-indexed)
            if (len(digits) - i) % 2 == 0:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d

        return checksum % 10 == 0

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
