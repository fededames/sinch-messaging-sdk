from __future__ import annotations

from sinch_messaging.exceptions import SinchAPIError


def test_sinch_api_error_str_without_code_or_tracking_id() -> None:
    exc = SinchAPIError(
        status_code=500,
        code=None,
        message="Internal server error",
    )

    assert str(exc) == "500: Internal server error"


def test_sinch_api_error_str_with_code_and_tracking_id() -> None:
    exc = SinchAPIError(
        status_code=404,
        code="NOT_FOUND",
        message="Message not found",
        tracking_id="trk-123",
    )

    assert str(exc) == "404 NOT_FOUND: Message not found (tracking_id=trk-123)"