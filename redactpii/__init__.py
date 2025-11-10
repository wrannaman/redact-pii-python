"""Zero-dependency, blazing-fast regex-based PII redaction with optional compliance dashboard integration."""

from redactpii.redactor import Redactor
from redactpii.types import RedactionEvent, RedactorOptions

__version__ = "1.0.0"
__all__ = ["Redactor", "RedactorOptions", "RedactionEvent"]

