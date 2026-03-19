from __future__ import annotations

import httpx
import pytest

from sinch_messaging import (
    BadRequestError,
    Channel,
    ForbiddenError,
    MessageStatus,
    NotFoundError,
    SinchClient,
)
from sinch_messaging.http import HttpClient
from sinch_messaging.resources.messages import MessagesResource


def _make_client(handler) -> SinchClient:
    transport = httpx.MockTransport(handler)
    client = SinchClient(auth_token="token", base_url="https://test.local")
    client._http = HttpClient(
        base_url="https://test.local",
        auth_token="token",
        transport=transport,
    )
    client.messages = MessagesResource(client._http)
    return client


def test_send_sms() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/messages"
        assert request.headers["X-Sinch-Auth"] == "token"

        payload = request.read().decode()
        assert '"channel":"sms"' in payload
        assert '"recipient":"+34600111222"' in payload
        assert '"text_message":"Hello from integration test"' in payload

        return httpx.Response(
            202,
            json={
                "message_id": "msg_sms_1",
                "status": "ACCEPTED",
                "channel": "sms",
                "recipient_id": "+34600111222",
                "created_at": "2026-03-19T10:30:00Z",
            },
        )

    client = _make_client(handler)

    message = client.messages.send_sms(
        to="+34600111222",
        text="Hello from integration test",
    )

    assert message.message_id == "msg_sms_1"
    assert message.status is MessageStatus.ACCEPTED
    assert message.channel is Channel.SMS

    client.close()


def test_send_whatsapp() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/messages"

        payload = request.read().decode()
        assert '"channel":"whatsapp"' in payload
        assert '"identifier":"+34600999888"' in payload
        assert '"type":"whatsapp_id"' in payload
        assert '"text_message":"Hi from WhatsApp"' in payload

        return httpx.Response(
            202,
            json={
                "message_id": "msg_wa_1",
                "status": "ACCEPTED",
                "channel": "whatsapp",
                "recipient_id": "+34600999888",
                "created_at": "2026-03-19T10:35:00Z",
            },
        )

    client = _make_client(handler)

    message = client.messages.send_whatsapp(
        to="+34600999888",
        text="Hi from WhatsApp",
    )

    assert message.message_id == "msg_wa_1"
    assert message.status is MessageStatus.ACCEPTED
    assert message.channel is Channel.WHATSAPP

    client.close()


def test_get_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/messages/msg_123"

        return httpx.Response(
            200,
            json={
                "message_id": "msg_123",
                "status": "DELIVERED",
                "channel": "sms",
                "recipient_id": "+34600111222",
                "created_at": "2026-03-19T10:40:00Z",
            },
        )

    client = _make_client(handler)

    message = client.messages.get("msg_123")

    assert message.message_id == "msg_123"
    assert message.status is MessageStatus.DELIVERED
    assert message.channel is Channel.SMS

    client.close()


def test_list_messages() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/messages"
        assert request.url.params.get("page_size") == "2"

        return httpx.Response(
            200,
            json={
                "messages": [
                    {
                        "message_id": "msg_1",
                        "status": "SENT",
                        "channel": "sms",
                        "recipient_id": "+1",
                        "created_at": "2026-03-19T10:00:00Z",
                    },
                    {
                        "message_id": "msg_2",
                        "status": "DELIVERED",
                        "channel": "whatsapp",
                        "recipient_id": "+2",
                        "created_at": "2026-03-19T10:01:00Z",
                    },
                ],
                "next_page_token": "next-token",
            },
        )

    client = _make_client(handler)

    page = client.messages.list(page_size=2)

    assert len(page.items) == 2
    assert page.items[0].message_id == "msg_1"
    assert page.items[1].channel is Channel.WHATSAPP
    assert page.next_page_token == "next-token"

    client.close()


def test_iterate_auto_paginates() -> None:
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, str(request.url)))
        token = request.url.params.get("pageToken")

        if token is None:
            return httpx.Response(
                200,
                json={
                    "messages": [
                        {
                            "message_id": "msg_1",
                            "status": "ACCEPTED",
                            "channel": "sms",
                            "recipient_id": "+1",
                            "created_at": "2026-03-18T10:00:00Z",
                        }
                    ],
                    "next_page_token": "next-token",
                },
            )

        return httpx.Response(
            200,
            json={
                "messages": [
                    {
                        "message_id": "msg_2",
                        "status": "DELIVERED",
                        "channel": "sms",
                        "recipient_id": "+2",
                        "created_at": "2026-03-18T10:01:00Z",
                    }
                ]
            },
        )

    client = _make_client(handler)

    messages = list(client.messages.iterate(page_size=1))

    assert [message.message_id for message in messages] == ["msg_1", "msg_2"]
    assert len(calls) == 2

    client.close()


def test_recall_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/messages/msg_123"
        return httpx.Response(202)

    client = _make_client(handler)

    result = client.messages.recall("msg_123")

    assert result is None

    client.close()


def test_send_sms_bad_request_error_is_normalized() -> None:
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

    client = _make_client(handler)

    with pytest.raises(BadRequestError) as exc_info:
        client.messages.send_sms(
            to="not-a-phone",
            text="hello",
        )

    exc = exc_info.value
    assert exc.status_code == 400
    assert exc.code == "INVALID_RECIPIENT"
    assert exc.message == "Recipient format is invalid"

    client.close()


def test_get_not_found_error_is_normalized() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={
                "error_code": "NOT_FOUND",
                "detail": "Message not found",
                "tracking_id": "trk-404",
            },
        )

    client = _make_client(handler)

    with pytest.raises(NotFoundError) as exc_info:
        client.messages.get("missing-message")

    exc = exc_info.value
    assert exc.status_code == 404
    assert exc.code == "NOT_FOUND"
    assert exc.message == "Message not found"
    assert exc.tracking_id == "trk-404"

    client.close()


def test_recall_forbidden_error_is_normalized() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={
                "error_code": "RECALL_NOT_ALLOWED",
                "detail": "Recall is not allowed for this message",
                "tracking_id": "trk-403",
            },
        )

    client = _make_client(handler)

    with pytest.raises(ForbiddenError) as exc_info:
        client.messages.recall("msg_999")

    exc = exc_info.value
    assert exc.status_code == 403
    assert exc.code == "RECALL_NOT_ALLOWED"
    assert exc.message == "Recall is not allowed for this message"
    assert exc.tracking_id == "trk-403"

    client.close()


def test_client_context_manager() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "messages": [],
                "next_page_token": None,
            },
        )

    transport = httpx.MockTransport(handler)

    with SinchClient(auth_token="token", base_url="https://test.local") as client:
        client._http = HttpClient(
            base_url="https://test.local",
            auth_token="token",
            transport=transport,
        )
        client.messages = MessagesResource(client._http)

        page = client.messages.list()

        assert page.items == []
        assert page.next_page_token is None