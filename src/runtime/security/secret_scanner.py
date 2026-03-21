"""
敏感信息扫描器

扫描并检测代码中的敏感信息泄露
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SecretType(Enum):
    """敏感信息类型"""

    OPENAI_API_KEY = "openai_api_key"
    ANTHROPIC_API_KEY = "anthropic_api_key"
    AWS_ACCESS_KEY = "aws_access_key"
    AWS_SECRET_KEY = "aws_secret_key"
    GOOGLE_API_KEY = "google_api_key"
    GITHUB_TOKEN = "github_token"
    GENERIC_API_KEY = "generic_api_key"
    PASSWORD = "password"
    PRIVATE_KEY = "private_key"
    DATABASE_URL = "database_url"
    JWT_TOKEN = "jwt_token"
    # PII Types
    CHINA_ID = "china_id"
    PHONE = "phone"
    BANK_CARD = "bank_card"
    EMAIL = "email"


@dataclass
class SecretMatch:
    """敏感信息匹配"""

    type: SecretType
    position: tuple[int, int]
    snippet: str
    redacted: str

    def __str__(self) -> str:
        return f"{self.type.value} at {self.position}: {self.redacted}"


@dataclass
class SecretScanResult:
    """扫描结果"""

    has_secrets: bool
    secrets_found: list[SecretMatch]
    redacted_content: Optional[str] = None

    def __str__(self) -> str:
        if not self.has_secrets:
            return "No secrets found"
        return (
            f"Found {len(self.secrets_found)} secrets: {[s.type.value for s in self.secrets_found]}"
        )


class SecretScanner:
    """敏感信息扫描器

    检测代码中的 API keys、密码、私钥等敏感信息
    """

    # 敏感信息模式
    PATTERNS: dict[SecretType, str] = {
        SecretType.OPENAI_API_KEY: r"sk-[a-zA-Z0-9]{20,}",
        # Anthropic: sk-ant- prefix with flexible length (20+ chars to match real keys)
        SecretType.ANTHROPIC_API_KEY: r"sk-ant-[a-zA-Z0-9_-]{20,}",
        # AWS: flexible matching for both access key and secret key
        SecretType.AWS_ACCESS_KEY: r"(?i)(aws[_-]?)?access[_-]?key[_-]?id?\s*[:=]\s*['\"]?([A-Z0-9]{16,20})['\"]?",
        SecretType.AWS_SECRET_KEY: r"(?i)aws[_-]?secret[_-]?key|aws[_-]?secret|access[_-]?key[_-]?secret\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{20,})['\"]?",
        SecretType.GOOGLE_API_KEY: r"AIza[0-9A-Za-z_-]{35}",
        SecretType.GITHUB_TOKEN: r"gh[pousr]_[A-Za-z0-9_]{20,}",
        SecretType.GENERIC_API_KEY: r"(?i)(api[_-]?key|apikey|secret[_-]?key|client[_-]?secret)\s*[:=]\s*['\"]([a-zA-Z0-9_-]{20,})['\"]",
        SecretType.PASSWORD: r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]([^'\"]{8,})['\"]",
        SecretType.PRIVATE_KEY: r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
        SecretType.DATABASE_URL: r"(?i)(mysql|postgresql|mongodb|redis)://[^'\"]+:[^'\"]+@",
        SecretType.JWT_TOKEN: r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*",
        # PII Patterns
        # Chinese ID card: 18 digits, first digit cannot be 0
        SecretType.CHINA_ID: r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b",
        # Chinese mobile phone: 11 digits, starting with 1
        SecretType.PHONE: r"\b1[3-9]\d{9}\b",
        # Bank card: 16-19 digits
        SecretType.BANK_CARD: r"\b(?:(?![12]\d{5}(?:19|20)\d{2})\d){16,19}\b|\b(?:\d{4}[\s-]){3,4}\d{4}\b",
        # Email address
        SecretType.EMAIL: r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    }

    # 需要熵检测的密钥类型（避免假阳性）
    ENTROPY_REQUIRING_TYPES: set[SecretType] = {
        SecretType.GENERIC_API_KEY,
    }

    # 高风险模式（需要阻止执行）
    HIGH_RISK_TYPES: set[SecretType] = {
        SecretType.PRIVATE_KEY,
        SecretType.AWS_SECRET_KEY,
        SecretType.GITHUB_TOKEN,
    }

    # 最小熵值（比特），高于此值认为是真实密钥
    MIN_ENTROPY = 3.5

    def __init__(self, redact: bool = True):
        """初始化扫描器

        Args:
            redact: 是否自动脱敏
        """
        self.redact = redact
        self._compiled_patterns: dict[SecretType, re.Pattern] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """预编译所有正则表达式"""
        for secret_type, pattern in self.PATTERNS.items():
            self._compiled_patterns[secret_type] = re.compile(pattern)

    def _calculate_entropy(self, text: str) -> float:
        """计算字符串的信息熵（每字符比特数）

        Args:
            text: 待计算的字符串

        Returns:
            信息熵值
        """
        if not text:
            return 0.0

        # 统计字符频率
        freq: dict[str, int] = {}
        for char in text:
            freq[char] = freq.get(char, 0) + 1

        # 计算香农熵
        import math

        entropy = 0.0
        length = len(text)
        for count in freq.values():
            probability = count / length
            entropy -= probability * math.log2(probability)

        return entropy

    def _is_high_entropy(self, text: str) -> bool:
        """检查字符串是否具有足够的信息熵（可能是真实密钥）

        Args:
            text: 待检查的字符串

        Returns:
            是否具有高熵
        """
        entropy = self._calculate_entropy(text)
        return entropy >= self.MIN_ENTROPY

    def scan(self, content: str) -> SecretScanResult:
        """扫描敏感信息

        Args:
            content: 待扫描的内容

        Returns:
            SecretScanResult: 扫描结果
        """
        secrets: list[SecretMatch] = []
        redacted_content = content

        for secret_type, pattern in self._compiled_patterns.items():
            matches = pattern.finditer(content)
            for match in matches:
                # 提取匹配的文本
                matched_text = match.group(0)

                # 对于需要熵检测的类型，验证是否是真实密钥
                if secret_type in self.ENTROPY_REQUIRING_TYPES:
                    # 尝试提取密钥值（假设格式为 key="value" 或 key: value）
                    key_value = matched_text
                    if "=" in matched_text:
                        key_value = matched_text.split("=")[-1].strip().strip("'\"")
                    elif ":" in matched_text:
                        key_value = matched_text.split(":")[-1].strip().strip("'\"")

                    if not self._is_high_entropy(key_value):
                        # 熵值过低，跳过（可能是误报）
                        continue

                # 生成脱敏版本
                redacted = self._redact(matched_text, secret_type)

                # 创建匹配对象
                secret_match = SecretMatch(
                    type=secret_type,
                    position=match.span(),
                    snippet=matched_text[:20] + "..." if len(matched_text) > 20 else matched_text,
                    redacted=redacted,
                )
                secrets.append(secret_match)

                # 替换为脱敏版本
                if self.redact:
                    redacted_content = redacted_content.replace(matched_text, redacted)

        return SecretScanResult(
            has_secrets=len(secrets) > 0,
            secrets_found=secrets,
            redacted_content=redacted_content if self.redact else None,
        )

    def _redact(self, text: str, secret_type: SecretType) -> str:
        """脱敏处理

        Args:
            text: 原始文本
            secret_type: 敏感信息类型

        Returns:
            脱敏后的文本
        """
        if secret_type == SecretType.PRIVATE_KEY:
            return "[PRIVATE_KEY_REDACTED]"

        if secret_type == SecretType.PASSWORD:
            # 保留最后2个字符
            if len(text) > 4:
                return text[:2] + "*" * (len(text) - 4) + text[-2:]
            return "*" * len(text)

        # PII types redaction
        if secret_type == SecretType.EMAIL:
            # Mask email: first char + *** + domain
            if "@" in text:
                parts = text.split("@")
                if len(parts) == 2 and len(parts[0]) > 1:
                    return f"{parts[0][0]}***@{parts[1]}"
            return "***@***"

        if secret_type == SecretType.PHONE:
            # Mask phone: first 3 + **** + last 4
            if len(text) >= 7:
                return f"{text[:3]}****{text[-4:]}"
            return "***-****-****"

        if secret_type == SecretType.CHINA_ID:
            # Mask ID: first 6 + *** + last 4
            if len(text) >= 10:
                return f"{text[:6]}****{text[-4:]}"
            return "**********"

        if secret_type == SecretType.BANK_CARD:
            # Mask bank card: first 4 + **** + last 4
            # Normalize first: remove spaces/dashes
            normalized = text.replace(" ", "").replace("-", "")
            if len(normalized) >= 8:
                return f"{normalized[:4]}****{normalized[-4:]}"
            return "****-****-****-****"

        # 对于 API key，保留前4个字符
        if len(text) > 8:
            prefix = text[:4]
            suffix = text[-4:]
            return f"{prefix}...{suffix}"

        return "[REDACTED]"

    def is_high_risk(self, result: SecretScanResult) -> bool:
        """检查扫描结果是否包含高风险敏感信息

        Args:
            result: 扫描结果

        Returns:
            是否包含高风险信息
        """
        return any(secret.type in self.HIGH_RISK_TYPES for secret in result.secrets_found)


# ========== Convenience Functions ==========


def scan_for_secrets(content: str) -> SecretScanResult:
    """便捷函数：扫描敏感信息"""
    scanner = SecretScanner()
    return scanner.scan(content)


def has_high_risk_secrets(content: str) -> bool:
    """便捷函数：检查是否包含高风险敏感信息"""
    scanner = SecretScanner()
    result = scanner.scan(content)
    return scanner.is_high_risk(result)
