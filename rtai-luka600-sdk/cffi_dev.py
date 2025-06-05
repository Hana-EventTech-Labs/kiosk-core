from cffi import FFI
import os
import time

ffi = FFI()

ffi.cdef("""
    unsigned int __stdcall R600LibInit();
    unsigned int __stdcall R600LibClear();
         
    unsigned int __stdcall R600EnumTcpPrt(char *szEnumList, unsigned int *pEnumListLen, int *pNum);
         
    unsigned int __stdcall R600TcpSetTimeout(int nReadTimeout, int nWriteTimeout);
         
    unsigned int __stdcall R600SelectPrt(const char *szPrt);
         
    unsigned int __stdcall R600PrepareCanvas(int nChromaticMode, int nMonoChroMode);
         
    unsigned int __stdcall R600DrawImage(double dX, double dY, double dWidth, double dHeight, const char *szImgFilePath, int nSetNoAbsoluteBlack);
         
    unsigned int __stdcall R600CommitCanvas(char *szImgInfo, int *pImgInfoLen);
         
    unsigned int __stdcall R600QueryPrtStatus(short *pChassisTemp, short *pPrintheadTemp, short *pHeaterTemp, unsigned int *pMainStatus, unsigned int *pSubStatus, unsigned int *pErrorStatus, unsigned int *pWarningStatus, unsigned char *pMainCode, unsigned char *pSubCode);
         
    unsigned int __stdcall R600IsFeederNoEmpty(int *pFlag);
         
    unsigned int __stdcall R600SetRibbonOpt(unsigned char isWrite, unsigned int key, char *value, unsigned int valueLen);
    
    unsigned int __stdcall R600CardInject(unsigned int ucDestPos);
         
    unsigned int __stdcall R600GetCardPos(int *pPos);
         
    unsigned int __stdcall R600PrintDraw(const char *szImgInfoFront, const char *szImgInfoBack);
         
    unsigned int __stdcall R600CardEject(unsigned int ucDestPos);
""")

dllpath = "libDSRetransfer600App.dll"

try:
    lib = ffi.dlopen(dllpath)
    print(f"DLL {dllpath} loaded successfully")

    ret  = lib.R600LibInit()
    if ret == 0:
        print("R600LibInit success")
    else:
        print(f"R600LibInit failed with error code {ret}")

    list_buffer_size = 1024 # 프린터 이름 목록을 받을 버퍼 크기 (충분히 크게)
    printer_list_buffer = ffi.new("char[]", list_buffer_size) # C 문자열 버퍼 생성
    p_enum_list_len = ffi.new("unsigned int*") # 실제 반환된 문자열 길이
    p_num_printers = ffi.new("int*") # 발견된 프린터 수

    ret = lib.R600EnumTcpPrt(printer_list_buffer, p_enum_list_len, p_num_printers)     
    if ret == 0:
        ret = lib.R600TcpSetTimeout(3000, 3000)
        if ret == 0:
            print("R600TcpSetTimeout success")
        else:
            print(f"R600TcpSetTimeout failed with error code {ret}")
        actual_len = p_enum_list_len[0]
        num_printers = p_num_printers[0]
        
        if actual_len > 0 and num_printers > 0:
            # C 버퍼에서 파이썬 문자열로 디코딩
            # cffi.string은 첫 번째 null 문자까지 읽습니다.
            printer_names_str = ffi.string(printer_list_buffer).decode('cp949')
            printer_names = [name.strip() for name in printer_names_str.split('\n') if name.strip()]
            
            print(f"프린터 열거 성공. 발견된 프린터 수: {num_printers}")
            print(f"프린터 목록:")
            for name in printer_names:
                print(f"- {name}")

        if printer_names:
            selected_printer = printer_names[0]
            print(f"\n[단계 3] R600SelectPrt 호출: '{selected_printer}' 선택 시도...")
            # 파이썬 문자열을 C 함수가 예상하는 바이트열(char*)로 인코딩
            ret = lib.R600SelectPrt(selected_printer.encode('cp949'))
            if ret == 0:
                print(f"프린터 '{selected_printer}' 선택 성공.")
            else:
                print(f"프린터 선택 실패: {ret}. SDK 문서의 'SDK Error Code'를 확인하세요.")
                exit()

        time.sleep(5)
        
        ret = lib.R600CardInject(0)
        if ret == 0:
            print("R600CardInject success")
        else:
            print(f"R600CardInject failed with error code {ret}")

        time.sleep(5)
        
        ret = lib.R600PrepareCanvas(0, 0)
        if ret == 0:
            print("R600PrepareCanvas success")
        else:
            print(f"R600PrepareCanvas failed with error code {ret}")

        # time.sleep(5)

        img_path = "test2.jpg"
        if os.path.exists(img_path):
            ret = lib.R600DrawImage(0.0,0.0,85.6,54.0,img_path.encode('cp949'),1)
            if ret == 0:
                print("R600DrawImage success")
            else:
                print(f"R600DrawImage failed with error code {ret}")
        else:
            print(f"이미지 파일 {img_path} 존재하지 않습니다.")

        # time.sleep(5)
        
        img_info_buffer_size = 200 # 이미지 정보 문자열을 받을 버퍼 크기
        img_info_buffer = ffi.new("char[]", img_info_buffer_size)
        p_img_info_len = ffi.new("int*", img_info_buffer_size)
        
        ret = lib.R600CommitCanvas(img_info_buffer, p_img_info_len)
        if ret == 0:
            committed_img_info = ffi.string(img_info_buffer).decode('cp949')
            print(f"캔버스 커밋 성공. 이미지 정보: {committed_img_info}")
        else:
            print(f"캔버스 커밋 실패: {ret}")
            exit()

        # p_flag = ffi.new("int*")
        # ret = lib.R600IsFeederNoEmpty(p_flag)
        # if ret == 0:
        #     print("R600IsFeederNoEmpty success")
        #     feeder_is_no_empty = p_flag[0]
        #     if feeder_is_no_empty:
        #         print("카드 슬롯이 비어있습니다.")
        #     else:
        #         print("카드 슬롯에 카드가 있습니다.")
        # else:
        #     print(f"R600IsFeederNoEmpty failed with error code {ret}")
        



        # p_card_pos = ffi.new("int*")
        # ret = lib.R600GetCardPos(p_card_pos)
        # if ret == 0:
        #     print("R600GetCardPos success")
        #     print(f"카드 위치: {p_card_pos[0]}")
        # else:
        #     print(f"R600GetCardPos failed with error code {ret}")

        # p_chassis_temp = ffi.new("short*")
        # p_printhead_temp = ffi.new("short*")
        # p_heater_temp = ffi.new("short*")
        # p_main_status = ffi.new("unsigned int*")
        # p_sub_status = ffi.new("unsigned int*")
        # p_error_status = ffi.new("unsigned int*")
        # p_warning_status = ffi.new("unsigned int*")
        # p_main_code = ffi.new("unsigned char*")
        # p_sub_code = ffi.new("unsigned char*")

        # ret = lib.R600QueryPrtStatus(p_chassis_temp, p_printhead_temp, p_heater_temp, p_main_status, p_sub_status, p_error_status, p_warning_status, p_main_code, p_sub_code) 
        # print(f"리턴 상태: {ret}")
        # print(f"메인 상태: {p_main_status[0]}")

        # if p_main_status[0] == 1004:
        #     ret = lib.R600PrintDraw(committed_img_info.encode('cp949'), ffi.NULL)
        #     print(f"인쇄 시작. 리턴 상태: {ret}")
            
        #     # 인쇄 완료까지 대기
        #     while True:
        #         ret = lib.R600QueryPrtStatus(p_chassis_temp, p_printhead_temp, p_heater_temp, p_main_status, p_sub_status, p_error_status, p_warning_status, p_main_code, p_sub_code)
        #         print(f"현재 메인 상태: {p_main_status[0]}")
                
        #         if p_main_status[0] == 1004:  # 인쇄 완료 상태
        #             print("인쇄 완료!")
        #             break
                    
        #         print("인쇄 진행 중... 30초 대기")
        #         time.sleep(30)
        # time.sleep(5)

        ret = lib.R600PrintDraw(committed_img_info.encode('cp949'), ffi.NULL)


        ret = lib.R600CardEject(0)
        if ret == 0:
            print("R600CardEject success")
        else:
            print(f"R600CardEject failed with error code {ret}")

    ret = lib.R600LibClear()
    if ret == 0:
        print("R600LibClear success")

except Exception as e:
    print(f"Error loading DLL: {e}")
    
