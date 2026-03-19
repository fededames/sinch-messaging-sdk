from __future__ import annotations

import pytest

from sinch_messaging.models import Channel, MessageStatus
from sinch_messaging.resources.messages import MessagesResource


class FakeHttpClient:
    def __init__(self) -> None:
        self.last_post_path = None
        self.last_post_json = None
        self.last_get_path = None
        self.last_get_params = None
        self.last_delete_path = None

        self.post_response = {
            "message_id": "msg_123",
            "status": "ACCEPTED",
            "channel": "sms",
            "recipient_id": "+34600111222",
            "created_at": "2026-03-19T10:30:00",
        }
        self.get_response = {
            "message_id": "msg_123",
            "status": "DELIVERED",
            "channel": "sms",
            "recipient_id": "+34600111222",
            "created_at": "2026-03-19T10:30:00",
        }
        self.get_responses = []

    def post(self, path, *, json=None):
        self.last_post_path = path
        self.last_post_json = json
        return self.post_response

    def get(self, path, *, params=None):
        self.last_get_path = path
        self.last_get_params = params
        if self.get_responses:
            return self.get_responses.pop(0)
        return self.get_response

    def delete(self, path):
        self.last_delete_path = path
        return None


def test_send_sms_builds_expected_payload() -> None:
    http = FakeHttpClient()
    resource = MessagesResource(http)

    message = resource.send(channel="sms", to="+34600111222", text="hello")

    assert http.last_post_path == "/messages"
    assert http.last_post_json == {
        "channel": "sms",
        "recipient": "+34600111222",
        "message_content": {"text_message": "hello"},
    }
    assert message.message_id == "msg_123"
    assert message.channel is Channel.SMS
    assert message.status is MessageStatus.ACCEPTED


def test_send_whatsapp_builds_expected_payload() -> None:
    http = FakeHttpClient()
    http.post_response = {
        "message_id": "msg_456",
        "status": "ACCEPTED",
        "channel": "whatsapp",
        "recipient_id": "+34600999888",
        "created_at": "2026-03-19T10:30:00",
    }
    resource = MessagesResource(http)

    message = resource.send(channel="whatsapp", to="+34600999888", text="hi")

    assert http.last_post_json == {
        "channel": "whatsapp",
        "recipient": {
            "identifier": "+34600999888",
            "type": "whatsapp_id",
        },
        "message_content": {"text_message": "hi"},
    }
    assert message.channel is Channel.WHATSAPP


def test_send_accepts_channel_enum() -> None:
    http = FakeHttpClient()
    resource = MessagesResource(http)

    resource.send(channel=Channel.SMS, to="+34600111222", text="hello")

    assert http.last_post_json["channel"] == "sms"


def test_send_invalid_channel_raises_friendly_error() -> None:
    http = FakeHttpClient()
    resource = MessagesResource(http)

    with pytest.raises(ValueError) as exc_info:
        resource.send(channel="email", to="+34600111222", text="hello")

    message = str(exc_info.value)
    assert "Invalid channel 'email'" in message
    assert "sms" in message
    assert "whatsapp" in message


def test_get_returns_message() -> None:
    http = FakeHttpClient()
    resource = MessagesResource(http)

    message = resource.get("msg_123")

    assert http.last_get_path == "/messages/msg_123"
    assert message.message_id == "msg_123"
    assert message.status is MessageStatus.DELIVERED


def test_list_passes_page_token_and_page_size() -> None:
    http = FakeHttpClient()
    http.get_response = {
        "messages": [
            {
                "message_id": "msg_1",
                "status": "SENT",
                "channel": "sms",
                "recipient_id": "+111",
                "created_at": "2026-03-19T10:30:00",
            }
        ],
        "next_page_token": "next-123",
    }
    resource = MessagesResource(http)

    page = resource.list(page_size=50, page_token="cursor-1")

    assert http.last_get_path == "/messages"
    assert http.last_get_params == {
        "page_size": 50,
        "pageToken": "cursor-1",
    }
    assert len(page.items) == 1
    assert page.next_page_token == "next-123"


def test_list_without_page_token_only_sends_page_size() -> None:
    http = FakeHttpClient()
    http.get_response = {"messages": [], "next_page_token": None}
    resource = MessagesResource(http)

    resource.list(page_size=10)

    assert http.last_get_params == {"page_size": 10}


def test_iterate_auto_paginates_until_no_next_token() -> None:
    http = FakeHttpClient()
    http.get_responses = [
        {
            "messages": [
                {
                    "message_id": "msg_1",
                    "status": "SENT",
                    "channel": "sms",
                    "recipient_id": "+111",
                    "created_at": "2026-03-19T10:30:00",
                }
            ],
            "next_page_token": "page-2",
        },
        {
            "messages": [
                {
                    "message_id": "msg_2",
                    "status": "DELIVERED",
                    "channel": "whatsapp",
                    "recipient_id": "+222",
                    "created_at": "2026-03-19T10:40:00",
                }
            ],
            "next_page_token": None,
        },
    ]
    resource = MessagesResource(http)

    messages = list(resource.iterate(page_size=1))

    assert [msg.message_id for msg in messages] == ["msg_1", "msg_2"]
    assert messages[0].channel is Channel.SMS
    assert messages[1].channel is Channel.WHATSAPP


def test_iterate_returns_empty_iterator_when_no_messages() -> None:
    http = FakeHttpClient()
    http.get_responses = [
        {"messages": [], "next_page_token": None},
    ]
    resource = MessagesResource(http)

    messages = list(resource.iterate())

    assert messages == []


def test_recall_deletes_message() -> None:
    http = FakeHttpClient()
    resource = MessagesResource(http)

    resource.recall("msg_123")

    assert http.last_delete_path == "/messages/msg_123"