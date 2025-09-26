from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfLength,
    UnitOfPressure,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util.unit_conversion import DistanceConverter, PressureConverter
from typing import Any, Callable

from .const import CONF_USE_IMPERIAL, EntityDescriptionKey
from .coordinator import SmartcarVehicleCoordinator
from .entity import SmartcarEntity, SmartcarEntityDescription

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SmartcarSensorDescription(SensorEntityDescription, SmartcarEntityDescription):
    """Class describing Smartcar sensor entities."""

    imperial_unit_of_measurement: str | None = None
    to_native_conversion: Callable[[Any], Any] | None = None
    from_native_conversion: Callable[[Any], Any] | None = None


SENSOR_TYPES: tuple[SmartcarSensorDescription, ...] = (
    SmartcarSensorDescription(
        key=EntityDescriptionKey.BATTERY_CAPACITY,
        name="Battery Capacity",
        value_key_path="battery_nominal_capacity.capacity.nominal",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    ),
    SmartcarSensorDescription(
        key=EntityDescriptionKey.BATTERY_LEVEL,
        name="Battery",
        value_key_path="battery.percentRemaining",
        value_cast=lambda pct: pct and round(pct * 100),
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    SmartcarSensorDescription(
        key=EntityDescriptionKey.CHARGING_STATE,
        name="Charging Status",
        value_key_path="charge.state",
        icon="mdi:ev-station",
    ),
    SmartcarSensorDescription(
        key=EntityDescriptionKey.ENGINE_OIL,
        name="Engine Oil Life",
        value_key_path="engine_oil.lifeRemaining",
        icon="mdi:oil-level",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    SmartcarSensorDescription(
        key=EntityDescriptionKey.FUEL,
        name="Fuel",
        value_key_path="fuel.amountRemaining",
        icon="mdi:gas-station",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        imperial_unit_of_measurement=UnitOfVolume.GALLONS,
        to_native_conversion=lambda v: DistanceConverter.convert(
            v, UnitOfVolume.GALLONS, UnitOfVolume.LITERS
        ),
        from_native_conversion=lambda v: DistanceConverter.convert(
            v, UnitOfVolume.LITERS, UnitOfVolume.GALLONS
        ),
    ),
    SmartcarSensorDescription(
        key=EntityDescriptionKey.FUEL_PERCENT,
        name="Fuel Percent",
        value_key_path="fuel.percentRemaining",
        value_cast=lambda pct: pct and round(pct * 100),
        icon="mdi:gas-station",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    SmartcarSensorDescription(
        key=EntityDescriptionKey.FUEL_RANGE,
        name="Fuel Range",
        value_key_path="fuel.range",
        icon="mdi:map-marker-distance",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        imperial_unit_of_measurement=UnitOfLength.MILES,
        to_native_conversion=lambda v: DistanceConverter.convert(
            v, UnitOfLength.MILES, UnitOfLength.KILOMETERS
        ),
        from_native_conversion=lambda v: DistanceConverter.convert(
            v, UnitOfLength.KILOMETERS, UnitOfLength.MILES
        ),
    ),
    SmartcarSensorDescription(
        key=EntityDescriptionKey.ODOMETER,
        name="Odometer",
        value_key_path="odometer.distance",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        imperial_unit_of_measurement=UnitOfLength.MILES,
        to_native_conversion=lambda v: DistanceConverter.convert(
            v, UnitOfLength.MILES, UnitOfLength.KILOMETERS
        ),
        from_native_conversion=lambda v: DistanceConverter.convert(
            v, UnitOfLength.KILOMETERS, UnitOfLength.MILES
        ),
    ),
    SmartcarSensorDescription(
        key=EntityDescriptionKey.RANGE,
        name="Range",
        value_key_path="battery.range",
        icon="mdi:map-marker-distance",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        imperial_unit_of_measurement=UnitOfLength.MILES,
        to_native_conversion=lambda v: DistanceConverter.convert(
            v, UnitOfLength.MILES, UnitOfLength.KILOMETERS
        ),
        from_native_conversion=lambda v: DistanceConverter.convert(
            v, UnitOfLength.KILOMETERS, UnitOfLength.MILES
        ),
    ),
    SmartcarSensorDescription(
        key=EntityDescriptionKey.TIRE_PRESSURE_BACK_LEFT,
        name="Tire Pressure Back Left",
        value_key_path="tires_pressure.backLeft",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        native_unit_of_measurement=UnitOfPressure.KPA,
        imperial_unit_of_measurement=UnitOfPressure.PSI,
        to_native_conversion=lambda v: PressureConverter.convert(
            v, UnitOfPressure.PSI, UnitOfPressure.KPA
        ),
        from_native_conversion=lambda v: PressureConverter.convert(
            v, UnitOfPressure.KPA, UnitOfPressure.PSI
        ),
    ),
    SmartcarSensorDescription(
        key=EntityDescriptionKey.TIRE_PRESSURE_BACK_RIGHT,
        name="Tire Pressure Back Right",
        value_key_path="tires_pressure.backRight",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        native_unit_of_measurement=UnitOfPressure.KPA,
        imperial_unit_of_measurement=UnitOfPressure.PSI,
        to_native_conversion=lambda v: PressureConverter.convert(
            v, UnitOfPressure.PSI, UnitOfPressure.KPA
        ),
        from_native_conversion=lambda v: PressureConverter.convert(
            v, UnitOfPressure.KPA, UnitOfPressure.PSI
        ),
    ),
    SmartcarSensorDescription(
        key=EntityDescriptionKey.TIRE_PRESSURE_FRONT_LEFT,
        name="Tire Pressure Front Left",
        value_key_path="tires_pressure.frontLeft",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        native_unit_of_measurement=UnitOfPressure.KPA,
        imperial_unit_of_measurement=UnitOfPressure.PSI,
        to_native_conversion=lambda v: PressureConverter.convert(
            v, UnitOfPressure.PSI, UnitOfPressure.KPA
        ),
        from_native_conversion=lambda v: PressureConverter.convert(
            v, UnitOfPressure.KPA, UnitOfPressure.PSI
        ),
    ),
    SmartcarSensorDescription(
        key=EntityDescriptionKey.TIRE_PRESSURE_FRONT_RIGHT,
        name="Tire Pressure Front Right",
        value_key_path="tires_pressure.frontRight",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        native_unit_of_measurement=UnitOfPressure.KPA,
        imperial_unit_of_measurement=UnitOfPressure.PSI,
        to_native_conversion=lambda v: PressureConverter.convert(
            v, UnitOfPressure.PSI, UnitOfPressure.KPA
        ),
        from_native_conversion=lambda v: PressureConverter.convert(
            v, UnitOfPressure.KPA, UnitOfPressure.PSI
        ),
    ),
)


async def async_setup_entry(  # noqa: RUF029
    hass: HomeAssistant,  # noqa: ARG001
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from coordinator."""
    coordinators: dict[str, SmartcarVehicleCoordinator] = (
        entry.runtime_data.coordinators
    )
    _LOGGER.debug("Setting up sensors for VINs: %s", list(coordinators.keys()))
    entities: list[SmartcarSensor] = [
        SmartcarSensor(coordinator, description)
        for coordinator in coordinators.values()
        for description in SENSOR_TYPES
        if coordinator.is_scope_enabled(description.key, verbose=True)
    ]
    _LOGGER.info("Adding %s Smartcar sensor entities", len(entities))
    async_add_entities(entities)


class SmartcarSensor[ValueT, RawValueT](
    SmartcarEntity[ValueT, RawValueT], SensorEntity
):
    """Sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SmartcarVehicleCoordinator,
        description: SmartcarSensorDescription,
    ) -> None:
        super().__init__(coordinator, description)
        self.entity_description: SmartcarSensorDescription = description

        self._use_imperial = coordinator.config_entry.data.get(CONF_USE_IMPERIAL, False)

        if self._use_imperial and description.imperial_unit_of_measurement:
            self._attr_native_unit_of_measurement = (
                description.imperial_unit_of_measurement
            )
        else:
            self._attr_native_unit_of_measurement = (
                description.native_unit_of_measurement
            )

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        return self._extract_value()

    def _extract_value(self) -> ValueT | None:
        value = self._extract_raw_value()

        if value is None:
            return None

        if self._use_imperial and self.entity_description.from_native_conversion:
            return self.entity_description.from_native_conversion(value)
        if not self._use_imperial and self.entity_description.to_native_conversion:
            return self.entity_description.to_native_conversion(value)

        return value
