from __future__ import annotations

from typing import Self

from .http import HttpClient
from .resources.messages import MessagesResource


class SinchClient:

    def __init__(
        self,
        auth_token: str,
        base_url: str = "https://messaging.api.sinch.com/v1",
        timeout: float = 10.0,
    ) -> None:
        if not auth_token:
            raise ValueError("auth_token must be provided")

        self._http = HttpClient(
            base_url=base_url,
            auth_token=auth_token,
            timeout=timeout,
        )
        self.messages = MessagesResource(self._http)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"