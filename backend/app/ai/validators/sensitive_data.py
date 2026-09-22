import re
from dataclasses import dataclass

SENSITIVE_PATTERNS = [
  (r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?\w{8,}", "API key"),
  (r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?\S+", "Password"),
  (r"(?i)(secret|token|bearer)\s*[:=]\s*['\"]?\S{8,}", "Secret/Token"),
  (r"(?i)(aws_access_key_id|aws_secret_access_key)", "AWS credentials"),
  (r"(?i)(postgresql|mysql|mongodb)://\S+:\S+@", "Database connection string"),
  (r"(?i)sk-[a-zA-Z0-9]{20,}", "OpenAI API key"),
  (r"\b\d{3}-\d{2}-\d{4}\b", "SSN pattern"),
  (r"(?i)(BEGIN (RSA |OPENSSH )?PRIVATE KEY)", "Private key"),
]


@dataclass
class ScanResult:
    has_sensitive: bool
    findings: list[str]
    redacted_text: str


def scan_sensitive_data(text: str) -> ScanResult:
    findings: list[str] = []
    redacted = text
    for pattern, label in SENSITIVE_PATTERNS:
        if re.search(pattern, text):
            findings.append(label)
            redacted = re.sub(pattern, f"[REDACTED_{label.upper().replace(' ', '_')}]", redacted)
    return ScanResult(has_sensitive=bool(findings), findings=findings, redacted_text=redacted)
