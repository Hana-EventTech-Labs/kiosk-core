# HiTi 프린터 SDK for Python

HiTi 프린터를 Python에서 쉽게 제어할 수 있는 SDK입니다. 이 SDK는 HiTi Roll Type Printer SDK를 래핑하여 GDI없이 명령어로 직접 프린터를 제어할 수 있도록 합니다. 특히 키오스크와 같은 응용 프로그램에 적합합니다.

## 주요 기능

- USB를 통한 HiTi 프린터 자동 검색
- 이미지 직접 인쇄 (GDI 사용하지 않음)
- 다양한 용지 크기 및 방향 지원
- 분할 인쇄 지원 (여러 이미지를 하나의 용지에 인쇄)
- 프린터 상태 모니터링
- 프린터 정보 조회
- 간편한 오류 처리

## 지원 모델

HiTi Roll Type Printer SDK를 지원하는 모든 프린터 모델:
- P510 series
- P710L
- P720L/P728L
- P52xL
- P52x
- P750L
- M610
- P910L
- 기타 드라이버 없이 USB를 통해 연결할 수 있는 모든 HiTi 모델

## 설치

### 요구 사항

- Python 3.6 이상
- Windows 운영 체제 (HiTi 프린터 드라이버 SDK 요구사항)
- PIL/Pillow (이미지 처리용)
- cffi (HiTi SDK DLL 접근용)

```bash
pip install pillow cffi
```

### 설치 방법

1. 이 저장소를 클론합니다:

```bash
git clone https://github.com/yourusername/hiti-python-sdk.git
cd hiti-python-sdk
```

2. 패키지를 설치합니다:

```bash
pip install -e .
```

또는 직접 소스 코드를 프로젝트에 복사하여 사용할 수도 있습니다.

### HiTi SDK DLL 준비

HiTi 공식 웹사이트에서 HiTi Roll Type Printer SDK를 다운로드하여 `HTRTAPI.dll` 파일을 확보해야 합니다. 이 파일은 다음 위치 중 하나에 배치해야 합니다:

- Python 스크립트와 같은 디렉토리
- `hiti_sdk` 패키지 디렉토리
- 시스템 경로 내 (`PATH` 환경 변수로 접근 가능한 위치)

## 빠른 시작

### 기본 사용법

```python
from hiti_sdk import HiTiPrinter, PaperType, Orientation

# 프린터 연결 (자동으로 첫 번째 발견된 프린터 사용)
printer = HiTiPrinter()

# 프린터 정보 확인
info = printer.get_device_info()
print(f"모델: {info['model_name']}, 리본: {info['ribbon_type_name']}")

# 이미지 인쇄
printer.print_image(
    image_path="path/to/photo.jpg",
    paper_type=PaperType.PHOTO_4X6,
    orientation=Orientation.PORTRAIT,
    copies=1
)
```

### 특정 프린터 사용

```python
# 특정 프린터 이름으로 연결
printer = HiTiPrinter(printer_name="\\?\\USB#VID_0CF6&PID_0009...")
```

### 분할 인쇄

```python
# 여러 이미지를 하나의 용지에 인쇄
printer.print_split_images(
    image_paths=["photo1.jpg", "photo2.jpg"],
    paper_type=PaperType.PHOTO_6X9_SPLIT_2UP,
    orientation=Orientation.PORTRAIT
)
```

### 프린터 상태 확인

```python
# 프린터 상태 확인
status, desc = printer.get_status()
print(f"프린터 상태: {desc}")

# 프린터가 준비될 때까지 대기
is_ready = printer.wait_until_ready(timeout=30)
if is_ready:
    print("프린터 준비 완료")
else:
    print("프린터 준비 안됨")
```

## 예제 코드

더 많은 예제는 `examples` 디렉토리를 참조하세요:

- `examples/kiosk_print.py`: 키오스크 응용을 위한 기본 예제
- `examples/batch_print.py`: 여러 이미지를 일괄 인쇄하는 예제
- `examples/split_print.py`: 분할 인쇄 예제

## API 레퍼런스

### 주요 클래스

- `HiTiPrinter`: 프린터 제어를 위한 기본 클래스
- `HiTiDevice`: 저수준 디바이스 인터페이스 클래스
- `ImageData`: 이미지 데이터 처리 클래스

### 상수 및 열거형

- `PaperType`: 용지 유형 상수
- `Orientation`: 인쇄 방향 상수
- `PrintMode`: 인쇄 품질 모드 상수
- `PrinterStatus`: 프린터 상태 코드
- `DeviceStatus`: 디바이스 상태 코드
- `RibbonType`: 리본 유형 상수

### 예외 클래스

- `PrinterError`: 기본 예외 클래스
- `ConnectionError`: 프린터 연결 관련 예외
- `PrintError`: 인쇄 관련 예외
- `StatusError`: 상태 확인 관련 예외
- `ImageError`: 이미지 처리 관련 예외
- `DeviceError`: 장치 제어 관련 예외

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.

## 참고사항

- 이 SDK는 HiTi Digital, Inc.의 공식 제품이 아니며, 해당 회사와 관련이 없습니다.
- HiTi 프린터를 사용하기 전에 공식 문서와 지침을 참조하세요.
- 프린터 드라이버 SDK는 HiTi의 지적 재산이며, 사용 전 적절한 라이센스를 취득해야 합니다.