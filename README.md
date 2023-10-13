# 코콤 에너지 컴포넌트

이 프로젝트는 코콤 홈매니저 앱의 에너지 사용량 조회를 Home Assistant(이하 HA)에 연동하기 위한 통합구성요소 입니다.

---

## 🚀 Features

- 코콤 앱에서 에너지 사용량 조회 데이터를 HA 센서로 수집
- 사용자 선택에 따라 사용량 데이터 갱신

## 🛠 Installation

1. HACS 설치
- HACS 메뉴 > Custom repositories 이동
- Repositories : https://github.com/angkk2u/kocom_energy 입력, Category : Integration 입력 > ADD
- 통합구성요소 메뉴 이동 후 추가하기 버튼 클릭
- kocom energy 검색 후 설치

2. 직접 설치
- https://github.com/angkk2u/kocom_energy 저장소에서 다운로드 받은 파일을 HA config/custom_components/kocom_energy 폴더에 붙여넣기
- HA 재시작

## 🔧 Configuration

### 통합구성요소 설정
- 코콤 앱에서 사용하는 ID 입력
- 사용중인 ID를 기반으로 서버 확인
- 코콤 앱에서 사용하는 비밀번호 입력
- 코콤 앱 인증 확인 후 컴포넌트 설치 완료


## 📝 Usage

- 통합 구성요소 설정 후 4개의 센서가 추가되고 사용자가 설정한 주기에 맞춰 사용량 갱신
  - Kocom Energy Usage
  - Kocom Eletricity Usage
  - Kocom Gas Usage
  - Kocom Water Usage

## 📜 License

This project is licensed under the [Apache-2.0 license](LICENSE).

