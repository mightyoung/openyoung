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
        text = "Phones: 13456789012, 14712345678, 19812345678"
        matches = self.scanner.scan(text, [PIIType.PHONE])
        # All valid 11-digit mobile phones should be detected
        assert len(matches) == 3

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

    # ==================== China Passport Tests ====================

    def test_detect_china_passport(self):
        """Test Chinese passport detection."""
        text = "Passport: G12345678"
        matches = self.scanner.scan(text, [PIIType.CHINA_PASSPORT])

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.CHINA_PASSPORT
        assert matches[0].value == "G12345678"

    def test_detect_china_passport_E(self):
        """Test Chinese passport with E prefix."""
        text = "Passport: E87654321"
        matches = self.scanner.scan(text, [PIIType.CHINA_PASSPORT])

        assert len(matches) == 1
        assert matches[0].value == "E87654321"

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

    # ==================== Luhn Validation Tests ====================

    def test_luhn_valid_card(self):
        """Test Luhn validation with a valid card number."""
        # A known valid test card number
        valid_card = "4532015112830366"
        matches = self.scanner.scan(valid_card, [PIIType.BANK_CARD])

        assert len(matches) == 1
        assert matches[0].is_valid is True

    def test_luhn_invalid_card(self):
        """Test Luhn validation with an invalid card number."""
        # Invalid card number (changed last digit)
        invalid_card = "4532015112830367"
        matches = self.scanner.scan(invalid_card, [PIIType.BANK_CARD])

        assert len(matches) == 1
        assert matches[0].is_valid is False

    def test_luhn_disabled_validation(self):
        """Test bank card detection with Luhn validation disabled."""
        scanner_no_luhn = PIIScanner(validate_bank_cards=False)
        invalid_card = "4532015112830367"
        matches = scanner_no_luhn.scan(invalid_card, [PIIType.BANK_CARD])

        assert len(matches) == 1
        # When validation is disabled, is_valid should be True (not validated)
        assert matches[0].is_valid is True

    def test_luhn_too_short(self):
        """Test Luhn validation rejects too-short numbers."""
        short_card = "123456789012"
        matches = self.scanner.scan(short_card, [PIIType.BANK_CARD])

        assert len(matches) == 0  # Should not match at all

    def test_luhn_too_long(self):
        """Test Luhn validation rejects too-long numbers."""
        long_card = "12345678901234567890"
        matches = self.scanner.scan(long_card, [PIIType.BANK_CARD])

        assert len(matches) == 0  # Should not match at all

    # ==================== US SSN Tests ====================

    def test_detect_us_ssn_dashed(self):
        """Test US SSN with dashes detection."""
        text = "SSN: 123-45-6789"
        matches = self.scanner.scan(text, [PIIType.US_SSN])

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.US_SSN
        assert matches[0].value == "123-45-6789"

    def test_detect_us_ssn_no_dashes(self):
        """Test US SSN without dashes detection."""
        text = "SSN: 123456789"
        matches = self.scanner.scan(text, [PIIType.US_SSN])

        assert len(matches) == 1
        assert matches[0].value == "123456789"

    def test_us_ssn_masking(self):
        """Test SSN masking."""
        text = "SSN: 123-45-6789"
        matches = self.scanner.scan(text, [PIIType.US_SSN])

        assert matches[0].masked_value == "123***6789"

    # ==================== UK NIN Tests ====================

    def test_detect_uk_nin(self):
        """Test UK National Insurance Number detection."""
        text = "NIN: QQ 12 34 56 C"
        matches = self.scanner.scan(text, [PIIType.UK_NIN])

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.UK_NIN
        assert matches[0].value == "QQ 12 34 56 C"

    def test_detect_uk_nin_no_spaces(self):
        """Test UK NIN without spaces detection."""
        text = "NIN: QQ123456C"
        matches = self.scanner.scan(text, [PIIType.UK_NIN])

        assert len(matches) == 1

    def test_uk_nin_masking(self):
        """Test UK NIN masking."""
        text = "NIN: QQ 12 34 56 C"
        matches = self.scanner.scan(text, [PIIType.UK_NIN])

        assert matches[0].masked_value == "QQ***56 C"

    # ==================== EU National ID Tests ====================

    def test_detect_eu_german_id(self):
        """Test German ID detection."""
        text = "ID: 123456789A"
        matches = self.scanner.scan(text, [PIIType.EU_NATIONAL_ID])

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.EU_NATIONAL_ID

    def test_detect_eu_french_id(self):
        """Test French ID detection."""
        text = "ID: AB123456CD"
        matches = self.scanner.scan(text, [PIIType.EU_NATIONAL_ID])

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.EU_NATIONAL_ID

    def test_detect_eu_italy_id(self):
        """Test Italian ID detection."""
        text = "ID: CA1234567B"
        matches = self.scanner.scan(text, [PIIType.EU_NATIONAL_ID])

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.EU_NATIONAL_ID

    def test_detect_eu_spain_dni(self):
        """Test Spanish DNI detection."""
        text = "DNI: A12345678B"
        matches = self.scanner.scan(text, [PIIType.EU_NATIONAL_ID])

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.EU_NATIONAL_ID

    def test_eu_id_masking(self):
        """Test EU ID masking."""
        text = "ID: AB123456CD"
        matches = self.scanner.scan(text, [PIIType.EU_NATIONAL_ID])

        assert matches[0].masked_value == "AB****6CD"

    # ==================== Passport Tests ====================

    def test_detect_passport(self):
        """Test general passport detection."""
        text = "Passport: A1234567"
        matches = self.scanner.scan(text, [PIIType.PASSPORT])

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.PASSPORT

    def test_passport_masking(self):
        """Test passport masking."""
        text = "Passport: A12345678"
        matches = self.scanner.scan(text, [PIIType.PASSPORT])

        assert matches[0].masked_value == "A12****78"

    # ==================== IP Address Tests ====================

    def test_detect_ip_address(self):
        """Test IP address detection."""
        text = "Server IP: 192.168.1.1"
        matches = self.scanner.scan(text, [PIIType.IP_ADDRESS])

        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.IP_ADDRESS
        assert matches[0].value == "192.168.1.1"

    def test_detect_ip_address_public(self):
        """Test public IP address detection."""
        text = "Public IP: 8.8.8.8"
        matches = self.scanner.scan(text, [PIIType.IP_ADDRESS])

        assert len(matches) == 1
        assert matches[0].value == "8.8.8.8"

    def test_ip_address_masking(self):
        """Test IP address masking."""
        text = "IP: 192.168.1.100"
        matches = self.scanner.scan(text, [PIIType.IP_ADDRESS])

        assert matches[0].masked_value == "192.168.1.***"

    # ==================== Mixed PII Tests ====================

    def test_detect_multiple_pii_types(self):
        """Test detection of multiple PII types."""
        text = "Contact: john@email.com, Phone: 13912345678, ID: 110101199001011234"
        matches = self.scanner.scan(text)

        assert len(matches) == 3
        assert {m.pii_type for m in matches} == {PIIType.EMAIL, PIIType.PHONE, PIIType.CHINA_ID}

    def test_detect_international_pii(self):
        """Test detection of international PII types."""
        text = "SSN: 123-45-6789, NIN: QQ 12 34 56 C, ID: AB123456CD"
        matches = self.scanner.scan(text)

        assert len(matches) == 3
        assert {m.pii_type for m in matches} == {PIIType.US_SSN, PIIType.UK_NIN, PIIType.EU_NATIONAL_ID}

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

    def test_china_passport_masked_value(self):
        """Test China passport masking."""
        text = "G12345678"
        matches = self.scanner.scan(text, [PIIType.CHINA_PASSPORT])

        assert matches[0].masked_value == "G1****78"


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
        assert match.is_valid is True

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

    def test_match_with_invalid_flag(self):
        """Test creating a PIIMatch with invalid flag."""
        match = PIIMatch(
            pii_type=PIIType.BANK_CARD,
            value="4532015112830367",  # Invalid Luhn
            start=0,
            end=16,
            masked_value="4532****0367",
            is_valid=False,
        )

        assert match.is_valid is False


class TestLuhnAlgorithm:
    """Test the Luhn algorithm implementation."""

    def setup_method(self):
        """Set up test scanner."""
        self.scanner = PIIScanner()

    def test_luhn_valid_numbers(self):
        """Test known valid card numbers."""
        valid_cards = [
            "4532015112830366",  # Visa
            "5425233430109903",  # MasterCard
            "374245455400126",   # American Express
            "6011000991001201",  # Discover
        ]
        for card in valid_cards:
            assert self.scanner._validate_luhn(card) is True, f"Card {card} should be valid"

    def test_luhn_invalid_numbers(self):
        """Test known invalid card numbers."""
        invalid_cards = [
            "4532015112830367",  # Wrong checksum
            "1234567890123456",  # Random
            "1111111111111111",  # All ones (fails Luhn)
        ]
        for card in invalid_cards:
            assert self.scanner._validate_luhn(card) is False, f"Card {card} should be invalid"

    def test_luhn_non_digits(self):
        """Test that non-digit strings return False."""
        assert self.scanner._validate_luhn("abcd1234567890") is False
        assert self.scanner._validate_luhn("1234-5678-9012-3456") is False  # Has dashes

    def test_luhn_edge_cases(self):
        """Test edge cases for Luhn validation."""
        # Too short
        assert self.scanner._validate_luhn("123456789012") is False
        # Too long
        assert self.scanner._validate_luhn("12345678901234567890") is False
        # Empty
        assert self.scanner._validate_luhn("") is False
