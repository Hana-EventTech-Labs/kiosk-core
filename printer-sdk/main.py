from device_functions import *
from image_utils import *
from cffi_defs import ffi, SMART_OPENDEVICE_BYID, PAGE_FRONT, PANELID_COLOR
import tkinter as tk
from tkinter import messagebox

def show_print_confirmation():
    root = tk.Tk()
    root.withdraw()  # 메인 윈도우 숨김
    return messagebox.askyesno("인쇄 확인", "인쇄하시겠습니까?")

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
        return
    
    # 장치 선택
    device_index = 0
    device_id = get_device_id(printer_list, device_index)

    # 장치 열기
    result, device_handle = open_device(device_id, SMART_OPENDEVICE_BYID)
    if result != 0:
        print("장치 열기 실패")
        return

    # set_surface_properties(device_handle)

    # # ✅ 플리퍼 장착 여부 확인 추가
    # flipper_installed = get_printer_status(device_handle)
    # if flipper_installed is None:
    #     print("프린터 상태를 가져오는 데 실패했습니다.")
    # elif flipper_installed:
    #     print("✅ 이 프린터에는 플리퍼가 장착되어 있습니다. (양면 인쇄 가능)")
    # else:
    #     print("❌ 이 프린터에는 플리퍼가 없습니다. (단면 인쇄만 가능)")


    # Base이미지
    result = draw_image(device_handle, PAGE_FRONT, PANELID_COLOR, 0, 0, 638, 1011, "1.jpg")
    if result != 0:
        print("이미지 그리기 실패")

    #출력 내용물 좌표
    # result = draw_image(device_handle, PAGE_FRONT, PANELID_COLOR, 56, 292, 545, 545, "prac.jpg")
    # if result != 0:
    #     print("이미지 그리기 실패")

    font_style = 0x01  # Bold(0x01) + Italic(0x02)
    font_path = "resources/LAB디지털.ttf"
    font_name = load_font(font_path)  # 폰트 로드 후 폰트명 가져오기
    font_color = 0x0000FF  # ✅ 빨간색 (COLORREF 형식: 0x00BBGGRR)
    align = 0x01 | 0x10  # ✅ 가로 중앙 정렬 (OBJ_ALIGN_CENTER) + 세로 중앙 정렬 (OBJ_ALIGN_MIDDLE)

    # # ✅ 특정 좌표에 텍스트 출력 ( 사용자 지정 폰트 색상 불가, 검은색 텍스트만 뽑을 때 사용 )
    # if font_name:
    #     print(f"사용할 폰트: {font_name}")

    #     # ✅ 특정 좌표에 사용자 지정 폰트 적용하여 텍스트 출력
    #     font_style = 0x01  # Bold(0x01) + Italic(0x02)
    #     text="텍스트"
    #     result = draw_text(device_handle, PAGE_FRONT, PANELID_COLOR, 245, 145, font_name, 36, font_style, text)

    #     if result != 0:
    #         print("❌ 텍스트 출력 실패")

    multi_line_text = "첫 번째 줄\n두 번째 줄\n세 번째 줄"

    # ✅ SmartComm_DrawText2를 사용하여 빨간색 볼드 텍스트 출력
    result = draw_text2(
        device_handle,
        PAGE_FRONT, PANELID_COLOR,
        x=0, y=50, width=400, height=100,  # 텍스트 출력 영역
        # x=0, y=100, width=0, height=100,  # 텍스트 출력 영역
        font_name=font_name, font_height=32, font_width=21,  # 폰트 및 크기 설정
        font_style=font_style, font_color=font_color,  # 스타일 및 색상
        text=multi_line_text,  # 출력할 텍스트
        rotate=0, align=align, option=0
    )

    if result != 0:
        print("❌ 텍스트 출력 실패")
        
        
    # 미리보기 비트맵 가져오기
    result, bm_info = get_preview_bitmap(device_handle, PAGE_FRONT)
    if result == 0:
        image = bitmapinfo_to_image(bm_info)
        image.show()
    else:
        print("미리보기 비트맵 가져오기 실패")

    # 인쇄 여부 확인 대화상자 표시
    if show_print_confirmation():
        result = print_image(device_handle)
        if result != 0:
            print("이미지 인쇄 실패")
    else:
        print("인쇄가 취소되었습니다.")

    # 장치 닫기
    result = close_device(device_handle)
    if result != 0:
        print("장치 닫기 실패")

if __name__ == "__main__":
    main()
