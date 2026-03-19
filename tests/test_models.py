from __future__ import annotations

from datetime import datetime

import pytest

from sinch_messaging.models import Channel, Message, MessagePage, MessageStatus


def test_message_from_dict_parses_fields() -> None:
    message = Message.from_dict(
        {
            "message_id": "msg_123",
            "status": "DELIVERED",
            "channel": "sms",
            "recipient_id": "+34600111222",
            "created_at": "2026-03-19T10:30:00",
        }
    )

    assert message.message_id == "msg_123"
    assert message.status is MessageStatus.DELIVERED
    assert message.channel is Channel.SMS
    assert message.recipient_id == "+34600111222"
    assert message.created_at == datetime(2026, 3, 19, 10, 30, 0)


def test_message_from_dict_missing_fields_raises_value_error() -> None:
    with pytest.raises(ValueError) as exc_info:
        Message.from_dict(
            {
                "message_id": "msg_123",
                "status": "DELIVERED",
                "channel": "sms",
            }
        )

    assert "missing required fields" in str(exc_info.value)


def test_message_from_dict_invalid_status_raises_value_error() -> None:
    with pytest.raises(ValueError) as exc_info:
        Message.from_dict(
            {
                "message_id": "msg_123",
                "status": "UNKNOWN",
                "channel": "sms",
                "recipient_id": "+34600111222",
                "created_at": "2026-03-19T10:30:00",
            }
        )

    assert "Invalid message payload" in str(exc_info.value)


def test_message_from_dict_invalid_channel_raises_value_error() -> None:
    with pytest.raises(ValueError) as exc_info:
        Message.from_dict(
            {
                "message_id": "msg_123",
                "status": "SENT",
                "channel": "email",
                "recipient_id": "+34600111222",
                "created_at": "2026-03-19T10:30:00",
            }
        )

    assert "Invalid message payload" in str(exc_info.value)


def test_message_from_dict_invalid_datetime_raises_value_error() -> None:
    with pytest.raises(ValueError) as exc_info:
        Message.from_dict(
            {
                "message_id": "msg_123",
                "status": "SENT",
                "channel": "sms",
                "recipient_id": "+34600111222",
                "created_at": "not-a-date",
            }
        )

    assert "Invalid message payload" in str(exc_info.value)


def test_message_page_from_dict_parses_messages_and_token() -> None:
    page = MessagePage.from_dict(
        {
            "messages": [
                {
                    "message_id": "msg_1",
                    "status": "SENT",
                    "channel": "sms",
                    "recipient_id": "+111",
                    "created_at": "2026-03-19T10:30:00",
                },
                {
                    "message_id": "msg_2",
                    "status": "DELIVERED",
                    "channel": "whatsapp",
                    "recipient_id": "+222",
                    "created_at": "2026-03-19T11:30:00",
                },
            ],
            "next_page_token": "next-123",
        }
    )

    assert len(page.items) == 2
    assert page.items[0].message_id == "msg_1"
    assert page.items[1].channel is Channel.WHATSAPP
    assert page.next_page_token == "next-123"


def test_message_page_from_dict_defaults_to_empty_items() -> None:
    page = MessagePage.from_dict({})

    assert page.items == []
    assert page.next_page_token is None


def test_message_page_from_dict_requires_messages_list() -> None:
    with pytest.raises(ValueError) as exc_info:
        MessagePage.from_dict({"messages": "not-a-list"})

    assert "'messages' must be a list" in str(exc_info.value)