import datetime
import asyncio
import logging

from .util import string_to_padded_hex, string_to_hex, hex_to_ascii, hex_to_double
from .exceptions import AuthenticationError

_LOGGER = logging.getLogger(__name__)

class API:

    # 인증관련 패킷
    auth_req_format = "78563412000010017c01000000000000000000000000000000000000000000000000000000000000000000000000000000000000{username}{password}02000000{fcm}{phone}"
    auth_req = ""
    auth_resp_checker = "7856341201001001040000000000000000000000000000000000000000000000"

    # 주소 관련 패킷
    addr_req = "785634120200100120000000000000000000000000000000000000000000000018000000f00000000000000000000000000000000000000000000000"

    # 에너지 관련 패킷
    energy_req_prefix_format = "785634127800100120000000{town}0000{dong}0000{ho}000000000000"
    energy_req_prefix = ""
    energy_req_postfix = "000000000000000000000000"


    def __init__(self, ip, username, password, fcm, phone):
        self.ip = ip
        self.port = 15000
        self.username = username
        self.password = password
        self.fcm = fcm
        self.phone = phone

        # 인증 요청 패킷 조립
        self.auth_req = self.auth_req_format.format(username=self.username, password=self.password, fcm=self.fcm, phone=self.phone)
        _LOGGER.debug(f"인증 요청 패킷 조립 결과: {self.auth_req}")

    async def authenticate(self):

        try:
            _LOGGER.debug(f"========== 소켓 통신 시작 ==========")
            _LOGGER.debug(f"ip : {self.ip}")
            _LOGGER.debug(f"port : {self.port}")
            reader, writer = await asyncio.open_connection(self.ip, self.port)

            # 인증 정보 전송
            writer.write(bytes.fromhex(self.auth_req))
            await writer.drain()

            # 인증 응답 대기 (10초 timeout 설정)
            auth_response = (await asyncio.wait_for(reader.read(1024), timeout=10.0)).hex()
            _LOGGER.debug(f'인증 응답 패킷: {auth_response}')

            if auth_response == self.auth_resp_checker:
                _LOGGER.debug("인증 성공")
                return True

            _LOGGER.error(f'인증 실패, 요청 패킷 : {self.auth_req}')
            raise AuthenticationError("인증 정보가 올바르지 않습니다.")

        except asyncio.TimeoutError:
            _LOGGER.debug("인증 timeout")
        except Exception as e:
            _LOGGER.error("소켓 통신 오류: %s", e)
        finally:
            # 연결 종료
            writer.close()
            await writer.wait_closed()

        return False

    async def get_energy_data(self):
        
        try:
            energy_response_dict = {}

            _LOGGER.debug(f"========== 소켓 통신 시작 ==========")
            _LOGGER.debug(f"ip : {self.ip}")
            _LOGGER.debug(f"port : {self.port}")
            reader, writer = await asyncio.open_connection(self.ip, self.port)

            # 인증 정보 전송
            writer.write(bytes.fromhex(self.auth_req))
            await writer.drain()

            # 인증 응답 대기 (10초 timeout 설정)
            try:
                auth_response = (await asyncio.wait_for(reader.read(1024), timeout=10.0)).hex()
                _LOGGER.debug(f'인증 응답 패킷: {auth_response}')
            except asyncio.TimeoutError:
                _LOGGER.debug("인증 timeout")
                return

            if auth_response == self.auth_resp_checker:
                _LOGGER.debug("인증 성공")
                # 주소 조회 패킷 전송
                _LOGGER.debug(f"주소 조회 요청 패킷 : {self.addr_req}")
                writer.write(bytes.fromhex(self.addr_req))
                await writer.drain()

                # 주소 조회 응답 대기 (10초 timeout 설정)
                try:
                    addr_response = (await asyncio.wait_for(reader.read(1024), timeout=10.0)).hex()
                    _LOGGER.debug(f'주소 응답 패킷: {addr_response}')
                    _LOGGER.debug(f'타운: {addr_response[24:28]}')
                    _LOGGER.debug(f'동: {addr_response[32:36]}')
                    _LOGGER.debug(f'호: {addr_response[40:44]}')
                    # 주소정보 세팅
                    self.energy_req_prefix = self.energy_req_prefix_format.format(town=addr_response[24:28], dong=addr_response[32:36], ho=addr_response[40:44])
                except asyncio.TimeoutError:
                    _LOGGER.debug("주소 조회 요청 timeout")
                    return

                # 에너지 조회 패킷 전송
                
                ########## 에너지 요청 데이터 가공 ##########
                now = datetime.datetime.now()
                two_months_ago = now.replace(month=(now.month - 2) % 12 or 12)
                one_month_ago = now.replace(month=(now.month - 1) % 12 or 12)

                months = [
                    two_months_ago.strftime("%Y%m"),
                    one_month_ago.strftime("%Y%m"),
                    now.strftime("%Y%m"),
                ]
                months_str = ",".join(months)

                energy_req_data = (
                    self.energy_req_prefix + string_to_hex(months_str) + self.energy_req_postfix
                )

                _LOGGER.debug(f"에너지 정보 요청 패킷 : {energy_req_data}")
                writer.write(bytes.fromhex(energy_req_data))
                await writer.drain()

                # 조회 응답 대기 (10초 timeout 설정)
                try:
                    gnergy_response = (await asyncio.wait_for(reader.read(1024), timeout=10.0)).hex()
                    _LOGGER.debug(f'에너지 정보 수신 패킷: {gnergy_response}')

                    # 전전달 전기
                    start_idx = 72
                    response_ym = hex_to_ascii(gnergy_response[start_idx : start_idx + 16])
                    usage = hex_to_double(gnergy_response[start_idx + 32 : start_idx + 48])
                    energy_response_dict["two_months_ago"] = response_ym
                    energy_response_dict["electricity_usage_two_months_ago"] = usage

                    # 전전달 가스
                    start_idx = 128
                    response_ym = hex_to_ascii(gnergy_response[start_idx : start_idx + 16])
                    usage = hex_to_double(gnergy_response[start_idx + 32 : start_idx + 48])
                    energy_response_dict["gas_usage_two_months_ago"] = usage

                    # 전전달 수도
                    start_idx = 184
                    response_ym = hex_to_ascii(gnergy_response[start_idx : start_idx + 16])
                    usage = hex_to_double(gnergy_response[start_idx + 32 : start_idx + 48])
                    energy_response_dict["water_usage_two_months_ago"] = usage

                    # 지난달 전기
                    start_idx = 352
                    response_ym = hex_to_ascii(gnergy_response[start_idx : start_idx + 16])
                    usage = hex_to_double(gnergy_response[start_idx + 32 : start_idx + 48])
                    energy_response_dict["last_month"] = response_ym
                    energy_response_dict["electricity_usage_last_month"] = usage

                    # 지난달 가스
                    start_idx = 408
                    response_ym = hex_to_ascii(gnergy_response[start_idx : start_idx + 16])
                    usage = hex_to_double(gnergy_response[start_idx + 32 : start_idx + 48])
                    energy_response_dict["gas_usage_last_month"] = usage

                    # 지난달 수도
                    start_idx = 464
                    response_ym = hex_to_ascii(gnergy_response[start_idx : start_idx + 16])
                    usage = hex_to_double(gnergy_response[start_idx + 32 : start_idx + 48])
                    energy_response_dict["water_usage_last_month"] = usage

                    # 이번달 전기
                    start_idx = 632
                    response_ym = hex_to_ascii(gnergy_response[start_idx : start_idx + 16])
                    usage = hex_to_double(gnergy_response[start_idx + 32 : start_idx + 48])
                    energy_response_dict["this_month"] = response_ym
                    energy_response_dict["electricity_usage_this_month"] = usage

                    # 이번달 가스
                    start_idx = 700 - 12
                    response_ym = hex_to_ascii(gnergy_response[start_idx : start_idx + 16])
                    usage = hex_to_double(gnergy_response[start_idx + 32 : start_idx + 48])
                    energy_response_dict["gas_usage_this_month"] = usage

                    # 이번달 수도
                    start_idx = 757 - 13
                    response_ym = hex_to_ascii(gnergy_response[start_idx : start_idx + 16])
                    usage = hex_to_double(gnergy_response[start_idx + 32 : start_idx + 48])
                    energy_response_dict["water_usage_this_month"] = usage

                except asyncio.TimeoutError:
                    _LOGGER.debug("Query response timeout")
                    return
            else:
                _LOGGER.error(f"인증정보가 올바르지 않습니다.")


            _LOGGER.debug(f"========== 소켓 통신 종료 ==========")
            return energy_response_dict

        except Exception as e:
            _LOGGER.error("소켓 통신 오류: %s", e)
        finally:
            # 연결 종료
            writer.close()
            await writer.wait_closed()

