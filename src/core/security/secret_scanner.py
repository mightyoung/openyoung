"""
Secret Scanner - Scans code and text for secrets and sensitive information.

Integrates with PIIScanner to detect:
- API keys, tokens, and credentials
- Personally Identifiable Information (PII)
- Security-sensitive patterns
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.core.security.pii_scanner import PIIScanner, PIIMatch, PIIType


class SecretType(Enum):
    """Types of secrets that can be detected."""

    # Credentials
    API_KEY = "api_key"
    PRIVATE_KEY = "private_key"
    Bearer_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"

    # Cloud credentials
    AWS_ACCESS_KEY = "aws_access_key"
    AWS_SECRET_KEY = "aws_secret_key"
    GCP_API_KEY = "gcp_api_key"
    AZURE_CONNECTION_STRING = "azure_connection_string"

    # Database
    DB_CONNECTION_STRING = "db_connection_string"

    # PII (delegated to PIIScanner)
    PII = "pii"


@dataclass
class SecretMatch:
    """Represents a secret match found in text."""

    secret_type: SecretType
    value: str
    start: int
    end: int
    masked_value: str
    is_pii: bool = False
    pii_match: Optional[PIIMatch] = None

    def __post_init__(self):
        if not self.masked_value:
            self.masked_value = self._mask_value()

    def _mask_value(self) -> str:
        """Mask the secret value for safe display."""
        if self.secret_type == SecretType.API_KEY:
            # API key: first 8 + *** + last 4
            if len(self.value) >= 12:
                return f"{self.value[:8]}***{self.value[-4:]}"
            return "***"

        if self.secret_type == SecretType.PRIVATE_KEY:
            # Private key: first 7 + *** (RSA/DSA private key markers)
            if "PRIVATE KEY" in self.value:
                return "-----BEGIN PRIVATE KEY*****"
            if "RSA PRIVATE KEY" in self.value:
                return "-----BEGIN RSA PRIVATE KEY*****"
            return "***"

        if self.secret_type in (SecretType.Bearer_TOKEN, SecretType.BASIC_AUTH):
            # Token: first 7 (Bearer ) + *** or Basic + base64 + ***
            if len(self.value) > 15:
                return f"{self.value[:7]}***{self.value[-4:]}"
            return "***"

        if self.secret_type == SecretType.AWS_ACCESS_KEY:
            # AWS Access Key ID: AKIA + 16 chars
            if len(self.value) >= 20:
                return f"{self.value[:4]}***{self.value[-4:]}"
            return "AKIA***"

        if self.secret_type == SecretType.AWS_SECRET_KEY:
            return "AWS_SECRET_KEY***"

        if self.secret_type == SecretType.PII and self.pii_match:
            return self.pii_match.masked_value

        return "***"


class SecretScanner:
    """Scanner for detecting secrets and PII in code/text."""

    # API Key patterns (generic)
    API_KEY_PATTERN = r"\b[Aa][Pp][Ii]_?[Kk][Ee][Yy]\s*[:=]\s*['\"]?[\w\-]{20,}['\"]?"

    # Bearer token patterns
    BEARER_TOKEN_PATTERN = r"\b[Bb]earer\s+[A-Za-z0-9\-_\.]+\b"

    # Basic auth pattern
    BASIC_AUTH_PATTERN = r"\b[Bb]asic\s+[A-Za-z0-9+\/]+=*\b"

    # AWS Access Key ID
    AWS_ACCESS_KEY_PATTERN = r"\bAKIA[0-9A-Z]{16}\b"

    # AWS Secret Key
    AWS_SECRET_KEY_PATTERN = r"\b[Aa][Ww][Ss][\s_-]?[Ss]ecret[\s_-]?[Kk]ey\s*[:=]\s*['\"]?[\w+\/]{40}['\"]?"

    # GCP API Key
    GCP_API_KEY_PATTERN = r"\b[Aa][Ii][Zz][Aa][-_][A-Za-z0-9_\-]{20,}\b"

    # Azure connection string
    AZURE_CONNECTION_PATTERN = r"\b(DefaultEndpointsProtocol|AccountName|AccountKey)\s*=\s*[^;]+"

    # Database connection string
    DB_CONNECTION_PATTERN = r"\b((mongodb|postgres|mysql|postgresql|redis|mssql):\/\/[\w\-\.:@\/]+)"

    # Private key patterns
    PRIVATE_KEY_PATTERN = r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----"

    def __init__(self, include_pii: bool = True, validate_bank_cards: bool = True):
        """Initialize the secret scanner.

        Args:
            include_pii: If True, also scan for PII using PIIScanner
            validate_bank_cards: If True, validate bank card numbers using Luhn
        """
        self._include_pii = include_pii
        self._pii_scanner = PIIScanner(validate_bank_cards=validate_bank_cards) if include_pii else None

        self._patterns: dict[SecretType, re.Pattern] = {
            SecretType.API_KEY: re.compile(self.API_KEY_PATTERN),
            SecretType.Bearer_TOKEN: re.compile(self.BEARER_TOKEN_PATTERN),
            SecretType.BASIC_AUTH: re.compile(self.BASIC_AUTH_PATTERN),
            SecretType.AWS_ACCESS_KEY: re.compile(self.AWS_ACCESS_KEY_PATTERN),
            SecretType.AWS_SECRET_KEY: re.compile(self.AWS_SECRET_KEY_PATTERN),
            SecretType.GCP_API_KEY: re.compile(self.GCP_API_KEY_PATTERN),
            SecretType.AZURE_CONNECTION_STRING: re.compile(self.AZURE_CONNECTION_PATTERN),
            SecretType.DB_CONNECTION_STRING: re.compile(self.DB_CONNECTION_PATTERN),
            SecretType.PRIVATE_KEY: re.compile(self.PRIVATE_KEY_PATTERN),
        }

    def scan(
        self,
        text: str,
        secret_types: Optional[list[SecretType]] = None,
        include_pii: Optional[bool] = None,
    ) -> list[SecretMatch]:
        """Scan text for secrets and optionally PII.

        Args:
            text: Text to scan
            secret_types: Specific secret types to scan for. If None, scans for all non-PII types.
            include_pii: Override the include_pii setting for this scan.

        Returns:
            List of secret matches found in the text
        """
        if secret_types is None:
            secret_types = [st for st in SecretType if st != SecretType.PII]

        matches: list[SecretMatch] = []

        # Scan for secrets
        for secret_type in secret_types:
            if secret_type == SecretType.PII:
                continue

            pattern = self._patterns.get(secret_type)
            if pattern is None:
                continue

            for match in pattern.finditer(text):
                matches.append(
                    SecretMatch(
                        secret_type=secret_type,
                        value=match.group(),
                        start=match.start(),
                        end=match.end(),
                        masked_value="",
                    )
                )

        # Scan for PII if enabled
        should_include_pii = include_pii if include_pii is not None else self._include_pii
        if should_include_pii and self._pii_scanner:
            pii_matches = self._pii_scanner.scan(text)
            for pii_match in pii_matches:
                matches.append(
                    SecretMatch(
                        secret_type=SecretType.PII,
                        value=pii_match.value,
                        start=pii_match.start,
                        end=pii_match.end,
                        masked_value=pii_match.masked_value,
                        is_pii=True,
                        pii_match=pii_match,
                    )
                )

        # Sort by position
        matches.sort(key=lambda m: m.start)
        return matches

    def contains_secrets(
        self,
        text: str,
        secret_types: Optional[list[SecretType]] = None,
        include_pii: Optional[bool] = None,
    ) -> bool:
        """Check if text contains any secrets.

        Args:
            text: Text to check
            secret_types: Specific secret types to check for
            include_pii: Override the include_pii setting

        Returns:
            True if any secrets are found
        """
        return len(self.scan(text, secret_types, include_pii)) > 0

    def get_secret_summary(self, text: str) -> dict[SecretType, int]:
        """Get a summary of secret counts by type.

        Args:
            text: Text to analyze

        Returns:
            Dictionary mapping secret type to count
        """
        matches = self.scan(text)
        summary: dict[SecretType, int] = {st: 0 for st in SecretType}
        for match in matches:
            summary[match.secret_type] += 1
        return summary


# Default scanner instance
default_scanner = SecretScanner()
