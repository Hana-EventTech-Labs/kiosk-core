import ctypes
import os
import time  # 상단에 추가

lib = ctypes.CDLL('./libDSRetransfer600App.dll')

# 라이브러리 초기화
ret = lib.R600LibInit()
print(ret)

# 함수 시그니처 정의
lib.R600EnumTcpPrt.argtypes = [ctypes.POINTER(ctypes.c_char), ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_int)]
lib.R600EnumTcpPrt.restype = ctypes.c_uint

# 버퍼와 포인터 생성
list_buffer_size = 1024
printer_list_buffer = ctypes.create_string_buffer(list_buffer_size)
enum_list_len = ctypes.c_uint(list_buffer_size)
num_printers = ctypes.c_int()

ret = lib.R600EnumTcpPrt(printer_list_buffer, ctypes.byref(enum_list_len), ctypes.byref(num_printers))
print(f"R600EnumTcpPrt 결과: {ret}")

if ret == 0:
    actual_len = enum_list_len.value
    printer_count = num_printers.value
    
    if actual_len > 0 and printer_count > 0:
        # 버퍼에서 문자열 디코딩
        printer_names_str = printer_list_buffer.value.decode('cp949')
        printer_names = [name.strip() for name in printer_names_str.split('\n') if name.strip()]
        
        print(f"발견된 프린터 수: {printer_count}")
        print("프린터 목록:")
        for name in printer_names:
            print(f"- {name}")
    else:
        print("프린터를 찾을 수 없습니다.")
    
    lib.R600TcpSetTimeout.argtypes = [ctypes.c_int, ctypes.c_int]
    lib.R600TcpSetTimeout.restype = ctypes.c_uint
    # 타임아웃 설정
    ret = lib.R600TcpSetTimeout(3000, 3000)
    print(f"R600TcpSetTimeout 결과: {ret}")

    lib.R600SelectPrt.argtypes = [ctypes.POINTER(ctypes.c_char)]
    lib.R600SelectPrt.restype = ctypes.c_uint
    # 프린터 선택
    selected_printer = printer_names[0]
    ret = lib.R600SelectPrt(selected_printer.encode('cp949'))
    print(f"R600SelectPrt 결과: {ret}")
    
    if ret == 0:
        print(f"프린터 선택 성공: {selected_printer}")

        lib.R600CardInject.argtypes = [ctypes.c_int]
        lib.R600CardInject.restype = ctypes.c_uint

        ret = lib.R600CardInject(0)
        if ret == 0:
            print("R600CardInject success")

            lib.R600SetRibbonOpt.argtypes = [ctypes.c_ubyte, ctypes.c_uint, ctypes.c_char_p, ctypes.c_uint]
            lib.R600SetRibbonOpt.restype = ctypes.c_uint

            # YMCS 리본 인쇄 모드 설정: key=0, value="2" (disabled)
            value_str = "2"
            value_bytes = value_str.encode('cp949')
            ret = lib.R600SetRibbonOpt(1, 0, value_bytes, len(value_bytes))
            if ret == 0:
                print("R600SetRibbonOpt success - 인쇄 모드 설정")
            else:
                print(f"R600SetRibbonOpt failed with error code {ret}")

            lib.R600PrepareCanvas.argtypes = [ctypes.c_int, ctypes.c_int]
            lib.R600PrepareCanvas.restype = ctypes.c_uint

            ret = lib.R600PrepareCanvas(0, 0)
            if ret == 0:
                print("R600PrepareCanvas success")
            else:
                print(f"R600PrepareCanvas failed with error code {ret}")

            lib.R600SetImagePara.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_float]
            lib.R600SetImagePara.restype = ctypes.c_uint

            ret = lib.R600SetImagePara(1, 0, 0.0)
            if ret == 0:
                print("R600SetImagePara success")
            else:
                print(f"R600SetImagePara failed with error code {ret}")

            lib.R600SetAddImageMode_Rtai.argtypes = [ctypes.c_int, ctypes.c_bool, ctypes.c_bool, ctypes.c_char_p, ctypes.c_int]
            lib.R600SetAddImageMode_Rtai.restype = ctypes.c_uint

            # ret = lib.R600SetAddImageMode_Rtai(3, True, False, ctypes.c_char_p(None), 100)
            # if ret == 0:
            #     print("R600SetAddImageMode_Rtai success")
            # else:
            #     print(f"R600SetAddImageMode_Rtai failed with error code {ret}")

            lib.R600DrawWaterMark.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_char_p]
            lib.R600DrawWaterMark.restype = ctypes.c_uint

            img_path = "12-B.jpg"
            if os.path.exists(img_path):
                ret = lib.R600DrawWaterMark(0.0, 0.0, 85.6, 53.98, img_path.encode('cp949'))
                if ret == 0:
                    print("R600DrawWaterMark success")
                else:
                    print(f"R600DrawWaterMark failed with error code {ret}")
            else:
                print(f"이미지 파일 {img_path} 존재하지 않습니다.")

            lib.R600DrawImage.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_char_p, ctypes.c_int]
            lib.R600DrawImage.restype = ctypes.c_uint
            
            img_path = "12.jpg"
            if os.path.exists(img_path):
                ret = lib.R600DrawImage(0.0, 0.0, 85.6, 53.98, img_path.encode('cp949'), 1)
                if ret == 0:
                    print("R600DrawImage success")
                else:
                    print(f"R600DrawImage failed with error code {ret}")
            else:
                print(f"이미지 파일 {img_path} 존재하지 않습니다.")

            # ret = lib.R600SetAddImageMode_Rtai(3, True, True, ctypes.c_char_p(None), 1)
            # if ret == 0:
            #     print("R600SetAddImageMode_Rtai success")
            # else:
            #     print(f"R600SetAddImageMode_Rtai failed with error code {ret}")
            
            lib.R600DrawLayerWhite.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_char_p]
            lib.R600DrawLayerWhite.restype = ctypes.c_uint

            # img_path_b = "black.jpg"
            # if os.path.exists(img_path_b):
            #     ret = lib.R600DrawLayerWhite(42.8, 26.99, 42.8, 26.99, img_path_b.encode('cp949'))
            #     if ret == 0:
            #         print("R600DrawLayerWhite success")
            #     else:
            #         print(f"R600DrawLayerWhite failed with error code {ret}")
            # else:
            #     print(f"이미지 파일 {img_path_b} 존재하지 않습니다.")

            lib.R600CommitCanvas.argtypes = [ctypes.POINTER(ctypes.c_char), ctypes.POINTER(ctypes.c_uint)]
            lib.R600CommitCanvas.restype = ctypes.c_uint

            img_info_buffer_size = 3072
            img_info_buffer = ctypes.create_string_buffer(img_info_buffer_size)
            p_img_info_len = ctypes.pointer(ctypes.c_uint(img_info_buffer_size))

            ret = lib.R600CommitCanvas(img_info_buffer, p_img_info_len)
            if ret == 0:
                committed_img_info = img_info_buffer.value.decode('cp949')
                print(f"캔버스 커밋 성공. 이미지 정보: {committed_img_info}")
                print(f"실제 이미지 정보 길이: {p_img_info_len.contents.value}")
            else:
                print(f"R600CommitCanvas failed with error code {ret}")

            time.sleep(1)


            lib.R600PrintDraw.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
            lib.R600PrintDraw.restype = ctypes.c_uint

            ret = lib.R600PrintDraw(committed_img_info.encode('cp949'), ctypes.c_char_p(None))
            if ret == 0:
                print("R600PrintDraw success")
            else:
                print(f"R600PrintDraw failed with error code {ret}")

            lib.R600CardEject.argtypes = [ctypes.c_int]
            lib.R600CardEject.restype = ctypes.c_uint

            ret = lib.R600CardEject(0)
            if ret == 0:
                print("R600CardEject success")
            else:
                print(f"R600CardEject failed with error code {ret}")
                
                
                
        else:
            print(f"R600CardInject failed with error code {ret}")

    else:
        print(f"프린터 선택 실패: {ret}")

else:
    print(f"프린터 열거 실패: {ret}")


# 라이브러리 닫기
ret = lib.R600LibClear()
print(ret)







