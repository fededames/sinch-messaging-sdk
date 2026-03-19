from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class Channel(StrEnum):
    SMS = "sms"
    WHATSAPP = "whatsapp"


class MessageStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


@dataclass(slots=True)
class Message:
    message_id: str
    status: MessageStatus
    channel: Channel | str
    recipient_id: str
    created_at: datetime

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        required_fields = [
            "message_id",
            "status",
            "channel",
            "recipient_id",
            "created_at",
        ]
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(
                f"Invalid message payload: missing required fields: {', '.join(missing)}"
            )

        try:
            return cls(
                message_id=str(data["message_id"]),
                status=MessageStatus(data["status"]),
                channel=Channel(data["channel"]),
                recipient_id=str(data["recipient_id"]),
                created_at=datetime.fromisoformat(str(data["created_at"])),
            )
        except ValueError as exc:
            raise ValueError(f"Invalid message payload: {exc}") from exc

@dataclass(slots=True)
class MessagePage:
    items: list[Message]
    next_page_token: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MessagePage":
        raw_items = data.get("messages", [])
        if not isinstance(raw_items, list):
            raise ValueError("Invalid message page payload: 'messages' must be a list")

        return cls(
            items=[Message.from_dict(item) for item in raw_items],
            next_page_token=data.get("next_page_token"),
        )
