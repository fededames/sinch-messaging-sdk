from __future__ import annotations

import httpx
import pytest

from sinch_messaging.exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    RequestTimeoutError,
    ServerError, RequestError,
)
from sinch_messaging.http import HttpClient


def make_client(handler):
    transport = httpx.MockTransport(handler)
    return HttpClient(
        base_url="https://messaging.api.sinch.com/v1",
        auth_token="test-token",
        transport=transport,
    )


def test_get_returns_json_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/v1/messages/abc"
        assert request.headers["X-Sinch-Auth"] == "test-token"
        return httpx.Response(
            200,
            json={
                "message_id": "abc",
                "status": "SENT",
                "channel": "sms",
                "recipient_id": "+34600111222",
                "created_at": "2026-03-19T10:30:00",
            },
        )

    client = make_client(handler)

    data = client.get("/messages/abc")

    assert data["message_id"] == "abc"
    client.close()


def test_post_sends_json_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/messages"
        assert request.headers["X-Sinch-Auth"] == "test-token"
        assert request.headers["content-type"].startswith("application/json")
        payload = request.read().decode()
        assert '"channel":"sms"' in payload
        assert '"recipient":"+34600111222"' in payload
        return httpx.Response(
            202,
            json={
                "message_id": "msg_123",
                "status": "ACCEPTED",
                "channel": "sms",
                "recipient_id": "+34600111222",
                "created_at": "2026-03-19T10:30:00",
            },
        )

    client = make_client(handler)

    data = client.post(
        "/messages",
        json={
            "channel": "sms",
            "recipient": "+34600111222",
            "message_content": {"text_message": "hello"},
        },
    )

    assert data["message_id"] == "msg_123"
    client.close()


def test_delete_accepts_empty_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/v1/messages/msg_123"
        return httpx.Response(202)

    client = make_client(handler)

    client.delete("/messages/msg_123")
    client.close()


def test_bad_request_error_v1_is_normalized() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "fault": {
                    "code": "INVALID_RECIPIENT",
                    "description": "Recipient format is invalid",
                }
            },
        )

    client = make_client(handler)

    with pytest.raises(BadRequestError) as exc_info:
        client.post("/messages", json={"foo": "bar"})

    exc = exc_info.value
    assert exc.status_code == 400
    assert exc.code == "INVALID_RECIPIENT"
    assert exc.message == "Recipient format is invalid"
    assert exc.raw_response == {
        "fault": {
            "code": "INVALID_RECIPIENT",
            "description": "Recipient format is invalid",
        }
    }
    client.close()


def test_not_found_error_v2_is_normalized() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={
                "error_code": "NOT_FOUND",
                "detail": "Message not found",
                "tracking_id": "trk-123",
            },
        )

    client = make_client(handler)

    with pytest.raises(NotFoundError) as exc_info:
        client.get("/messages/missing")

    exc = exc_info.value
    assert exc.status_code == 404
    assert exc.code == "NOT_FOUND"
    assert exc.message == "Message not found"
    assert exc.tracking_id == "trk-123"
    client.close()


def test_forbidden_error_v2_is_normalized() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={
                "error_code": "RECALL_NOT_ALLOWED",
                "detail": "Recall is not allowed for this message",
                "tracking_id": "trk-456",
            },
        )

    client = make_client(handler)

    with pytest.raises(ForbiddenError) as exc_info:
        client.delete("/messages/msg_123")

    exc = exc_info.value
    assert exc.status_code == 403
    assert exc.code == "RECALL_NOT_ALLOWED"
    assert exc.message == "Recall is not allowed for this message"
    assert exc.tracking_id == "trk-456"
    client.close()


def test_server_error_is_normalized() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Service unavailable")

    client = make_client(handler)

    with pytest.raises(ServerError) as exc_info:
        client.get("/messages")

    exc = exc_info.value
    assert exc.status_code == 503
    assert exc.code is None
    assert "Service unavailable" in exc.message
    client.close()


def test_non_json_error_body_is_preserved() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    client = make_client(handler)

    with pytest.raises(ServerError) as exc_info:
        client.get("/messages")

    exc = exc_info.value
    assert exc.raw_response == "Internal Server Error"
    client.close()


def test_timeout_is_wrapped() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("boom")

    client = make_client(handler)

    with pytest.raises(RequestTimeoutError):
        client.get("/messages")

    client.close()


def test_transport_error_is_wrapped() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    client = make_client(handler)

    with pytest.raises(RequestError) as exc_info:
        client.get("/messages")

    assert "Request to Sinch API failed" in str(exc_info.value)
    client.close()

