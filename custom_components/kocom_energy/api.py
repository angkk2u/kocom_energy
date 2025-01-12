import datetime
import asyncio
import logging

from dateutil.relativedelta import relativedelta
from .util import string_to_padded_hex, string_to_hex, hex_to_ascii, hex_to_double
from .exceptions import AuthenticationError


_LOGGER = logging.getLogger(__name__)

class API:

    # 인증관련 패킷
    auth_req_format = "78563412000010017c01000000000000000000000000000000000000000000000000000000000000000000000000000000000000{username}{password}02000000{fcm}{phone}"
    auth_req = ""
    auth_resp_checker = "7856341201001001040000000000000000000000000000000000000000000000"

    # 메뉴 관련 패킷
    menu_req = "78563412b80b1001040000000000000000000000000000000000000000000000"

    # 주소 관련 패킷
    addr_req = "785634120200100120000000000000000000000000000000000000000000000018000000f00000000000000000000000000000000000000000000000"

    # 에너지 관련 패킷
    energy_disp_type = ""
    energy_req_type_1_format = "785634127800100120000000{town}0000{dong}0000{ho}000000000000{months_str}000000000000000000000000"
    # energy_req_type_1_postfix = "000000000000000000000000"
    
    energy_req_type_3_format = "785634129001100148000000{town}0000{dong}0000{ho}000000000000020000000200000001000000{months_str}00{months_str}00312c322c332c342c350000000000000000000000"
    # energy_req_type_3_postfix = "312c322c332c342c350000000000000000000000"


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
                _LOGGER.error("인증 timeout")
                return {}

            if auth_response == self.auth_resp_checker:
                _LOGGER.debug("인증 성공")
                
                # 메뉴 정보 조회 패킷 전송
                _LOGGER.debug(f"메뉴 정보 조회 요청 패킷 : {self.menu_req}")
                writer.write(bytes.fromhex(self.menu_req))
                await writer.drain()
                
                # 메뉴 정보 조회 응답 대기 (10초 timeout 설정)
                try:
                    menu_response = (await asyncio.wait_for(reader.read(1024), timeout=10.0)).hex()
                    _LOGGER.debug(f'메뉴 정보 응답 패킷: {menu_response}')
                    _LOGGER.debug(f'에너지 조회 유형 : {menu_response[96:100]}')
                    
                    
                    """# 에너지 조회 유형 세팅 (energyInfo.class)
                    
                    0100 인 경우
                    |항목|전전달|지난달|이번달|
                    |---|----|-----|----|
                    전기    -
                    가스    -
                    수도    -
                    온수    -
                    난방    -

                    0200 인 경우 아직 미식별됨 (항목을 제외한 열이 4개)

                    0300 1, 2 두가지 유형이 있으나 1번만 처리
                    |항목|사용량|증감|
                    |---|----|---|
                    전기    -
                    수도    -
                    온수    -
                    가스    -
                    난방    -

                    """
                    self.energy_disp_type = menu_response[96:100]
                except asyncio.TimeoutError:
                    _LOGGER.debug("주소 조회 요청 timeout")
                    return
                
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
                except asyncio.TimeoutError:
                    _LOGGER.debug("주소 조회 요청 timeout")
                    return

                # 에너지 조회 패킷 전송
                energy_req_data = ""

                if self.energy_disp_type == '0100':
                    ########## 에너지 요청 데이터 가공 ##########
                    now = datetime.datetime.now()

                    # 이전 달
                    one_month_ago = now - relativedelta(months=1)

                    # 그 이전 달
                    two_months_ago = now - relativedelta(months=2)

                    months = [
                        two_months_ago.strftime("%Y%m"),
                        one_month_ago.strftime("%Y%m"),
                        now.strftime("%Y%m"),
                    ]
                    months_str = ",".join(months)
                    
                    energy_req_data = self.energy_req_type_1_format.format(town=addr_response[24:28], dong=addr_response[32:36], ho=addr_response[40:44], months_str=string_to_hex(months_str))
                    
                elif self.energy_disp_type == '0300':
                    ########## 에너지 요청 데이터 가공 ##########
                    months_str = datetime.datetime.now().strftime("%Y-%m-00 00:00:00")

                    energy_req_data = self.energy_req_type_3_format.format(town=addr_response[24:28], dong=addr_response[32:36], ho=addr_response[40:44], months_str=string_to_hex(months_str))

                _LOGGER.debug(f"에너지 정보 요청 패킷 : {energy_req_data}")
                writer.write(bytes.fromhex(energy_req_data))
                await writer.drain()

                # 조회 응답 대기 (10초 timeout 설정)
                try:
                    gnergy_response = (await asyncio.wait_for(reader.read(1024), timeout=10.0)).hex()
                    _LOGGER.debug(f'에너지 정보 수신 패킷: {gnergy_response}')

                    # 에너지 정보 수신 패킷 검증
                    if len(gnergy_response) < 500:  # 정상적인 응답 패킷 길이보다 짧은 경우
                        _LOGGER.error(f"비정상 응답 데이터 수신. 응답 길이: {len(gnergy_response)}")
                        return None

                    # 응답 헤더 검증 (첫 10자리)    
                    if gnergy_response.startswith("7856341210"):
                        _LOGGER.error(f"잘못된 응답 헤더: {gnergy_response[:10]}")
                        return None

                    if self.energy_disp_type == '0100':
                        ########## 전전달 에너지 사용량 ##########
                        _LOGGER.debug(f"에너지 사용량 조회 패턴 : {self.energy_disp_type}")
                        # 전기
                        start_idx = 64
                        response_ym = hex_to_ascii(gnergy_response[start_idx + 8 : start_idx + 24])
                        _LOGGER.debug(f"전전달 조회 년월 : {response_ym}, raw_data : {gnergy_response[start_idx + 8 : start_idx + 24]}")
                        usage = hex_to_double(gnergy_response[start_idx + 40 : start_idx + 56])
                        _LOGGER.debug(f"전전달 전기 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 40 : start_idx + 56]}")
                        energy_response_dict["two_months_ago"] = response_ym
                        energy_response_dict["electricity_usage_two_months_ago"] = usage

                        # 가스
                        start_idx = 120
                        usage = hex_to_double(gnergy_response[start_idx + 40 : start_idx + 56])
                        _LOGGER.debug(f"전전달 가스 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 40 : start_idx + 56]}")
                        energy_response_dict["gas_usage_two_months_ago"] = usage

                        # 수도
                        start_idx = 176
                        usage = hex_to_double(gnergy_response[start_idx + 40 : start_idx + 56])
                        _LOGGER.debug(f"전전달 수도 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 40 : start_idx + 56]}")
                        energy_response_dict["water_usage_two_months_ago"] = usage

                        # 온수
                        start_idx = 232
                        usage = hex_to_double(gnergy_response[start_idx + 40 : start_idx + 56])
                        _LOGGER.debug(f"전전달 온수 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 40 : start_idx + 56]}")
                        energy_response_dict["hot_water_usage_two_months_ago"] = usage

                        # 난방
                        start_idx = 288
                        usage = hex_to_double(gnergy_response[start_idx + 40 : start_idx + 56])
                        _LOGGER.debug(f"전전달 난방 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 40 : start_idx + 56]}")
                        energy_response_dict["heating_usage_two_months_ago"] = usage

                        ########## 지난달 에너지 사용량 ##########
                        
                        # 전기
                        start_idx = 344
                        response_ym = hex_to_ascii(gnergy_response[start_idx + 8 : start_idx + 24])
                        _LOGGER.debug(f"지난달 조회 년월 : {response_ym}, raw_data : {gnergy_response[start_idx + 8 : start_idx + 24]}")
                        usage = hex_to_double(gnergy_response[start_idx + 40 : start_idx + 56])
                        _LOGGER.debug(f"지난달 전기 사용량 : {usage}, raw : {gnergy_response[start_idx + 40 : start_idx + 56]}")
                        energy_response_dict["last_month"] = response_ym
                        energy_response_dict["electricity_usage_last_month"] = usage

                        # 가스
                        start_idx = 400
                        usage = hex_to_double(gnergy_response[start_idx + 40 : start_idx + 56])
                        _LOGGER.debug(f"지난달 가스 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 40 : start_idx + 56]}")
                        energy_response_dict["gas_usage_last_month"] = usage

                        # 수도
                        start_idx = 456
                        usage = hex_to_double(gnergy_response[start_idx + 40 : start_idx + 56])
                        _LOGGER.debug(f"지난달 수도 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 40 : start_idx + 56]}")
                        energy_response_dict["water_usage_last_month"] = usage

                        # 온수
                        start_idx = 512
                        usage = hex_to_double(gnergy_response[start_idx + 40 : start_idx + 56])
                        _LOGGER.debug(f"지난달 온수 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 40 : start_idx + 56]}")
                        energy_response_dict["hot_water_usage_last_month"] = usage

                        # 난방
                        start_idx = 568
                        usage = hex_to_double(gnergy_response[start_idx + 40 : start_idx + 56])
                        _LOGGER.debug(f"지난달 난방 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 40 : start_idx + 56]}")
                        energy_response_dict["heating_usage_last_month"] = usage

                        ########## 이번달 에너지 사용량 ##########
                        
                        # 전기
                        start_idx = 624
                        response_ym = hex_to_ascii(gnergy_response[start_idx + 8 : start_idx + 24])
                        _LOGGER.debug(f"이번달 조회 년월 : {response_ym}, raw_data : {gnergy_response[start_idx + 8 : start_idx + 24]}   ")
                        usage = hex_to_double(gnergy_response[start_idx + 40 : start_idx + 56])
                        _LOGGER.debug(f"이번달 전기 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 40 : start_idx + 56]}")
                        energy_response_dict["this_month"] = response_ym
                        energy_response_dict["electricity_usage_this_month"] = usage

                        # 가스
                        start_idx = 680
                        usage = hex_to_double(gnergy_response[start_idx + 40 : start_idx + 56])
                        _LOGGER.debug(f"이번달 가스 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 40 : start_idx + 56]}")
                        energy_response_dict["gas_usage_this_month"] = usage

                        # 수도
                        start_idx = 736
                        usage = hex_to_double(gnergy_response[start_idx + 40 : start_idx + 56])
                        _LOGGER.debug(f"이번달 수도 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 40 : start_idx + 56]}")
                        energy_response_dict["water_usage_this_month"] = usage

                        # 온수
                        start_idx = 792
                        usage = hex_to_double(gnergy_response[start_idx + 40 : start_idx + 56])
                        _LOGGER.debug(f"이번달 온수 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 40 : start_idx + 56]}")
                        energy_response_dict["hot_water_usage_this_month"] = usage

                        # 난방
                        start_idx = 848
                        usage = hex_to_double(gnergy_response[start_idx + 40 : start_idx + 56])
                        _LOGGER.debug(f"이번달 난방 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 40 : start_idx + 56]}")
                        energy_response_dict["heating_usage_this_month"] = usage
                    
                    elif self.energy_disp_type == '0300':
                        _LOGGER.debug(f"에너지 사용량 조회 패턴 : {self.energy_disp_type}")
                        # 전기
                        start_idx = 184
                        response_ym = hex_to_ascii(gnergy_response[start_idx + 8 : start_idx + 22])
                        _LOGGER.debug(f"이번달 조회 년월 : {response_ym}, raw_data   : {gnergy_response[start_idx + 8 : start_idx + 22]}")
                        usage = hex_to_double(gnergy_response[start_idx + 48 : start_idx + 64])
                        _LOGGER.debug(f"이번달 전기 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 48 : start_idx + 64]}")
                        energy_response_dict["this_month"] = response_ym
                        energy_response_dict["electricity_usage_this_month"] = usage

                        # 수도
                        start_idx = 272
                        usage = hex_to_double(gnergy_response[start_idx + 48 : start_idx + 64])
                        _LOGGER.debug(f"이번달 수도 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 48 : start_idx + 64]}")
                        energy_response_dict["water_usage_this_month"] = usage

                        # 온수
                        start_idx = 360
                        usage = hex_to_double(gnergy_response[start_idx + 48 : start_idx + 64])
                        _LOGGER.debug(f"이번달 온수 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 48 : start_idx + 64]}")
                        energy_response_dict["hot_water_usage_this_month"] = usage

                        # 가스
                        start_idx = 448
                        usage = hex_to_double(gnergy_response[start_idx + 48 : start_idx + 64])
                        _LOGGER.debug(f"이번달 가스 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 48 : start_idx + 64]}")
                        energy_response_dict["gas_usage_this_month"] = usage

                        # 난방
                        start_idx = 536
                        usage = hex_to_double(gnergy_response[start_idx + 48 : start_idx + 64])
                        _LOGGER.debug(f"이번달 난방 사용량 : {usage}, raw_data : {gnergy_response[start_idx + 48 : start_idx + 64]}")
                        energy_response_dict["heating_usage_this_month"] = usage



                except asyncio.TimeoutError:
                    _LOGGER.error("Query response timeout")
                    return {}
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

