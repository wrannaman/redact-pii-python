"""Comprehensive tests for the Redactor class."""

import re
import json
import unittest.mock
from unittest.mock import patch, MagicMock
import urllib.request
import urllib.error

import pytest

from redactpii import Redactor


class TestRedactor:
    """Test suite for the Redactor class."""

    def test_redact_email(self):
        """Test redacting email addresses."""
        redactor = Redactor({"rules": {"EMAIL": True}})
        result = redactor.redact("test@example.com")
        assert "EMAIL" in result
        result = redactor.redact("Contact test@example.com for details")
        assert "EMAIL" in result

    def test_redact_credit_card(self):
        """Test redacting credit cards."""
        redactor = Redactor({"rules": {"CREDIT_CARD": True}})
        result = redactor.redact("1234-5678-9012-3456")
        assert "CREDIT" in result
        result = redactor.redact("Card: 1234 5678 9012 3456")
        assert "CREDIT" in result

    def test_redact_ssn(self):
        """Test redacting SSN."""
        redactor = Redactor({"rules": {"SSN": True}})
        result = redactor.redact("123-45-6789")
        assert "SOCIAL" in result
        result = redactor.redact("SSN: 123.45.6789")
        assert "SOCIAL" in result

    def test_redact_phone(self):
        """Test redacting phone numbers."""
        redactor = Redactor({"rules": {"PHONE": True}})
        result = redactor.redact("555-123-4567")
        assert "PHONE" in result
        result = redactor.redact("Call (555) 123-4567")
        assert "PHONE" in result

    def test_redact_name(self):
        """Test redacting names."""
        redactor = Redactor({"rules": {"NAME": True}})
        result = redactor.redact("Hi John Smith, how are you?")
        assert "PERSON_NAME" in result
        result = redactor.redact("Dear Jane Doe,")
        assert "PERSON_NAME" in result

    def test_redact_multiple_pii_types(self):
        """Test redacting multiple PII types."""
        redactor = Redactor({"rules": {"EMAIL": True, "PHONE": True, "SSN": True}})
        result = redactor.redact("Email: test@example.com, Phone: 555-123-4567, SSN: 123-45-6789")
        assert "EMAIL" in result
        assert "PHONE" in result
        assert "SOCIAL" in result

    def test_global_replace_with(self):
        """Test using globalReplaceWith when provided."""
        redactor = Redactor({"rules": {"EMAIL": True}, "global_replace_with": "[REDACTED]"})
        assert redactor.redact("test@example.com") == "[REDACTED]"

    def test_disabled_rules(self):
        """Test that disabled rules don't redact."""
        redactor = Redactor({"rules": {"EMAIL": False}})
        assert redactor.redact("test@example.com") == "test@example.com"

    def test_empty_string(self):
        """Test handling empty string."""
        redactor = Redactor()
        assert redactor.redact("") == ""

    def test_no_pii(self):
        """Test handling text with no PII."""
        redactor = Redactor()
        text = "This is plain text with no sensitive information"
        assert redactor.redact(text) == text

    def test_has_pii_true(self):
        """Test has_pii returns true when PII is present."""
        redactor = Redactor({"rules": {"EMAIL": True}})
        assert redactor.has_pii("test@example.com") is True
        assert redactor.has_pii("Contact test@example.com for details") is True

    def test_has_pii_false(self):
        """Test has_pii returns false when no PII is present."""
        redactor = Redactor({"rules": {"EMAIL": True}})
        assert redactor.has_pii("This is plain text") is False
        assert redactor.has_pii("") is False

    def test_has_pii_multiple_types(self):
        """Test has_pii detects multiple PII types."""
        redactor = Redactor({"rules": {"EMAIL": True, "PHONE": True, "SSN": True}})
        assert redactor.has_pii("test@example.com") is True
        assert redactor.has_pii("555-123-4567") is True
        assert redactor.has_pii("123-45-6789") is True

    def test_has_pii_respects_disabled_rules(self):
        """Test has_pii respects disabled rules."""
        redactor = Redactor({"rules": {"EMAIL": False}})
        assert redactor.has_pii("test@example.com") is False

    def test_redact_object_strings(self):
        """Test redacting strings in objects."""
        redactor = Redactor({"rules": {"EMAIL": True}})
        input_obj = {"email": "test@example.com", "name": "John"}
        result = redactor.redact_object(input_obj)

        assert "EMAIL" in result["email"]
        assert result["name"] == "John"

    def test_redact_object_nested(self):
        """Test redacting strings in nested objects."""
        redactor = Redactor({"rules": {"EMAIL": True}})
        input_obj = {
            "user": {
                "email": "test@example.com",
                "profile": {
                    "contact": "test2@example.com",
                },
            },
        }
        result = redactor.redact_object(input_obj)

        assert "EMAIL" in result["user"]["email"]
        assert "EMAIL" in result["user"]["profile"]["contact"]

    def test_redact_object_arrays(self):
        """Test redacting strings in arrays."""
        redactor = Redactor({"rules": {"EMAIL": True}})
        input_obj = {"emails": ["test1@example.com", "test2@example.com"]}
        result = redactor.redact_object(input_obj)

        assert "EMAIL" in result["emails"][0]
        assert "EMAIL" in result["emails"][1]

    def test_redact_object_immutability(self):
        """Test that redact_object doesn't mutate original object."""
        redactor = Redactor({"rules": {"EMAIL": True}})
        input_obj = {"email": "test@example.com"}
        result = redactor.redact_object(input_obj)

        assert input_obj["email"] == "test@example.com"
        assert "EMAIL" in result["email"]

    def test_redact_object_null_undefined(self):
        """Test handling null and undefined values."""
        redactor = Redactor({"rules": {"EMAIL": True}})
        input_obj = {
            "email": "test@example.com",
            "null_value": None,
        }
        result = redactor.redact_object(input_obj)

        assert "EMAIL" in result["email"]
        assert result["null_value"] is None

    def test_redact_object_empty(self):
        """Test handling empty objects and arrays."""
        redactor = Redactor()
        assert redactor.redact_object({}) == {}
        assert redactor.redact_object({"items": []}) == {"items": []}

    @patch("urllib.request.urlopen")
    def test_dashboard_hook_with_api_key(self, mock_urlopen):
        """Test sending events to dashboard when api_key is provided."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        redactor = Redactor({"api_key": "test-key", "rules": {"EMAIL": True}})
        redactor.redact("test@example.com")

        # Wait a bit for the thread to execute
        import time
        time.sleep(0.1)

        assert mock_urlopen.called
        call_args = mock_urlopen.call_args
        assert call_args is not None

        # Check the request
        request = call_args[0][0]
        assert isinstance(request, urllib.request.Request)
        assert request.get_full_url() == "https://api.redactpii.com/v1/events"
        assert request.get_method() == "POST"

        # Check headers (urllib.request.Request normalizes header names)
        # Convert headers to dict for easier inspection
        headers_dict = dict(request.headers)
        # urllib normalizes headers - check for Authorization (case-insensitive)
        auth_key = next((k for k in headers_dict.keys() if k.lower() == "authorization"), None)
        assert auth_key is not None, f"Authorization header not found. Headers: {headers_dict}"
        assert headers_dict[auth_key] == "Bearer test-key"
        # Content-Type header (urllib stores as "Content-type")
        content_type_key = next((k for k in headers_dict.keys() if k.lower() == "content-type"), None)
        assert content_type_key is not None, f"Content-Type header not found. Headers: {headers_dict}"
        assert headers_dict[content_type_key] == "application/json"

        # Check body
        body_data = request.data
        assert body_data is not None
        payload = json.loads(body_data.decode("utf-8"))
        assert "events" in payload
        assert isinstance(payload["events"], list)
        assert len(payload["events"]) > 0
        assert payload["events"][0]["pii_type"] == "EMAIL"
        assert payload["events"][0]["action"] == "REDACTED"
        assert payload["sdk_version"] == "1.0.0"
        assert payload["sdk_language"] == "python"

    @patch("urllib.request.urlopen")
    def test_dashboard_hook_no_api_key(self, mock_urlopen):
        """Test that events are not sent when api_key is not provided."""
        redactor = Redactor({"rules": {"EMAIL": True}})
        redactor.redact("test@example.com")

        import time
        time.sleep(0.1)

        assert not mock_urlopen.called

    @patch("urllib.request.urlopen")
    def test_dashboard_hook_no_pii(self, mock_urlopen):
        """Test that events are not sent when no PII is redacted."""
        redactor = Redactor({"api_key": "test-key", "rules": {"EMAIL": True}})
        redactor.redact("This is plain text")

        import time
        time.sleep(0.1)

        assert not mock_urlopen.called

    @patch("urllib.request.urlopen")
    def test_dashboard_hook_custom_url(self, mock_urlopen):
        """Test using custom api_url when provided."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        redactor = Redactor({
            "api_key": "test-key",
            "api_url": "https://custom-api.example.com/events",
            "rules": {"EMAIL": True},
        })
        redactor.redact("test@example.com")

        import time
        time.sleep(0.1)

        assert mock_urlopen.called
        call_args = mock_urlopen.call_args
        assert call_args is not None
        request = call_args[0][0]
        assert request.get_full_url() == "https://custom-api.example.com/events"

    @patch("urllib.request.urlopen")
    def test_dashboard_hook_fail_silent(self, mock_urlopen):
        """Test that dashboard hook fails silently by default."""
        mock_urlopen.side_effect = Exception("Network error")

        redactor = Redactor({"api_key": "test-key", "rules": {"EMAIL": True}})

        # Should not throw
        redactor.redact("test@example.com")

        import time
        time.sleep(0.1)

        assert mock_urlopen.called

    def test_custom_rules(self):
        """Test applying custom regex rules."""
        redactor = Redactor({
            "rules": {},
            "custom_rules": [re.compile(r"\b\d{5}\b")],  # 5-digit numbers
        })

        result = redactor.redact("My code is 12345")
        assert "DIGITS" in result

    def test_combine_builtin_and_custom_rules(self):
        """Test combining built-in and custom rules."""
        redactor = Redactor({
            "rules": {"EMAIL": True},
            "custom_rules": [re.compile(r"\b\d{5}\b")],
        })

        result = redactor.redact("Email: test@example.com, Code: 12345")
        assert "EMAIL" in result
        assert "DIGITS" in result

    def test_pii_at_start(self):
        """Test handling PII at start of string."""
        redactor = Redactor({"rules": {"EMAIL": True}})
        result = redactor.redact("test@example.com is my email")
        assert "EMAIL" in result

    def test_pii_at_end(self):
        """Test handling PII at end of string."""
        redactor = Redactor({"rules": {"EMAIL": True}})
        result = redactor.redact("My email is test@example.com")
        assert "EMAIL" in result

    def test_multiple_pii_instances(self):
        """Test handling multiple PII instances."""
        redactor = Redactor({"rules": {"EMAIL": True}})
        result = redactor.redact("test1@example.com and test2@example.com")
        assert result.count("EMAIL") >= 2

    def test_pii_with_special_characters(self):
        """Test handling PII with special characters."""
        redactor = Redactor({"rules": {"EMAIL": True}})
        result = redactor.redact("Contact test+tag@example.com")
        assert "EMAIL" in result

    def test_whitespace_only_strings(self):
        """Test handling whitespace-only strings."""
        redactor = Redactor()
        assert redactor.redact("   ") == "   "
        assert redactor.redact("\n\n") == "\n\n"

