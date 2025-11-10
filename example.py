#!/usr/bin/env python3
"""Example usage of the redactpii package."""

from redactpii import Redactor

# Basic usage
print("=== Basic Usage ===")
redactor = Redactor()
text = "Hi David Johnson, call 555-555-5555 or email david@example.com"
clean = redactor.redact(text)
print(f"Original: {text}")
print(f"Redacted: {clean}")
print()

# Check for PII without redacting
print("=== Check for PII ===")
if redactor.has_pii("Contact test@example.com for details"):
    print("PII detected!")
    clean = redactor.redact("Contact test@example.com for details")
    print(f"Redacted: {clean}")
print()

# Redact objects
print("=== Redact Objects ===")
redactor = Redactor({"rules": {"EMAIL": True}})
user = {
    "name": "John Doe",
    "email": "john@example.com",
    "profile": {
        "contact": "contact@example.com",
    },
}
clean = redactor.redact_object(user)
print(f"Original: {user}")
print(f"Redacted: {clean}")
print()

# Custom rules
print("=== Custom Rules ===")
import re
redactor = Redactor({
    "rules": {"EMAIL": True},
    "custom_rules": [re.compile(r"\b\d{5}\b")],  # 5-digit codes
})
result = redactor.redact("Email: test@example.com, Code: 12345")
print(f"Result: {result}")
print()

# Global replacement
print("=== Global Replacement ===")
redactor = Redactor({
    "rules": {"EMAIL": True},
    "global_replace_with": "[REDACTED]",
})
result = redactor.redact("test@example.com")
print(f"Result: {result}")

