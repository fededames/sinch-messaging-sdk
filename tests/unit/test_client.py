from __future__ import annotations

import pytest

from sinch_messaging import SinchClient


def test_client_requires_auth_token() -> None:
    with pytest.raises(ValueError) as exc_info:
        SinchClient(auth_token="")

    assert "auth_token must be provided" in str(exc_info.value)


def test_client_exposes_messages_resource() -> None:
    client = SinchClient(auth_token="test-token")

    assert client.messages is not None

    client.close()


def test_client_context_manager_returns_self() -> None:
    with SinchClient(auth_token="test-token") as client:
        assert isinstance(client, SinchClient)


def test_client_repr_is_stable() -> None:
    client = SinchClient(auth_token="test-token")

    assert repr(client) == "SinchClient()"

    client.close()