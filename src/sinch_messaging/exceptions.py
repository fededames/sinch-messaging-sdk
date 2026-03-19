from __future__ import annotations


class SinchError(Exception):
    """Base exception for all SDK errors."""


class SinchAPIError(SinchError):
    def __init__(
            self,
            *,
            status_code: int,
            code: str | None,
            message: str,
            tracking_id: str | None = None,
            raw_response: object | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.tracking_id = tracking_id
        self.raw_response = raw_response

    def __str__(self) -> str:
        prefix_parts = [str(self.status_code)]

        if self.code:
            prefix_parts.append(self.code)

        prefix = " ".join(prefix_parts)

        message = f"{prefix}: {self.message}"

        if self.tracking_id:
            message += f" (tracking_id={self.tracking_id})"

        return message


class BadRequestError(SinchAPIError):
    """400"""


class UnauthorizedError(SinchAPIError):
    """401"""


class ForbiddenError(SinchAPIError):
    """403"""


class NotFoundError(SinchAPIError):
    """404"""


class ServerError(SinchAPIError):
    """5xx"""


# 🔹 Network / transport errors (no HTTP response)
class RequestError(SinchError):
    """Base class for request/connection issues."""


class RequestTimeoutError(RequestError):
    """Timeout while calling Sinch API."""