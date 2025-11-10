# redactpii

[![PyPI Package](https://img.shields.io/pypi/v/redactpii.svg)](https://pypi.org/project/redactpii/)

> **⚡ Zero-dependency, blazing-fast regex-based PII redaction with optional compliance dashboard integration.**

**Python package for [redactpii.com](https://redactpii.com)** - Protect PII before it hits AI APIs with optional SOC 2/HIPAA audit trails.

Built for the modern AI stack. Protect PII **before** it hits OpenAI, Anthropic, or LangChain with **optional dashboard integration** for SOC 2 & HIPAA audit trails.

## ⚡ Zero Dependencies. Blazing Fast. Enterprise Ready.

- **<1ms per operation** - Optimized regex engine
- **Zero external dependencies** - Pure Python, no bloat
- **Dashboard integration** - SOC 2/HIPAA audit trails (optional)
- **Zero-trust security** - Never sends PII, only metadata
- **Type hints** - Full type safety and IDE support

### Requirements

- **Python 3.8+**
- **Zero dependencies** (seriously, check your requirements)

## 🚀 Installation & Usage

```bash
pip install redactpii
```

### 🔥 Basic Usage

```python
from redactpii import Redactor

redactor = Redactor()
clean = redactor.redact('Hi David Johnson, call 555-555-5555')

# Result: "Hi PERSON_NAME, call PHONE_NUMBER"
```

### 🛡️ Enterprise Compliance (SOC 2/HIPAA Ready)

Enable **optional dashboard integration** for audit trails:

```python
from redactpii import Redactor
import os

redactor = Redactor({
    'api_key': os.getenv('REDACTPII_API_KEY'),  # Enables compliance dashboard
    'api_url': 'https://api.redactpii.com/v1/events',  # Your audit endpoint (optional)
    'rules': {
        'CREDIT_CARD': True,
        'EMAIL': True,
        'NAME': True,
        'PHONE': True,
        'SSN': True,
    },
})

clean = redactor.redact('CEO john@acme.com called from 555-123-4567 with SSN 123-45-6789')

# Result: "CEO EMAIL_ADDRESS called from PHONE_NUMBER with SSN US_SOCIAL_SECURITY_NUMBER"

# 🔒 Zero-trust: Only metadata sent to dashboard
# 📊 Audit log: {"sdk_version": "1.0.0", "pii_type": "EMAIL", "action": "REDACTED"}
```

> **🔐 Zero-Trust Guarantee**: Never sends actual PII data. Only anonymized metadata for compliance reporting. Non-blocking requests with 500ms timeout - never impacts your app performance.

### 🎯 PII Detection

Built-in patterns for:

- **👤 Names** - Person identification (greeting-based detection)
- **📧 Emails** - Email addresses
- **📞 Phones** - US phone numbers (all formats)
- **💳 Credit Cards** - Visa, Mastercard, Amex, Diners Club
- **🆔 SSN** - US Social Security Numbers

### 🔍 Check for PII Without Redacting

```python
from redactpii import Redactor

redactor = Redactor({'rules': {'EMAIL': True}})

if redactor.has_pii('Contact test@example.com for details'):
    print('PII detected!')
    # Now redact it
    clean = redactor.redact('Contact test@example.com for details')
```

### 📦 Redact Objects

```python
from redactpii import Redactor

redactor = Redactor({'rules': {'EMAIL': True}})

user = {
    'name': 'John Doe',
    'email': 'john@example.com',
    'profile': {
        'contact': 'contact@example.com',
    },
}

clean = redactor.redact_object(user)
# {
#   'name': 'John Doe',
#   'email': 'EMAIL_ADDRESS',
#   'profile': {
#     'contact': 'EMAIL_ADDRESS',
#   },
# }
```

### 🤖 Using with LLMs (OpenAI, LangChain)

Protect PII **before** it hits AI APIs. This is your compliance safety net.

<details>
<summary><b>Example: Using with OpenAI Client</b></summary>

```python
from redactpii import Redactor
from openai import OpenAI
import os

redactor = Redactor({
    'api_key': os.getenv('REDACTPII_API_KEY'),
    'rules': {'SSN': True, 'EMAIL': True},
})

openai_client = OpenAI()

# 1. Redact the prompt BEFORE you send it
raw_prompt = 'My SSN is 123-45-6789 and my email is test@example.com'
safe_prompt = redactor.redact(raw_prompt)

# 2. Send the "safe" prompt to the LLM
completion = openai_client.chat.completions.create(
    messages=[{'role': 'user', 'content': safe_prompt}],
    model='gpt-4o',
)

# 3. Your audit log on redactpii.com now has proof
#    of the redaction *before* it hit OpenAI.
```

</details>

<details>
<summary><b>Example: Using with LangChain</b></summary>

```python
from redactpii import Redactor
from langchain_openai import ChatOpenAI
import os

# 1. Init the redactor with your dashboard API key
redactor = Redactor({'api_key': os.getenv('REDACTPII_API_KEY')})
model = ChatOpenAI()

# 2. Create a middleware function to redact input
def redacting_middleware(input_data):
    if redactor.has_pii(input_data['query']):
        # Redact the input and log it to your dashboard
        safe_query = redactor.redact(input_data['query'])
        return {**input_data, 'query': safe_query}
    return input_data

# 3. Use the middleware before sending to LLM
user_input = {'query': 'My email is john@acme.com'}
safe_input = redacting_middleware(user_input)
result = model.invoke(safe_input['query'])

# Your prompt was safely redacted before hitting the LLM.
```

</details>

### 🎨 Customization

#### Configure Rules

```python
redactor = Redactor({
    'rules': {
        'CREDIT_CARD': True,  # Enable credit card detection
        'EMAIL': True,  # Enable email detection
        'NAME': False,  # Disable name detection
        'PHONE': True,  # Enable phone detection
        'SSN': False,  # Disable SSN detection
    },
})
```

#### Custom Regex Patterns

```python
import re
from redactpii import Redactor

redactor = Redactor({
    'rules': {'EMAIL': True},
    'custom_rules': [
        re.compile(r'\b\d{5}\b'),  # 5-digit codes
        re.compile(r'\bSECRET-\d+\b'),  # Secret codes
    ],
})
```

#### Global Replacement

```python
redactor = Redactor({
    'rules': {'EMAIL': True},
    'global_replace_with': '[REDACTED]',  # All PII types use this replacement
})

redactor.redact('test@example.com')  # "[REDACTED]"
```

### 🛡️ Dashboard Hook Configuration

```python
redactor = Redactor({
    'api_key': 'your-api-key',
    'api_url': 'https://api.redactpii.com/v1/events',  # Optional, defaults to this
    'fail_silent': True,  # Default: True (fail silently if dashboard is down)
    'hook_timeout': 500,  # Default: 500ms timeout for dashboard requests
    'rules': {'EMAIL': True},
})
```

**Dashboard Payload:**

```json
{
  "sdk_version": "1.0.0",
  "sdk_language": "python",
  "events": [
    { "pii_type": "EMAIL", "action": "REDACTED" },
    { "pii_type": "PHONE_NUMBER", "action": "REDACTED" }
  ]
}
```

## 🧪 Quality Assurance

- **Comprehensive tests** covering all APIs and edge cases
- **100% type hints** with mypy strict mode
- **Zero unsafe operations** - full type safety
- **Pre-commit hooks** - automatic linting and type checking

### 🏃‍♂️ Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=redactpii --cov-report=html

# Type checking
mypy redactpii

# Linting
ruff check redactpii tests
```

### 🤝 Contributing

We welcome contributions! This library powers compliance for thousands of applications.

---

**Built for the modern AI stack with optional SOC 2/HIPAA audit logs.**

