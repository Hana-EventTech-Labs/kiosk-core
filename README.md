# 🚀 Kiosk-Core

**키오스크 시스템을 위한 공통 기능 라이브러리**  
키오스크 기반 행사에서 재사용할 수 있는 다양한 기능을 포함하는 모듈입니다.  
현재는 **가상 키보드** 기능을 제공하며, 앞으로 **프린터 제어, 발급 통계 기록, 랜덤 디자인 선택** 기능이 추가될 예정입니다.  

---

## 📦 주요 기능 (진행 중)
| 기능                     | 설명 |
|--------------------------|----------------------------------------------------------------|
| 🎹 **가상 키보드**       | 키오스크에서 터치스크린용 가상 키보드 제공  |
| 🖨️ **프린터 제어** (예정) | 키오스크에서 카드를 즉시 출력하는 기능 |
| 📊 **발급 통계 기록** (예정) | 카드 발급 내역을 기록하고, 통계를 제공 |
| 🎨 **랜덤 디자인 선택** (예정) | 카드 디자인을 랜덤으로 선택하는 기능 |

---

## 🏗️ 현재 제공되는 기능

### 🎹 가상 키보드 (`virtual_keyboard.py`)
- 키오스크에서 사용할 수 있는 **터치스크린 가상 키보드** 제공  
- 숫자 키, 한글 입력 가능
- 대문자,소문자, 한글 입력 길이 제한 기능
  - MAX_LOWERCASE , MAX_UPPERCASE, MAX_HANGUL
- **향후 업데이트 예정**: 사용자 정의 테마 지원, 키보드 레이아웃 변경 기능

### 📌 **`hangul_composer.py` 파일 필수**
📌 `virtual_keyboard.py`는 **`hangul_composer.py` 파일과 동일한 디렉터리 내에 위치해야 합니다.**  
**둘 중 하나라도 없으면 한글 입력 기능이 정상 작동하지 않습니다.**  
