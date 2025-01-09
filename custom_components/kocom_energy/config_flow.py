import voluptuous as vol
import logging
import aiohttp
import async_timeout
import asyncio
import re
from homeassistant import config_entries
from .const import DOMAIN, PLATFORMS
from .exceptions import IpAddressNotFoundError
from .api import API
from .util import string_to_padded_hex, md5_hashing, hex_to_ascii

_LOGGER = logging.getLogger(__name__)

class KocomEnergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input=None):
        _LOGGER.debug("Config Flow Step ::: async_step_user")
        errors = {}
    
        if user_input is not None:
            try:
                # http 요청으로 IP 얻기
                async with aiohttp.ClientSession() as session, \
                        async_timeout.timeout(10):
                    resp = await session.get(f"http://221.141.3.28/SvrInfo.php?uid={user_input['username']}")
                    resp.raise_for_status()
                    response_text = await resp.text()

                    # IP 주소 추출
                    ip_address_match = re.search(r'3 => ([\d\.]+)', response_text)
                    if not ip_address_match:
                        raise IpAddressNotFoundError("IP address not found in the response")
                    ip_address = ip_address_match.group(1)
                    
                    # IP 얻기 성공 -> account step으로 이동
                    return self.async_show_form(
                        step_id="account",
                        data_schema=vol.Schema({
                            vol.Required("ip", default=ip_address): str,
                            vol.Required("username", default=user_input["username"]): str,
                            vol.Required("password"): str,
                            # vol.Optional("phone"): str,
                            vol.Required("update_interval", default=3600): vol.In({
                                # 60    : "1분",
                                # 180   : "3분",
                                300   : "5분",
                                3600  : "1시간",
                                86400 : "일"
                            })
                        })
                    )

            except aiohttp.ClientError:
                _LOGGER.error("서버 접속 실패")
                errors["base"] = "cannot_connect"
            except asyncio.TimeoutError:
                _LOGGER.error("서버 타임아웃")
                errors["base"] = "timeout"
            except IpAddressNotFoundError:
                _LOGGER.error("IP 정보를 찾을 수 없음")
                errors["base"] = "ip_not_found"
            except Exception as e:
                _LOGGER.error("서버 IP 확인 중 알 수 없는 오류 : %s", e)
                errors["base"] = "unknown_error"
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("username"): str,
            }),
            errors=errors
        )

    async def async_step_account(self, user_input=None):
        _LOGGER.debug("Config Flow Step ::: async_step_account")

        errors = {}

        if user_input is not None:
            _LOGGER.debug(f"user_input 정보 : {user_input}")
            transformed_input = {
                "ip"          : user_input["ip"],
                "username"    : string_to_padded_hex(md5_hashing(user_input["username"]), 80),      # md5 해싱 후 hex 변환
                "password"    : string_to_padded_hex(md5_hashing(user_input["password"]), 80),      # md5 해싱 후 hex 변환
                "fcm"         : string_to_padded_hex('', 512),                                      # 모바일 환경의 경우 fcm 값 전달함
                "phone"       : string_to_padded_hex('', 32),                                       # 전화번호 필수 값 아님
            }
            
            # 인증 확인
            api = API(**transformed_input)
            authenticated = await api.authenticate()

            if authenticated:
                # 인증될 경우
                return self.async_create_entry(
                    title = f'사용자({user_input["username"]})',
                    data = {
                        **transformed_input, 
                        "update_interval": user_input["update_interval"],
                        "original_username": user_input["username"]  # 원래 username 저장
                    }
                )
            else:
                errors["base"] = "auth_error"

        return self.async_show_form(
            step_id="account",
            data_schema=vol.Schema({
                vol.Required("ip", default=user_input["ip"]): str,
                vol.Required("username", default=user_input["username"]): str,
                vol.Required("password"): str,
                # vol.Optional("phone"): str,
                vol.Required("update_interval", default=user_input["update_interval"]): vol.In({
                    # 60     : "1분",
                    # 180    : "3분",
                    300    : "5분",
                    3600   : "1시간",
                    86400  : "일"
                })
            }),
            errors=errors
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """옵션 플로우 클래스 반환"""
        return KocomEnergyOptionsFlow(config_entry)

    async def async_step_reauth(self, user_input=None):
        """재인증 처리"""
        return await self.async_step_account()

class KocomEnergyOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""

        # FIXME: 수정중
        # Detected that custom integration 'kocom_energy' sets option flow config_entry explicitly, 
        # which is deprecated at custom_components/kocom_energy/config_flow.py, 
        # line 137: self.config_entry = config_entry. 
        # This will stop working in Home Assistant 2025.12, please report it to the author of the 'kocom_energy' custom integration
        self._config_entry = config_entry  # config_entry를 protected 멤버로 저장

    async def async_step_init(self, user_input=None):
        """옵션 설정 폼 표시"""
        errors = {}

        if user_input is not None:
            try:
                # 인증 확인
                transformed_input = {
                    "ip": self._config_entry.data["ip"],  # self.config_entry 대신 self._config_entry 사용
                    "username": string_to_padded_hex(md5_hashing(user_input["username"]), 80),
                    "password": string_to_padded_hex(md5_hashing(user_input["password"]), 80),
                    "fcm": string_to_padded_hex('', 512),
                    "phone": string_to_padded_hex('', 32),
                }
                
                api = API(**transformed_input)
                authenticated = await api.authenticate()

                if authenticated:
                    # 인증 성공 시 설정 업데이트
                    self.hass.config_entries.async_update_entry(
                        self._config_entry,  # self.config_entry 대신 self._config_entry 사용
                        data={
                            **self._config_entry.data,  # self.config_entry 대신 self._config_entry 사용
                            **transformed_input,
                            "original_username": user_input["username"]
                        }
                    )
                    # options로 update_interval 반환
                    return self.async_create_entry(
                        title="",
                        data={"update_interval": user_input["update_interval"]}
                    )
                else:
                    errors["base"] = "auth_error"
            except Exception as e:
                _LOGGER.error("설정 업데이트 중 오류 발생: %s", e)
                errors["base"] = "unknown_error"

        # 기본값 설정
        default_username = self._config_entry.data.get("original_username", "")  # self.config_entry 대신 self._config_entry 사용
        default_interval = self._config_entry.data.get("update_interval", 3600)  # self.config_entry 대신 self._config_entry 사용

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("username", default=default_username): str,
                vol.Required("password"): str,
                vol.Required("update_interval", default=default_interval): vol.In({
                    300: "5분",
                    3600: "1시간",
                    86400: "일"
                })
            }),
            errors=errors
        )


