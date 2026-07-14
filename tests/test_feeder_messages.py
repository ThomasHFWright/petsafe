"""Unit tests for SmartFeed message handling."""

from __future__ import annotations

from unittest.mock import AsyncMock

from petsafe.devices import DeviceSmartFeed
import pytest


def _create_feeder() -> DeviceSmartFeed:
    """Create a feeder without making API requests."""
    return DeviceSmartFeed(AsyncMock(), {"thing_name": "feeder-1"})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "messages",
    [
        [
            {"message_type": "FEED_DONE", "payload": {"time": 100}},
            {"message_type": "FEED_DONE", "payload": {"time": 300}},
            {"message_type": "FEED_DONE", "payload": {"time": 200}},
        ],
        [
            {"message_type": "FEED_DONE", "payload": {"time": 300}},
            {"message_type": "FEED_DONE", "payload": {"time": 200}},
            {"message_type": "FEED_DONE", "payload": {"time": 100}},
        ],
    ],
)
async def test_get_last_feeding_selects_latest_timestamp(messages) -> None:
    """The latest feeding should not depend on API response ordering."""
    feeder = _create_feeder()
    feeder.get_messages_since = AsyncMock(return_value=messages)

    result = await feeder.get_last_feeding()

    assert result == {"message_type": "FEED_DONE", "payload": {"time": 300}}


@pytest.mark.asyncio
async def test_get_last_feeding_ignores_other_and_malformed_messages() -> None:
    """Non-feeding and malformed messages should not prevent selecting a feeding."""
    latest = {"message_type": "FEED_DONE", "payload": {"time": 300}}
    feeder = _create_feeder()
    feeder.get_messages_since = AsyncMock(
        return_value=[
            None,
            {},
            {"message_type": "FEED_DONE"},
            {"message_type": "FEED_DONE", "payload": None},
            {"message_type": "FEED_DONE", "payload": {"time": "newest"}},
            {"message_type": "STATUS", "payload": {"time": 400}},
            {"message_type": "FEED_DONE", "payload": {"time": 100}},
            latest,
        ]
    )

    assert await feeder.get_last_feeding() is latest


@pytest.mark.asyncio
async def test_get_last_feeding_returns_none_without_valid_feeding() -> None:
    """No valid feeding messages should produce no result."""
    feeder = _create_feeder()
    feeder.get_messages_since = AsyncMock(
        return_value=[
            {"message_type": "STATUS", "payload": {"time": 300}},
            {"message_type": "FEED_DONE", "payload": {}},
        ]
    )

    assert await feeder.get_last_feeding() is None
