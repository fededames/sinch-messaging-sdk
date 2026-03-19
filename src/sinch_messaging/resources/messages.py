from __future__ import annotations

from typing import Iterator

from ..http import HttpClient
from ..models import Channel, Message, MessagePage
from .payload_builders import (
    MessagePayloadBuilder,
    SmsPayloadBuilder,
    WhatsAppPayloadBuilder,
)


class MessagesResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

        self._builders: dict[Channel, MessagePayloadBuilder] = {
            Channel.SMS: SmsPayloadBuilder(),
            Channel.WHATSAPP: WhatsAppPayloadBuilder(),
        }

    def send(self, *, channel: str | Channel, to: str, text: str) -> Message:
        normalized_channel = self._normalize_channel(channel)
        builder = self._get_builder(normalized_channel)
        payload = builder.build(to=to, text=text)
        data = self._http.post("/messages", json=payload)
        return Message.from_dict(data)

    def send_sms(self, *, to: str, text: str) -> Message:
        return self.send(channel=Channel.SMS, to=to, text=text)

    def send_whatsapp(self, *, to: str, text: str) -> Message:
        return self.send(channel=Channel.WHATSAPP, to=to, text=text)

    def get(self, message_id: str) -> Message:
        data = self._http.get(f"/messages/{message_id}")
        return Message.from_dict(data)

    def list(
        self,
        *,
        page_size: int = 20,
        page_token: str | None = None,
    ) -> MessagePage:
        params: dict[str, int | str] = {"page_size": page_size}
        if page_token:
            params["pageToken"] = page_token
        data = self._http.get("/messages", params=params)
        return MessagePage.from_dict(data)

    def iterate(self, *, page_size: int = 20) -> Iterator[Message]:
        page_token: str | None = None
        while True:
            page = self.list(page_size=page_size, page_token=page_token)
            yield from page.items
            if not page.next_page_token:
                break
            page_token = page.next_page_token

    def recall(self, message_id: str) -> None:
        self._http.delete(f"/messages/{message_id}")

    def _normalize_channel(self, channel: str | Channel) -> Channel:
        try:
            return Channel(channel)
        except ValueError:
            valid = ", ".join(c.value for c in Channel)
            raise ValueError(
                f"Invalid channel '{channel}'. Supported channels are: {valid}"
            )

    def _get_builder(self, channel: Channel) -> MessagePayloadBuilder:
        try:
            return self._builders[channel]
        except KeyError:
            raise ValueError(f"No payload builder registered for channel '{channel.value}'")
