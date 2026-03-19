from __future__ import annotations

from typing import Any
import logging

import httpx

from .exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    ServerError,
    SinchAPIError,
    UnauthorizedError,
    RequestError,
    RequestTimeoutError,
)


logger = logging.getLogger(__name__)


class HttpClient:
    def __init__(
        self,
        *,
        base_url: str,
        auth_token: str,
        timeout: float = 10.0,
        transport: httpx.BaseTransport | None = None,
        redact_fields: set[str] | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={"X-Sinch-Auth": auth_token},
            transport=transport,
        )
        self._redact_fields = redact_fields or {"recipient", "message_content"}

    # -------------------------
    # Public methods
    # -------------------------

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("GET", path, params=params)

    def post(self, path: str, *, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("POST", path, json=json)

    def delete(self, path: str) -> None:
        self._request("DELETE", path, expect_json=False)

    def close(self) -> None:
        self._client.close()

    # -------------------------
    # Internal helpers
    # -------------------------

    def _redact(self, data: dict[str, Any] | None) -> dict[str, Any] | None:
        if data is None:
            return None

        redacted = data.copy()
        for field in self._redact_fields:
            if field in redacted:
                redacted[field] = "***"
        return redacted

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        expect_json: bool = True,
    ) -> dict[str, Any]:
        logger.debug(
            "Request: method=%s path=%s params=%s body=%s",
            method,
            path,
            params,
            self._redact(json),
        )

        try:
            response = self._client.request(method, path, params=params, json=json)
        except httpx.TimeoutException as exc:
            raise RequestTimeoutError("Request to Sinch API timed out") from exc
        except httpx.HTTPError as exc:
            raise RequestError(f"Request to Sinch API failed: {exc}") from exc

        logger.debug("Response: status=%s", response.status_code)

        if response.status_code >= 400:
            self._raise_api_error(response)

        if not expect_json or not response.content:
            return {}

        return response.json()

    def _raise_api_error(self, response: httpx.Response) -> None:
        try:
            payload = response.json()
        except ValueError:
            payload = None

        code: str | None = None
        message = response.text or "Request failed"
        tracking_id: str | None = None

        if isinstance(payload, dict):
            # ErrorV1
            if "fault" in payload:
                fault = payload.get("fault") or {}
                code = fault.get("code")
                message = fault.get("description") or message
            # ErrorV2
            else:
                code = payload.get("error_code")
                message = payload.get("detail") or message
                tracking_id = payload.get("tracking_id")

        raw_response = payload if payload is not None else response.text

        kwargs = dict(
            status_code=response.status_code,
            code=code,
            message=message,
            tracking_id=tracking_id,
            raw_response=raw_response,
        )

        match response.status_code:
            case 400:
                raise BadRequestError(**kwargs)
            case 401:
                raise UnauthorizedError(**kwargs)
            case 403:
                raise ForbiddenError(**kwargs)
            case 404:
                raise NotFoundError(**kwargs)
            case status if status >= 500:
                raise ServerError(**kwargs)
            case _:
                raise SinchAPIError(**kwargs)