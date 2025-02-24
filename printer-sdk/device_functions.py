from cffi_defs import ffi, lib
from pathlib import Path

# 연결된 프린터 목록을 가져오는 함수
def get_device_list():
    # SMART_PRINTER_LIST 구조체 메모리 할당
    printer_list = ffi.new("SMART_PRINTER_LIST *")
    # DLL의 SmartComm_GetDeviceList2 함수를 호출하여 프린터 목록을 채움
    result = lib.SmartComm_GetDeviceList2(printer_list)
    return result, printer_list

# 프린터 리스트에서 특정 인덱스에 해당하는 프린터의 ID를 반환하는 함수
def get_device_id(printer_list, index):
    return printer_list.item[index].id

# 지정한 디바이스 ID를 이용하여 프린터 장치를 열고 핸들을 반환하는 함수
def open_device(device_id, open_device_by):
    # HSMART 핸들용 메모리 할당
    device_handle = ffi.new("HSMART *")
    # DLL의 SmartComm_OpenDevice2 함수를 호출하여 장치를 열고 핸들을 받아옴
    result = lib.SmartComm_OpenDevice2(device_handle, device_id, open_device_by)
    return result, device_handle[0]

# 프린터에 이미지를 출력하기 위한 함수
def draw_image(device_handle, page, panel, x, y, cx, cy, image_filename):
    # cx,cy는 px단위
    # 현재 파일의 경로를 기준으로 resources 폴더 내의 이미지 파일 경로 생성
    image_path = Path(__file__).parent / "resources" / image_filename
    image_path_str = str(image_path.resolve())
    # wchar_t 배열로 이미지 경로를 변환 (DLL 호출을 위해)
    image = ffi.new("wchar_t[]", image_path_str)
    # 출력 영역 정보 저장을 위한 RECT 구조체 메모리 할당
    rect_area = ffi.new("RECT *")
    # DLL의 SmartComm_DrawImage 함수를 호출하여 지정 영역에 이미지를 그림
    result = lib.SmartComm_DrawImage(device_handle, page, panel, x, y, cx, cy, image, rect_area)
    return result

# 프린터에서 미리보기 비트맵 데이터를 가져오는 함수
def get_preview_bitmap(device_handle, page):
    # BITMAPINFO 구조체에 대한 포인터 메모리 할당
    p_bitmap_info = ffi.new("BITMAPINFO **")
    # DLL의 SmartComm_GetPreviewBitmap 함수를 호출하여 비트맵 정보를 가져옴
    result = lib.SmartComm_GetPreviewBitmap(device_handle, page, p_bitmap_info)
    return result, p_bitmap_info[0]

# 프린터 장치에 인쇄 명령을 보내는 함수
def print_image(device_handle):
    result = lib.SmartComm_Print(device_handle)
    return result

# 열려있는 프린터 장치의 연결을 종료하는 함수
def close_device(device_handle):
    lib.SmartComm_CloseDevice(device_handle)

def get_printer_status(device_handle):
    """
    SmartComm_GetStatus 함수를 호출하여 프린터 상태를 가져오고, 플리퍼 장착 여부를 확인하는 함수
    """
    status = ffi.new("DWORD *")  # DWORD 타입 변수 생성
    result = lib.SmartComm_GetStatus(device_handle, status)

    if result != 0:
        print(f"SmartComm_GetStatus 호출 실패 (오류 코드: {result})")
        return None

    status_value = status[0]

    # 플리퍼 옵션 확인 (상태 값의 특정 비트 확인 필요)
    is_flipper_installed = (status_value & (1 << 3)) != 0  # 예제: 3번째 비트가 플리퍼 상태를 나타낸다고 가정

    return is_flipper_installed
