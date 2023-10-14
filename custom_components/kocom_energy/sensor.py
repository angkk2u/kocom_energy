import logging
import datetime

from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.components.sensor import SensorEntity
from datetime import timedelta

from .const import DOMAIN
from .api import API

_LOGGER = logging.getLogger(__name__)


SENSOR_TYPES = {
    "energy": {"name": "Kocom Energy Usage", "icon": "mdi:api"},
    "electricity": {"name": "Kocom Electricity Usage", "icon": "mdi:flash"},
    "gas": {"name": "Kocom Gas Usage", "icon": "mdi:fire"},
    "water": {"name": "Kocom Water Usage", "icon": "mdi:water"},
    "hot_water": {"name": "Kocom Hot Water Usage", "icon": "mdi:water-boiler"},
    "heating": {"name": "Kocom Heating Usage", "icon": "mdi:radiator"}
}

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the KocomEnergySensor from a config entry."""
    _LOGGER.debug(f"Entry Data : {entry.data}")



    update_interval = entry.data.get("update_interval")

    async def async_update_kocom_energy():
        _LOGGER.info(f"========== 센서 업데이트 시작 ==========")

        try:
            # 코콤 데이터 API 생성
            api = API(
                ip=entry.data.get("ip"),
                username=entry.data.get("username"),
                password=entry.data.get("password"),
                fcm=entry.data.get("fcm"),
                phone=entry.data.get("phone"),
            )
            
            energy_response_dict = await api.get_energy_data()

            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            _LOGGER.info("Updating sensor, State: %s", now)
            _LOGGER.info("Updating sensor, Attributes: %s", energy_response_dict)
            _LOGGER.info(f"========== 센서 업데이트 종료 ==========")

            return energy_response_dict

        except Exception as e:
            _LOGGER.error("센서 업데이트 오류: %s", e)

    # Create the coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="sensor",
        update_method   = async_update_kocom_energy,            # 코콤 에너지 조회 API
        update_interval = timedelta(seconds=update_interval)    # 사용자 정의 갱신 주기
    )

    # Fetch initial data
    # 데이터 갱신 시 사용하지만 오류 발생하더라도 예외 발생하지 않고 통합구성요소 설치 완료 됨
    # await coordinator.async_refresh()
    # 통합구성 요소가 처음 설정될 때 사용하며 실패할 경우 통합구성 요소의 설정을 중단
    await coordinator.async_config_entry_first_refresh()

    # 나중에 switch 등 다른 플랫폼을 사용할 경우 객체 공유 목적으로 사용
    # hass.data[DOMAIN][entry.entry_id] = {
    #     "coordinator": coordinator
    # }

    sensors = []
    for sensor_type, sensor_data in SENSOR_TYPES.items():
        sensors.append(KocomEnergySensor(coordinator, sensor_type, sensor_data["name"], sensor_data["icon"]))

    async_add_entities(sensors)


class KocomEnergySensor(CoordinatorEntity, SensorEntity):
    """Kocom Energy Sensor using DataUpdateCoordinator."""

    def __init__(self, coordinator, sensor_type, name, icon):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._name = name
        self._icon = icon

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def state(self):
        if self._sensor_type == "energy":
            # 상태값을 현재시간으로 설정
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif self._sensor_type == "electricity":
            return self.coordinator.data.get("electricity_usage_this_month", "unknown")
        elif self._sensor_type == "gas":
            return self.coordinator.data.get("gas_usage_this_month", "unknown")
        elif self._sensor_type == "water":
            return self.coordinator.data.get("water_usage_this_month", "unknown")
        elif self._sensor_type == "hot_water":
            return self.coordinator.data.get("hot_water_usage_this_month", "unknown")
        elif self._sensor_type == "heating":
            return self.coordinator.data.get("heating_usage_this_month", "unknown")
        return "unknown"

    @property
    def state_attributes(self):
        if self._sensor_type == "energy":
            # 전체 응답 데이터를 속성값으로 할당
            return self.coordinator.data
        return {}
