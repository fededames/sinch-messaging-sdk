# Sinch Messaging Python SDK

A developer-friendly Python SDK for the Sinch Messaging API (simplified).

This project focuses on providing a clean, consistent, and intuitive developer experience on top of an intentionally inconsistent API specification.

---

## ✨ Features

- Clean and intuitive resource-based API
- Consistent error handling across multiple API formats
- Strongly typed models
- Automatic pagination via iterators
- Simple authentication setup
- Context manager support for resource handling
- Fully tested core functionality

---

## 📦 Installation

Clone the repository and install in editable mode:

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

---

## 🚀 Quick Start

### Basic usage

```python
from sinch_messaging import SinchClient

client = SinchClient(auth_token="your-token")

message = client.messages.send_sms(
    to="+34600111222",
    text="Hello from SDK!"
)

print(message.message_id)

client.close()
```

### Using a context manager (recommended)

```python
from sinch_messaging import SinchClient

with SinchClient(auth_token="your-token") as client:
    for msg in client.messages.iterate():
        print(msg.message_id)
```

---

## 🧩 API Overview

### Send a message

```python
client.messages.send(channel="sms", to="+34600111222", text="Hello")
client.messages.send(channel="whatsapp", to="+34600111222", text="Hello")
```

Convenience methods:

```python
client.messages.send_sms(...)
client.messages.send_whatsapp(...)
```

---

### Retrieve a message

```python
message = client.messages.get("message_id")
```

---

### List messages

```python
page = client.messages.list(page_size=20)
```

---

### Iterate through all messages (auto-pagination)

```python
for message in client.messages.iterate():
    print(message.message_id)
```

---

### Recall a message

```python
client.messages.recall("message_id")
```

---

## 🧠 Design Decisions

### Resource-based API

Instead of mapping endpoints 1:1, the SDK exposes domain-oriented resources:

```python
client.messages.send(...)
```

This improves discoverability and aligns with common Python SDK patterns.

---

### Error normalization

The API returns inconsistent error formats:

- ErrorV1 (nested `fault`)
- ErrorV2 (flat structure)

The SDK normalizes both into a unified exception hierarchy:

```python
try:
    client.messages.get("invalid")
except NotFoundError as e:
    print(e)
```

---

### Channel abstraction

The API uses different `recipient` formats depending on the channel.

The SDK hides this complexity by:

- Providing a unified `send()` interface
- Using internal strategies to construct channel-specific payloads

---

### Pagination simplification

The API uses token-based pagination.

The SDK provides:

- `list()` → low-level access
- `iterate()` → automatic pagination

---

### Strongly typed models

API responses are converted into structured Python objects:

- Message
- MessagePage
- Channel
- MessageStatus

---

### HTTP layer separation

The HTTP layer is isolated in HttpClient, responsible for:

- Request execution
- Authentication handling
- Error mapping
- Logging and timeouts

---

### Logging and privacy

The SDK includes debug logging while avoiding sensitive data exposure.

---

## 🧪 Testing

Run tests:

```bash
pytest
```

The test suite covers:

- Payload correctness
- Error normalization
- Pagination behavior
- Model parsing
- Integration flows using mocked HTTP

---

## 🔧 Project Structure

```bash
src/
  sinch_messaging/
    __init__.py
    sinch_client.py
    http.py
    models.py
    exceptions.py
    resources/
      messages.py

tests/
  integration/
```

---

## 🚧 Future Improvements

- CLI interface using typer
- Async client support
- Retry policies
- Rate limiting
- OpenAPI-based code generation

---

## ⚙️ Optional Features Not Implemented

### CLI Tool

A CLI was not implemented in this submission, as the focus was on the SDK itself.

Example:

```bash
sinch-messaging send --channel sms --to "+1555..." --text "Hello"
```

Use cases:

- Quick testing
- Scripting
- Debugging
- CI/CD

---

### Code Generation

I did not use OpenAPI-based code generation.

In a production scenario:

- Use generator for low-level client
- Add handwritten layer for:
  - error normalization
  - better DX
  - abstraction

---

## 🎥 Video walkthrough

https://youtu.be/srF296qAIxQ

---

## 📄 License

MIT
