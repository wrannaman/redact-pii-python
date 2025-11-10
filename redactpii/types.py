"""Type definitions for the redactpii package."""

from typing import Any, Dict, List, Optional, Pattern, TypedDict


class RedactionEvent(TypedDict):
    """Redaction event structure for dashboard hook."""

    pii_type: str
    action: str  # Always 'REDACTED'


class RedactorOptions(TypedDict, total=False):
    """Configuration options for the Redactor class."""

    # Dashboard integration
    api_key: Optional[str]
    api_url: Optional[str]
    fail_silent: Optional[bool]
    hook_timeout: Optional[int]

    # Rule configuration
    rules: Optional[Dict[str, bool]]

    # Custom regex rules
    custom_rules: Optional[List[Pattern[str]]]

    # Global replacement string (optional)
    global_replace_with: Optional[str]

