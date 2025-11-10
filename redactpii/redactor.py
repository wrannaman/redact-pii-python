"""Main Redactor class that provides PII redaction with optional dashboard integration."""

import json
import re
from typing import Any, Dict, List, Optional, Pattern, Tuple
import threading
import urllib.request
import urllib.error


class Redactor:
    """
    Main Redactor class that provides PII redaction with optional dashboard integration.
    Zero dependencies, blazing fast regex-based redaction.
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the Redactor with configuration options.

        Args:
            options: Configuration dictionary with the following optional keys:
                - api_key: API key for dashboard integration
                - api_url: Custom API URL (defaults to https://api.redactpii.com/v1/events)
                - fail_silent: Whether to fail silently on dashboard errors (default: True)
                - hook_timeout: Timeout for dashboard requests in milliseconds (default: 500)
                - rules: Dictionary mapping rule names to enabled/disabled (default: all enabled)
                - custom_rules: List of custom regex patterns
                - global_replace_with: Global replacement string for all PII types
        """
        if options is None:
            options = {}

        self.api_key: Optional[str] = options.get("api_key")
        self.api_url: str = options.get("api_url", "https://api.redactpii.com/v1/events")
        self.fail_silent: bool = options.get("fail_silent", True)
        self.hook_timeout: int = options.get("hook_timeout", 500)
        self.global_replace_with: Optional[str] = options.get("global_replace_with")

        # Build active rule set - all rules enabled by default
        default_rules = {
            "CREDIT_CARD": True,
            "EMAIL": True,
            "NAME": True,
            "PHONE": True,
            "SSN": True,
        }
        rules = options.get("rules", default_rules)
        custom_rules = options.get("custom_rules", [])
        self.active_rules: List[Tuple[Pattern[str], str]] = self._build_rule_set(rules, custom_rules)

    def _build_rule_set(
        self, rules: Dict[str, bool], custom_rules: List[Pattern[str]]
    ) -> List[Tuple[Pattern[str], str]]:
        """
        Build active rule set from simplified configuration.

        Args:
            rules: Dictionary mapping rule names to enabled/disabled
            custom_rules: List of custom regex patterns

        Returns:
            List of tuples containing (pattern, name) for active rules
        """
        rule_patterns: Dict[str, Tuple[Pattern[str], str]] = {
            "CREDIT_CARD": (
                re.compile(r"\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}|\d{4}[ -]?\d{6}[ -]?\d{4}\d?"),
                "CREDIT_CARD",
            ),
            "EMAIL": (re.compile(r"([a-z0-9_\-.+]+)@\w+(\.\w+)*", re.IGNORECASE), "EMAIL"),
            "NAME": (
                re.compile(
                    r"(?:^|\.\s+)(?:dear|hi|hello|greetings|hey|hey there)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
                    re.IGNORECASE,
                ),
                "PERSON_NAME",
            ),
            "PHONE": (
                re.compile(
                    r"(\(?\+?[0-9]{1,2}\)?[-. ]?)?(\(?[0-9]{3}\)?[-. ]?[0-9]{3,4}[-. ]?[0-9]{4}|[0-9]{3}[-. ]?[0-9]{4}|[0-9]{4}[-. ]?[0-9]{4}|\b[A-Z0-9]{7}\b)"
                ),
                "PHONE_NUMBER",
            ),
            "SSN": (re.compile(r"\b\d{3}[ -.]\d{2}[ -.]\d{4}\b"), "US_SOCIAL_SECURITY_NUMBER"),
        }

        active_rules: List[Tuple[Pattern[str], str]] = []

        # Add enabled built-in rules
        for rule_name, enabled in rules.items():
            if enabled is True and rule_name in rule_patterns:
                active_rules.append(rule_patterns[rule_name])

        # Add custom rules (use DIGITS as default name)
        for custom_rule in custom_rules:
            active_rules.append((custom_rule, "DIGITS"))

        return active_rules

    def has_pii(self, text: str) -> bool:
        """
        Check if text contains any PII patterns without redacting.

        Args:
            text: The text to check for PII

        Returns:
            True if PII is detected, False otherwise
        """
        for pattern, _ in self.active_rules:
            if pattern.search(text):
                return True
        return False

    def redact_object(self, obj: Any) -> Any:
        """
        Redact PII from JSON objects recursively.

        Args:
            obj: The object to redact (dict, list, or primitive)

        Returns:
            A deep copy of the object with PII redacted
        """
        # Deep clone using JSON serialization
        redacted = json.loads(json.dumps(obj))

        def process_value(value: Any) -> Any:
            if isinstance(value, str):
                return self.redact(value)
            if isinstance(value, list):
                return [process_value(item) for item in value]
            if isinstance(value, dict):
                return {key: process_value(val) for key, val in value.items()}
            return value

        return process_value(redacted)

    def redact(self, text: str) -> str:
        """
        Redact PII from the input text using regex-based patterns.
        If an api_key is configured, asynchronously sends metadata to the dashboard.

        Args:
            text: The text to redact

        Returns:
            The redacted text with PII replaced
        """
        events: List[Dict[str, str]] = []
        redacted_text = text

        # Apply each rule and collect events during redaction
        for pattern, name in self.active_rules:
            def make_replacement_func(pii_name: str) -> Any:
                def replacement_func(match: re.Match[str]) -> str:
                    pii_type = pii_name
                    events.append({"pii_type": pii_type, "action": "REDACTED"})

                    # Use global_replace_with if provided, otherwise use type-specific replacements
                    if self.global_replace_with is not None:
                        return self.global_replace_with
                    return self._get_replacement(pii_type)

                return replacement_func

            redacted_text = pattern.sub(make_replacement_func(name), redacted_text)

        # Send events to dashboard if configured
        has_valid_api_key = self.api_key is not None and self.api_key != ""
        if has_valid_api_key and events:
            # Fire and forget - run in background thread
            thread = threading.Thread(target=self._phone_home, args=(events,), daemon=True)
            thread.start()

        return redacted_text

    def _get_replacement(self, pii_type: str) -> str:
        """
        Get the replacement string for a given PII type.

        Args:
            pii_type: The type of PII detected

        Returns:
            The replacement string
        """
        replacements = {
            "CREDIT_CARD": "CREDIT_CARD_NUMBER",
            "EMAIL": "EMAIL_ADDRESS",
            "PERSON_NAME": "PERSON_NAME",
            "PHONE_NUMBER": "PHONE_NUMBER",
            "US_SOCIAL_SECURITY_NUMBER": "US_SOCIAL_SECURITY_NUMBER",
        }
        return replacements.get(pii_type, "DIGITS")

    def _phone_home(self, events: List[Dict[str, str]]) -> None:
        """
        Spec-compliant dashboard hook - sends redaction events to dashboard.

        Args:
            events: List of redaction events to send
        """
        if not self.api_key or self.api_key == "":
            return

        try:
            payload = {
                "sdk_version": "1.0.0",
                "sdk_language": "python",
                "events": events,
            }

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.api_url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )

            # Use timeout (convert from milliseconds to seconds)
            timeout_seconds = self.hook_timeout / 1000.0
            with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
                if response.status >= 400:
                    raise Exception(f"Dashboard API returned {response.status}")

        except Exception as error:
            if not self.fail_silent:
                raise error
            # Fail silently by default

