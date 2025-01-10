import logging
import datetime

from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.components.sensor import SensorEntity
from datetime import timedelta

from .const import DOMAIN, DEVICE_ID
from .api import API

_LOGGER = logging.getLogger(__name__)


SENSOR_TYPES = {
    "energy": {
        "name": "Kocom Energy Usage", 
        "device_class": "", 
        "unit_of_measurement": "",
        "state_class": "measurement",
        "icon": "mdi:api"
    },
    "electricity": {
        "name": "Kocom Electricity Usage", 
        "device_class": "energy", 
        "unit_of_measurement": "kWh",
        "state_class": "total_increasing",
        "icon": "mdi:flash"
    },
    "gas": {
        "name": "Kocom Gas Usage", 
        "device_class": "gas", 
        "unit_of_measurement": "m³",
        "state_class": "total_increasing",
        "icon": "mdi:fire"
    },
    "water": {
        "name": "Kocom Water Usage", 
        "device_class": "water", 
        "unit_of_measurement": "m³",
        "state_class": "total_increasing",
        "icon": "mdi:water"
    },
    "hot_water": {
        "name": "Kocom Hot Water Usage", 
        "device_class": "", 
        "unit_of_measurement": "",
        "state_class": "total_increasing",
        "icon": "mdi:water-boiler"
    },
    "heating": {
        "name": "Kocom Heating Usage", 
        "device_class": "", 
        "unit_of_measurement": "",
        "state_class": "total_increasing",
        "icon": "mdi:radiator"
    }
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
        sensors.append(KocomEnergySensor(coordinator, entry, sensor_type, sensor_data))

    async_add_entities(sensors)


class KocomEnergySensor(CoordinatorEntity, SensorEntity):
    """Kocom Energy Sensor using DataUpdateCoordinator."""

    def __init__(self, coordinator, entry, sensor_type, sensor_data):
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._entry = entry
        self._sensor_type = sensor_type
        self._name = sensor_data["name"]
        self._entry_id = f"{DOMAIN}.{entry.data.get('username')}_{self._name.lower().replace(' ', '_')}"
        self._unique_id = f"{DOMAIN}.{entry.data.get('username')}_{self._name.lower().replace(' ', '_')}"
        self._device_class = sensor_data["device_class"]
        self._unit_of_measurement = sensor_data["unit_of_measurement"]
        self._state_class = sensor_data["state_class"]
        self._icon = sensor_data["icon"]

        self._device_info = {
            "identifiers": {(DOMAIN, DEVICE_ID)},
            "name": "코콤 에너지",
            "model": "Kocom Energy"
        }

        self._previous_value = None  # 이전 값 저장용 변수 추가

    @property
    def device_info(self):
        _LOGGER.debug(f"Device ID : {DEVICE_ID}")
        return self._device_info

    # @property
    # def entity_id(self):
    #     username = self._entry.data.get("username")
    #     return f"{DOMAIN}.{username}_{self._name.lower().replace(' ', '_')}"

    @property
    def entry_id(self):
        return self._entry_id

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def device_class(self):
        return self._device_class

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def state_class(self):
        return self._state_class

    @property
    def state(self):
        if self._sensor_type == "energy":
            # 상태값을 현재시간으로 설정
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 각 유틸리티별 현재 사용량과 이전달 사용량 비교
        current_usage = None
        last_month_usage = None
        
        try:
            if self._sensor_type == "electricity":
                current_usage = self.coordinator.data.get("electricity_usage_this_month")
                last_month_usage = self.coordinator.data.get("electricity_usage_last_month")
            elif self._sensor_type == "gas":
                current_usage = self.coordinator.data.get("gas_usage_this_month")
                last_month_usage = self.coordinator.data.get("gas_usage_last_month")
            elif self._sensor_type == "water":
                current_usage = self.coordinator.data.get("water_usage_this_month")
                last_month_usage = self.coordinator.data.get("water_usage_last_month")
            elif self._sensor_type == "hot_water":
                current_usage = self.coordinator.data.get("hot_water_usage_this_month")
                last_month_usage = self.coordinator.data.get("hot_water_usage_last_month")
            elif self._sensor_type == "heating":
                current_usage = self.coordinator.data.get("heating_usage_this_month")
                last_month_usage = self.coordinator.data.get("heating_usage_last_month")
        except Exception as e:
            _LOGGER.error(f"{self._sensor_type} 센서 데이터 처리 중 오류 발생: {e}")
            return "unknown"
        
        # 현재 사용량이 None이면 unknown 반환
        if current_usage is None:
            return "unknown"
            
        # 현재 사용량이 0이면 그대로 반영
        if current_usage == 0:
            self._previous_value = current_usage
            return current_usage
            
        # 이상치가 발생하는 패턴 : 이전달의 사용량이 이번달 사용량으로 응답데이터로 조회 됨
        if current_usage == last_month_usage:
            _LOGGER.warning(
                f"{self._sensor_type} 현재 사용량이 이전달과 동일합니다. 이전 상태값 유지 (현재: {current_usage}, 이전달: {last_month_usage})"
            )
            return self._previous_value if self._previous_value is not None else "unknown"
        
        # 정상적인 경우 현재 값을 저장하고 반환
        self._previous_value = current_usage
        return current_usage

    @property
    def state_attributes(self):
        if self._sensor_type == "energy":
            # 전체 응답 데이터를 속성값으로 할당
            return self.coordinator.data
        return {}
