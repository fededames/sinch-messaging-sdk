from __future__ import annotations

import httpx

from sinch_messaging import Channel, MessageStatus, SinchClient
from sinch_messaging.http import HttpClient
from sinch_messaging.resources.messages import MessagesResource


def test_sdk_smoke_send_sms_flow() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/messages"
        assert request.headers["X-Sinch-Auth"] == "test-token"

        body = request.read().decode()
        assert '"channel":"sms"' in body
        assert '"recipient":"+34600111222"' in body
        assert '"text_message":"hello"' in body

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

    transport = httpx.MockTransport(handler)

    client = SinchClient(auth_token="test-token")
    client._http = HttpClient(
        base_url="https://messaging.api.sinch.com/v1",
        auth_token="test-token",
        transport=transport,
    )
    client.messages = MessagesResource(client._http)

    message = client.messages.send_sms(
        to="+34600111222",
        text="hello",
    )

    assert message.message_id == "msg_123"
    assert message.status is MessageStatus.ACCEPTED
    assert message.channel is Channel.SMS

    client.close()