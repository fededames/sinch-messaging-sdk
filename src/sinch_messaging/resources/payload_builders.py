from __future__ import annotations

from typing import Any, Protocol

from ..models import Channel


class MessagePayloadBuilder(Protocol):
    channel: Channel

    def build(self, *, to: str, text: str) -> dict[str, Any]:
        ...


class SmsPayloadBuilder(MessagePayloadBuilder):
    channel: Channel = Channel.SMS

    def build(self, *, to: str, text: str) -> dict[str, Any]:
        return {
            "channel": self.channel.value,
            "recipient": to,
            "message_content": {"text_message": text},
        }


class WhatsAppPayloadBuilder(MessagePayloadBuilder):
    channel: Channel = Channel.WHATSAPP

    def build(self, *, to: str, text: str) -> dict[str, Any]:
        return {
            "channel": self.channel.value,
            "recipient": {
                "identifier": to,
                "type": "whatsapp_id",
            },
            "message_content": {"text_message": text},
        }
