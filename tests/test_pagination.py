from __future__ import annotations

import httpx

from sinch_messaging import SinchClient


def test_iter_auto_paginates() -> None:
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

    transport = httpx.MockTransport(handler)
    client = SinchClient(auth_token="token", base_url="https://test.local")
    client._http._client = httpx.Client(
        base_url="https://test.local",
        headers={"X-Sinch-Auth": "token"},
        transport=transport,
    )

    messages = list(client.messages.iterate(page_size=1))

    assert [message.message_id for message in messages] == ["msg_1", "msg_2"]
    assert len(calls) == 2
    client.close()
