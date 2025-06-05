"""Test lock entities."""

from unittest.mock import AsyncMock

from aiohttp import ClientResponseError
from homeassistant.components.lock import DOMAIN as LOCK_DOMAIN, LockState
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_LOCK, SERVICE_UNLOCK
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker
from syrupy.assertion import SnapshotAssertion

from . import MOCK_API_ENDPOINT, setup_integration

NO_ERROR = None.__class__


@pytest.mark.parametrize(
    (
        "service_action",
        "api_status",
        "api_status_slug",
        "expected_state",
        "expected_raises",
    ),
    [
        (SERVICE_LOCK, 200, "success", LockState.LOCKED, NO_ERROR),
        (SERVICE_UNLOCK, 200, "success", LockState.UNLOCKED, NO_ERROR),
        (SERVICE_LOCK, 409, "unreachable", LockState.UNLOCKED, NO_ERROR),
        (SERVICE_UNLOCK, 409, "unreachable", LockState.UNLOCKED, NO_ERROR),
        (SERVICE_LOCK, 401, "unauthroized", LockState.UNLOCKED, NO_ERROR),
        (SERVICE_UNLOCK, 401, "unauthroized", LockState.UNLOCKED, NO_ERROR),
        (SERVICE_UNLOCK, 500, "server", LockState.UNLOCKED, ClientResponseError),
    ],
)
@pytest.mark.parametrize("vehicle_fixture", ["unknown_make"])
async def test_lock(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    snapshot: SnapshotAssertion,
    vehicle: AsyncMock,
    service_action: str,
    api_status: int,
    api_status_slug: str,
    expected_state: LockState,
    expected_raises: Exception,
) -> None:
    """Test locking doors."""

    await setup_integration(hass, mock_config_entry)
    assert len(aioclient_mock.mock_calls) == 1

    aioclient_mock.post(
        f"{MOCK_API_ENDPOINT}/v2.0/vehicles/{vehicle['id']}/security",
        status=api_status,
        json={
            "message": "Some message related to the action unused by our code",
            "status": api_status_slug,
        },
    )

    try:
        await hass.services.async_call(
            LOCK_DOMAIN,
            service_action,
            {ATTR_ENTITY_ID: "lock.smartcar_784n_door_lock"},
            blocking=True,
        )
    except Exception as error:  # noqa: BLE001
        raised_error = error
    else:
        raised_error = None  # type: ignore[assignment]

    lock_state = hass.states.get("lock.smartcar_784n_door_lock")
    assert lock_state.state == expected_state
    assert isinstance(
        raised_error,
        expected_raises,  # type: ignore[arg-type]
    )

    assert len(aioclient_mock.mock_calls) == 2
    assert [tuple(mock_call) for mock_call in aioclient_mock.mock_calls[1:]] == snapshot
