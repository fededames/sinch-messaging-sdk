# Sinch Messaging Python SDK

A developer-friendly Python SDK for the Sinch Messaging API (simplified).  
This project focuses on providing a clean, consistent, and intuitive developer experience on top of an intentionally inconsistent API.

---

## ✨ Features

- Clean and intuitive client API
- Consistent error handling across different API formats
- Strongly typed models
- Automatic pagination via iterators
- Simple authentication setup
- Fully tested core functionality
- Context manager support for resource handling

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

```python
from sinch_messaging import SinchClient

client = SinchClient(auth_token="your-token")

message = client.messages.send_sms(
    to="+34600111222",
    text="Hello from SDK!"
)

print(message.message_id)
```

Using context manager:

```python
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

### 1. Resource-based API

Instead of mapping endpoints 1:1, the SDK exposes domain-oriented resources:

```python
client.messages.send(...)
```

This makes the SDK more intuitive and easier to navigate.

---

### 2. Error Normalization

The API returns inconsistent error formats:

- `ErrorV1` (nested `fault`)
- `ErrorV2` (flat structure)

The SDK normalizes both into a consistent exception hierarchy:

```python
try:
    client.messages.get("invalid")
except NotFoundError as e:
    print(e)
```

---

### 3. Channel Abstraction

The API uses different `recipient` formats depending on the channel.

The SDK hides this complexity by:

- Providing a unified `send()` method
- Using internal strategies to build payloads per channel

---

### 4. Pagination Simplification

The API uses token-based pagination (`pageToken` / `next_page_token`).

The SDK provides:

- `list()` → single page
- `iterate()` → automatic pagination

```python
for msg in client.messages.iterate():
    ...
```

---

### 5. Strongly Typed Models

API responses are converted into structured Python models:

- `Message`
- `MessagePage`
- `Channel`
- `MessageStatus`

This improves:

- Readability
- Type safety
- Developer experience

---

### 6. HTTP Layer Separation

The HTTP client is isolated:

- `HttpClient`

Responsibilities:

- Request handling
- Error mapping
- Logging
- Timeouts

This keeps the SDK modular and testable.

---

### 7. Logging & Privacy

The SDK includes debug logging while avoiding sensitive data leaks:

- Request bodies are not fully logged
- Sensitive fields can be redacted

---

## 🧪 Testing

Run tests:

```bash
pytest
```

The test suite focuses on:

- Payload correctness
- Error normalization
- Pagination behavior
- Model parsing
- Edge cases

---

## 🔧 Project Structure

```bash
src/
  sinch_messaging/
    sinch_client.py
    http.py
    models.py
    exceptions.py
    resources/
      messages.py

tests/
```

---

## 🚧 Future Improvements

- CLI interface using `typer`
- Async client support
- Retry policies
- Rate limiting support
- OpenAPI-based code generation

---

## 💡 Notes

This SDK was designed with a strong focus on developer experience rather than strict API mirroring.

---

## Optional Features Not Implemented

### CLI Tool

I did not implement a CLI in this submission, as I prioritized the SDK itself: client design, error normalization, pagination ergonomics, model parsing, and tests.

A CLI would be a thin layer on top of the SDK and could be implemented with a library such as `typer` or `click`. For example:

```bash
sinch-messaging send --channel sms --to "+1555..." --text "Hello"
sinch-messaging get --message-id "msg_123"
sinch-messaging list --page-size 20
```

Internally, the CLI would simply call the SDK:
```bash
client.messages.send(channel="sms", to="+1555...", text="Hello")
```
A customer might prefer the CLI over the SDK when:

- Testing the API quickly from a terminal

- Scripting operational workflows in shell environments

- Debugging integrations without writing Python code

- Using the tool in CI/CD pipelines or internal automation

- For product teams and application developers, the SDK remains the better choice because it provides a richer, typed, and more integrated programming interface.

---


## 📄 License

MIT
