import logging
import datetime
import math

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
        _LOGGER.info(f"==================== 센서 업데이트 시작 ====================")

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
            _LOGGER.info(f"==================== 센서 업데이트 종료 ====================")

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

        # 정상 데이터가 수신될 때 이번달 전기 사용량 보관용 변수
        self._previous_electricity_usage_this_month = None
        self._previous_electricity_this_month = None

        # 정상 데이터가 수실될 때 지난달 전기 사용량 보관용 변수
        self._previous_electricity_usage_last_month = None
        self._previous_electricity_last_month = None

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
        _LOGGER.debug(f"========== 센서 상태 변경({self._sensor_type}) ==========")


        

        # 각 유틸리티별 현재 사용량과 지난달 사용량 비교
        current_usage = None
        
        
        try:
            # coordinator.data가 None이거나 빈 딕셔너리인 경우 처리
            if not self.coordinator.data:
                if self._sensor_type == "energy":
                    # energy 센서는 현재 시간을 계속 표시
                    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return "unavailable" # 오류 발생 시 unavailable 반환
            
            if self._sensor_type == "energy":
                return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 전기 센서인 경우 데이터 검증
            if self._sensor_type == "electricity":
                current_usage = self.coordinator.data.get("electricity_usage_this_month")
                this_month = self.coordinator.data.get("this_month")
                
                _LOGGER.debug(f"이번달({this_month}) 전기 사용량 : {current_usage}")
                _LOGGER.debug(f"이전 응답 지난달 전기 사용량 : {self._previous_electricity_usage_last_month}, 이전 응답 지난달 : {self._previous_electricity_last_month}")

                if (self._previous_electricity_usage_last_month is not None and 
                    self._previous_electricity_last_month is not None and 
                    current_usage is not None and 
                    this_month is not None):
                    
                    # 같은 달의 데이터인 경우에만 비교 (정상적으로 월이 변경되어 전기 사용량이 0으로 초기화 되는 경우 제외)
                    if this_month == self._previous_electricity_this_month:
                        
                        # 현재 사용량과 지난달 사용량이 동일할 경우 비정상 데이터 처리
                        if math.isclose(current_usage, self._previous_electricity_usage_last_month):
                            _LOGGER.warning(
                                f"전기 이번달 사용량이 이전 응답의 지난달 사용량과 동일함 "
                                f"(이번달({this_month}): 전기 사용량 {current_usage}, 이전에 호출된 지난달 사용량: {self._previous_electricity_usage_last_month})"
                            )

                            # 비정상 일 경우 데이터 처리 중단
                            return "unknown"
                
                # 정상 데이터면 지난달 전기 사용량과 월 정보 저장
                self._previous_electricity_usage_last_month = self.coordinator.data.get("electricity_usage_last_month")
                self._previous_electricity_last_month = self.coordinator.data.get("last_month")
                
                # 정상 데이터면 이번달 전기 사용량을 보관
                self._previous_electricity_usage_this_month = current_usage
                self._previous_electricity_this_month = this_month

                return current_usage
            
            elif self._sensor_type == "gas":
                current_usage = self.coordinator.data.get("gas_usage_this_month")
                _LOGGER.debug(f"이번달 가스 사용량 : {current_usage}")
            elif self._sensor_type == "water":
                current_usage = self.coordinator.data.get("water_usage_this_month")
                _LOGGER.debug(f"이번달 수도 사용량 : {current_usage}")
            elif self._sensor_type == "hot_water":
                current_usage = self.coordinator.data.get("hot_water_usage_this_month")
                _LOGGER.debug(f"이번달 온수 사용량 : {current_usage}")
            elif self._sensor_type == "heating":
                current_usage = self.coordinator.data.get("heating_usage_this_month")
                _LOGGER.debug(f"이번달 난방 사용량 : {current_usage}")
        except Exception as e:
            _LOGGER.error(f"{self._sensor_type} 센서 데이터 처리 중 오류 발생: {e}")
            return "unknown"
        
        # 현재 사용량이 None이면 unknown 반환
        if current_usage is None:
            return "unknown"
            
        return current_usage

    @property
    def state_attributes(self):
        if self._sensor_type == "energy":
            # 전체 응답 데이터를 속성값으로 할당
            return self.coordinator.data
        return {}
