# 코콤 에너지 컴포넌트

이 프로젝트는 코콤 홈매니저 앱의 에너지 사용량 조회를 Home Assistant(이하 HA)에 연동하기 위한 통합구성요소 입니다.

---

## 🚀 Features

- 코콤 앱에서 에너지 사용량 조회 데이터를 HA 센서로 수집
- 설정된 주기 따라 에너지 사용량 갱신

## 🛠 Installation

1. HACS 활용 설치 시
- HACS 메뉴 > Custom repositories 이동
- Repositories : https://github.com/angkk2u/kocom_energy 입력, Category : Integration 입력 > ADD > 코콤 에너지 사용량 
- 통합구성요소 메뉴 이동 후 "통합구성요소 추가하기" 버튼 클릭
- Kocom Energy Integration 검색 후 설치

2. 직접 설치 시
- https://github.com/angkk2u/kocom_energy 저장소에서 다운로드 받은 파일을 HA config/custom_components/kocom_energy 폴더에 붙여넣기
- HA 재시작
- 통합구성요소 메뉴 이동 후 "통합구성요소 추가하기" 버튼 클릭
- Kocom Energy Integration 검색 후 설치

## 🔧 Configuration

### 통합구성요소 설정
- 코콤 앱에서 사용하는 ID 입력
- 사용중인 ID를 기반으로 서버 확인(자동)
- 코콤 앱에서 사용하는 비밀번호 입력
- 코콤 앱 인증 확인 후 컴포넌트 설치 완료


## 📝 Usage

- 통합 구성요소 설정 후 4개의 센서가 추가되고 사용자가 설정한 주기에 맞춰 사용량 갱신
  - Kocom Energy Usage : 에너지 센서 갱신 시간(상태) 및 전체 데이터(속성)
  - Kocom Eletricity Usage : 전기 사용량 센서
  - Kocom Gas Usage : 가스 사용량 센서
  - Kocom Water Usage : 수도 사용량 센서
  - Kocom Hot Water Usage : 온수 사용량 센서
  - Kocom Heating Usage : 난방 사용량 센서

## 📜 License

This project is licensed under the [Apache-2.0 license](LICENSE).

## History

- 1.0.4 : 설정 변경 지원
- 1.0.3 : hass.config_entries.async_forward_entry_setup 2025.6 버전에서 제거되는 변경사항 대응
- 1.0.2 : 날짜 계산 오류 수정. 에너지 조회 유형 1(전전달, 전달, 이번달) 만 해당하는 오류
- 1.0.1 : HA 공식 에너지 메뉴에 추가할 수 있도록 센서 device_class 속성 변경 (가스, 물 사용량)
- 1.0.0 : 전기요금 계산 센서 (https://github.com/dugurs/kwh_to_won) 와 연계 활용할 수 있도록 센서 속성 부여, 기기 및 구성요소 정보 추가
- 0.0.2 : 에너지 조회 유형(type3) 대응. 온수, 난방센서 추가
- 0.0.1 : 베타 테스트 최초 배포

