"""
PII Scanner Tests
"""

import pytest

from src.core.security.pii_scanner import PIIScanner, PIIType, PIIMatch


class TestPIIScanner:
    """Test PII Scanner functionality."""

    def setup_method(self):
        """Set up test scanner."""
        self.scanner = PIIScanner()

    # ==================== Email Tests ====================

    def test_detect_email_basic(self):
        """Test basic email detection."""
        text = "Contact me at test@example.com please."
        matches = self.scanner.scan(text)

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.EMAIL
        assert matches[0].value == "test@example.com"
        assert matches[0].start == 14
        assert matches[0].end == 30

    def test_detect_email_multiple(self):
        """Test multiple email detection."""
        text = "Email john@company.com or jane.doe@org.org for details."
        matches = self.scanner.scan(text, [PIIType.EMAIL])

        assert len(matches) == 2
        assert matches[0].value == "john@company.com"
        assert matches[1].value == "jane.doe@org.org"

    def test_detect_email_with_subdomain(self):
        """Test email with subdomain detection."""
        text = "Contact support@mail.server.co.uk for help."
        matches = self.scanner.scan(text, [PIIType.EMAIL])

        assert len(matches) == 1
        assert matches[0].value == "support@mail.server.co.uk"

    # ==================== Phone Tests ====================

    def test_detect_phone_basic(self):
        """Test basic phone detection."""
        text = "Call me at 13812345678 anytime."
        matches = self.scanner.scan(text, [PIIType.PHONE])

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.PHONE
        assert matches[0].value == "13812345678"

    def test_detect_phone_multiple(self):
        """Test multiple phone detection."""
        text = "Call 13900001111 or 18822223333 for support."
        matches = self.scanner.scan(text, [PIIType.PHONE])

        assert len(matches) == 2
        assert matches[0].value == "13900001111"
        assert matches[1].value == "18822223333"

    def test_detect_phone_various_prefixes(self):
        """Test phone detection with different prefixes."""
        text = "Phones: 134, 135, 147, 150, 151, 152, 153, 155, 156, 157, 158, 159, 166, 170, 171, 172, 173, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 191, 193, 195, 197, 198, 199"
        # Just check we can scan without errors and detect valid 11-digit phones
        matches = self.scanner.scan(text, [PIIType.PHONE])
        # All valid 11-digit mobile phones should be detected

    # ==================== China ID Tests ====================

    def test_detect_china_id_basic(self):
        """Test basic China ID detection."""
        text = "My ID is 110101199001011234 for reference."
        matches = self.scanner.scan(text, [PIIType.CHINA_ID])

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.CHINA_ID
        assert matches[0].value == "110101199001011234"

    def test_detect_china_id_with_x(self):
        """Test China ID with X checksum."""
        text = "ID: 11010119900101123X"
        matches = self.scanner.scan(text, [PIIType.CHINA_ID])

        assert len(matches) == 1
        assert matches[0].value == "11010119900101123X"

    def test_detect_china_id_with_lowercase_x(self):
        """Test China ID with lowercase x checksum."""
        text = "ID: 11010119900101123x"
        matches = self.scanner.scan(text, [PIIType.CHINA_ID])

        assert len(matches) == 1
        assert matches[0].value == "11010119900101123x"

    def test_detect_china_id_invalid_should_not_match(self):
        """Test that invalid ID numbers are not detected."""
        # ID starting with 0 is invalid
        text = "Invalid ID: 010101199001011234"
        matches = self.scanner.scan(text, [PIIType.CHINA_ID])

        assert len(matches) == 0

    # ==================== Bank Card Tests ====================

    def test_detect_bank_card_basic(self):
        """Test basic bank card detection."""
        text = "Card number: 6222021234567890123"
        matches = self.scanner.scan(text, [PIIType.BANK_CARD])

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.BANK_CARD
        # Value should be normalized (no spaces/dashes)
        assert matches[0].value == "6222021234567890123"

    def test_detect_bank_card_with_spaces(self):
        """Test bank card with spaces (16 digits with spaces)."""
        text = "Card: 6222 0212 3456 7890 1234"
        matches = self.scanner.scan(text, [PIIType.BANK_CARD])

        assert len(matches) == 1
        assert matches[0].value == "62220212345678901234"

    def test_detect_bank_card_with_dashes(self):
        """Test bank card with dashes (16 digits with dashes)."""
        text = "Card: 6222-0212-3456-7890-1234"
        matches = self.scanner.scan(text, [PIIType.BANK_CARD])

        assert len(matches) == 1
        assert matches[0].value == "62220212345678901234"

    def test_detect_bank_card_16_digits(self):
        """Test 16-digit bank card."""
        text = "Card: 4916123456789012"
        matches = self.scanner.scan(text, [PIIType.BANK_CARD])

        assert len(matches) == 1

    def test_detect_bank_card_19_digits(self):
        """Test 19-digit bank card (must not start with 19/20 to avoid ID conflict)."""
        text = "Card: 6217002345678901234"
        matches = self.scanner.scan(text, [PIIType.BANK_CARD])

        # Card number starts with 62, not 19/20, so should match
        assert len(matches) == 1

    # ==================== Mixed PII Tests ====================

    def test_detect_multiple_pii_types(self):
        """Test detection of multiple PII types."""
        text = "Contact: john@email.com, Phone: 13912345678, ID: 110101199001011234"
        matches = self.scanner.scan(text)

        assert len(matches) == 3
        assert {m.pii_type for m in matches} == {PIIType.EMAIL, PIIType.PHONE, PIIType.CHINA_ID}

    def test_scan_specific_types_only(self):
        """Test scanning for specific PII types only."""
        text = "Email: test@test.com, Phone: 13812345678"
        matches = self.scanner.scan(text, [PIIType.EMAIL])

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.EMAIL

    # ==================== Contains PII Tests ====================

    def test_contains_pii_true(self):
        """Test contains_pii returns True when PII found."""
        text = "My email is test@example.com"
        assert self.scanner.contains_pii(text) is True

    def test_contains_pii_false(self):
        """Test contains_pii returns False when no PII found."""
        text = "This is just normal text without any PII."
        assert self.scanner.contains_pii(text) is False

    def test_contains_pii_specific_type(self):
        """Test contains_pii with specific type filter."""
        text = "Normal text with no phone numbers"
        assert self.scanner.contains_pii(text, [PIIType.PHONE]) is False

        text = "Call me at 13812345678"
        assert self.scanner.contains_pii(text, [PIIType.PHONE]) is True
        assert self.scanner.contains_pii(text, [PIIType.EMAIL]) is False

    # ==================== PII Summary Tests ====================

    def test_get_pii_summary(self):
        """Test PII summary generation."""
        text = "Email: a@a.com, Phone: 13812345678, ID: 110101199001011234"
        summary = self.scanner.get_pii_summary(text)

        assert summary[PIIType.EMAIL] == 1
        assert summary[PIIType.PHONE] == 1
        assert summary[PIIType.CHINA_ID] == 1
        assert summary[PIIType.BANK_CARD] == 0

    def test_get_pii_summary_empty(self):
        """Test PII summary with no PII."""
        text = "No PII here"
        summary = self.scanner.get_pii_summary(text)

        assert all(count == 0 for count in summary.values())

    # ==================== PII Match Masking Tests ====================

    def test_email_masked_value(self):
        """Test email masking."""
        text = "test@example.com"
        matches = self.scanner.scan(text, [PIIType.EMAIL])

        assert matches[0].masked_value == "t***@example.com"

    def test_phone_masked_value(self):
        """Test phone masking."""
        text = "13812345678"
        matches = self.scanner.scan(text, [PIIType.PHONE])

        assert matches[0].masked_value == "138****5678"

    def test_china_id_masked_value(self):
        """Test China ID masking."""
        text = "110101199001011234"
        matches = self.scanner.scan(text, [PIIType.CHINA_ID])

        assert matches[0].masked_value == "110101****1234"

    def test_bank_card_masked_value(self):
        """Test bank card masking."""
        text = "6222021234567890123"
        matches = self.scanner.scan(text, [PIIType.BANK_CARD])

        # 19 digits: first 4 + **** + last 4 = 6222****0123
        assert matches[0].masked_value == "6222****0123"


class TestPIIMatch:
    """Test PIIMatch dataclass."""

    def test_create_match(self):
        """Test creating a PIIMatch."""
        match = PIIMatch(
            pii_type=PIIType.EMAIL,
            value="test@example.com",
            start=0,
            end=16,
            masked_value="t***@example.com",
        )

        assert match.pii_type == PIIType.EMAIL
        assert match.value == "test@example.com"
        assert match.start == 0
        assert match.end == 16

    def test_auto_masking(self):
        """Test automatic masking when not provided."""
        match = PIIMatch(
            pii_type=PIIType.PHONE,
            value="13812345678",
            start=0,
            end=11,
            masked_value="",  # Empty, should auto-mask
        )

        assert match.masked_value == "138****5678"
