from device_functions import get_device_list, get_device_id, open_device, draw_image, get_preview_bitmap, print_image, close_device
from image_utils import bitmapinfo_to_image
from cffi_defs import ffi, SMART_OPENDEVICE_BYID, PAGE_FRONT, PANELID_COLOR

def main():

    # 장치 목록 조회
    result, printer_list = get_device_list()
    if result == 0:
        print(f"총 {printer_list.n}개의 프린터 발견됨.")
        for i in range(printer_list.n):
            item = printer_list.item[i]
            print(f"프린터 {i+1}:")
            print(f"  이름: {ffi.string(item.name)}")
            print(f"  ID: {ffi.string(item.id)}")
            print(f"  장치: {ffi.string(item.dev)}")
            print(f"  설명: {ffi.string(item.desc)}")
            print(f"  PID: {item.pid}")
    else:
        print("프린터 목록 가져오기 실패.")
    
    # 장치 선택
    device_index = 0
    device_id = get_device_id(printer_list, device_index)

    # 장치 열기
    result, device_handle = open_device(device_id, SMART_OPENDEVICE_BYID)
    if result != 0:
        print("장치 열기 실패")

    # 이미지 그리기
    x = 0
    y = 0
    cx = 0
    cy = 0
    result = draw_image(device_handle, PAGE_FRONT, PANELID_COLOR, x, y, cx, cy, "base.jpg")
    if result != 0:
        print("이미지 그리기 실패")

    # AHC 예시 좌표
    # x = 56
    # y = 292
    # cx = 545
    # cy = 545
    # result = draw_image(device_handle, PAGE_FRONT, PANELID_COLOR, x, y, cx, cy, "prac.png")
    # if result != 0:
    #     print("이미지 그리기 실패")

    # 미리보기 비트맵 가져오기
    result, bm_info = get_preview_bitmap(device_handle, PAGE_FRONT)
    if result == 0:
        image = bitmapinfo_to_image(bm_info)
        image.show()
    else:
        print("미리보기 비트맵 가져오기 실패")

    # 이미지 인쇄
    result = print_image(device_handle)
    if result != 0:
        print("이미지 인쇄 실패")

    # 장치 닫기
    close_device(device_handle)
    if result != 0:
        print("장치 닫기 실패")

if __name__ == "__main__":
    main()

