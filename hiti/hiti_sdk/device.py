# hiti_sdk/device.py
"""
HiTi 프린터와 직접 통신하기 위한 DLL 인터페이스 및 기본 장치 기능
"""
import os
import sys
import logging
import time
from pathlib import Path
import ctypes
from ctypes import wintypes, c_char_p, c_wchar_p, c_void_p, byref, POINTER, Structure, c_char
from cffi import FFI

from .constants import DeviceStatus, RibbonType, PrintCommand, DeviceInfoType
from .exceptions import PrinterError, ConnectionError, DeviceError, DLLError

# 로깅 설정
logger = logging.getLogger(__name__)


class HITI_USB_PRINTER(Structure):
    """HiTi USB 프린터 구조체"""
    _fields_ = [
        ("PrinterName", c_char * 260),  # MAX_PATH = 260
        ("bModelNo", ctypes.c_ubyte),
        ("bIndexNo", ctypes.c_ubyte),
    ]


class HITI_JOB_PROPERTY_RT(Structure):
    """HiTi 인쇄 작업 속성 구조체"""
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("hParentWnd", wintypes.HWND),
        ("pReserved1", c_void_p),
        ("dwPaperType", wintypes.DWORD),
        ("dwPrintMode", wintypes.DWORD),
        ("shOrientation", ctypes.c_short),
        ("shCopies", ctypes.c_short),
        ("dwFlags", wintypes.DWORD),
        ("pReserved2", c_void_p),
        ("pReserved3", c_void_p),
        ("dwIndex", wintypes.DWORD),
        ("pReserved4", c_void_p),
        ("dwApplyMatte", wintypes.DWORD),
        ("lReserved1", ctypes.c_long),
        ("pReserved5", c_void_p),
        ("pReserved6", c_void_p),
    ]


class BITMAP(Structure):
    """비트맵 구조체"""
    _fields_ = [
        ("bmType", ctypes.c_long),
        ("bmWidth", ctypes.c_long),
        ("bmHeight", ctypes.c_long),
        ("bmWidthBytes", ctypes.c_long),
        ("bmPlanes", ctypes.c_short),
        ("bmBitsPixel", ctypes.c_short),
        ("bmBits", c_void_p),
    ]


class HiTiDll:
    """HiTi 프린터 DLL 래퍼 클래스"""
    def __init__(self, dll_path=None):
        """HiTi SDK DLL을 로드하고 필요한 함수를 초기화합니다."""
        if dll_path is None:
            # 기본 위치에서 DLL 찾기
            dll_path = self._find_default_dll_path()
        
        self.dll_path = Path(dll_path)
        self.ffi = FFI()
        
        try:
            # DLL 로드
            if sys.platform == 'win32':
                self.dll = ctypes.WinDLL(str(self.dll_path))
                logger.info(f"DLL 로드 성공: {self.dll_path}")
            else:
                # CFFI 사용 (비Windows 환경)
                self._init_cffi_interface()
                self.lib = self.ffi.dlopen(str(self.dll_path))
                logger.info(f"CFFI를 통해 DLL 로드 성공: {self.dll_path}")
        except Exception as e:
            logger.error(f"DLL 로드 실패: {e}")
            raise DLLError(f"HiTi SDK DLL 로드 실패: {e}")
        
        # 함수 설정
        self._setup_functions()
    
    def _find_default_dll_path(self):
        """기본 DLL 경로 찾기"""
        # 현재 모듈 디렉토리 기준으로 찾기
        module_dir = Path(__file__).parent
        
        # 32비트와 64비트 버전 경로
        possible_paths = [
            module_dir / "HTRTAPI.dll",
            module_dir / ".." / "HTRTAPI.dll",
            module_dir / ".." / "DLL" / "HTRTAPI.dll",
            module_dir / ".." / "DLLx64" / "HTRTAPI.dll",
        ]
        
        # 64비트 시스템인지 확인
        is_64bit = sys.maxsize > 2**32
        
        for path in possible_paths:
            if path.exists():
                # 64비트 시스템에서는 64비트 DLL을 우선적으로 선택
                if is_64bit and "x64" in str(path):
                    return path
                return path
        
        # DLL이 없는 경우 기본 위치 반환
        return module_dir / ".." / "HTRTAPI.dll"
    
    def _init_cffi_interface(self):
        """CFFI 인터페이스 초기화 (비Windows 환경용)"""
        # CFFI 인터페이스 정의
        self.ffi.cdef("""
            typedef unsigned int DWORD;
            typedef void* HWND;
            typedef void* HDC;
            typedef short SHORT;
            typedef char TCHAR;
            typedef unsigned char BYTE;
            typedef wchar_t WCHAR;
            typedef struct tagBITMAP BITMAP;
            typedef long LONG;
            typedef char* LPTSTR;

            #define MAX_PATH 260

            typedef struct tagHITI_USB_PRINTER {
                TCHAR PrinterName[MAX_PATH];
                BYTE bModelNo;
                BYTE bIndexNo;
            } HITI_USB_PRINTER, *PHITI_USB_PRINTER, *LPHITI_USB_PRINTER;

            typedef struct tagHITI_JOB_PROPERTY_RT {
                DWORD dwSize;
                HWND hParentWnd;
                void* pReserved1;
                DWORD dwPaperType;
                DWORD dwPrintMode;
                short shOrientation;
                short shCopies;
                DWORD dwFlags;
                void* pReserved2;
                void* pReserved3;
                DWORD dwIndex;
                void* pReserved4;
                DWORD dwApplyMatte;
                LONG lReserved1;
                void* pReserved5;
                void* pReserved6;
            } HITI_JOB_PROPERTY_RT;

            typedef struct tagBITMAP {
                LONG   bmType;
                LONG   bmWidth;
                LONG   bmHeight;
                LONG   bmWidthBytes;
                SHORT  bmPlanes;
                SHORT  bmBitsPixel;
                void   *bmBits;
            } BITMAP;

            DWORD HITI_ApplyJobSettingA(char* szPrinter, HDC hDC, BYTE* lpInDevMode, BYTE* lpInJobProp);
            DWORD HITI_CheckPrinterStatusA(char* szPrinter, DWORD *lpdwStatus);
            DWORD HITI_DoCommandA(char* szPrinter, DWORD dwCommand);
            DWORD HITI_GetDeviceInfoA(char* szPrinter, DWORD dwInfoType, BYTE *lpInfoData, DWORD *lpdwDataLen);
            DWORD HITI_PrintOnePageA(char* szPrinter, HITI_JOB_PROPERTY_RT *lpJobProp, BITMAP* lpBmpIn);
            DWORD HITI_EnumUsbPrinters(HITI_USB_PRINTER* pPrinterEnum, unsigned long cbBuf, unsigned long* pcbNeeded, unsigned long* pcReturned);
        """)
    
    def _setup_functions(self):
        """DLL 함수 설정"""
        if sys.platform == 'win32':
            # WinDLL 사용하는 경우 (Windows)
            # 프린터 열거 함수
            self.enum_usb_printers = self.dll.HITI_EnumUsbPrinters
            self.enum_usb_printers.argtypes = [
                POINTER(HITI_USB_PRINTER),
                wintypes.DWORD, 
                POINTER(wintypes.DWORD), 
                POINTER(wintypes.DWORD)
            ]
            self.enum_usb_printers.restype = wintypes.DWORD
            
            # 프린터 상태 확인 함수
            self.check_printer_status = self.dll.HITI_CheckPrinterStatusA
            self.check_printer_status.argtypes = [c_char_p, POINTER(wintypes.DWORD)]
            self.check_printer_status.restype = wintypes.DWORD
            
            # 프린터 명령 실행 함수
            self.do_command = self.dll.HITI_DoCommandA
            self.do_command.argtypes = [c_char_p, wintypes.DWORD]
            self.do_command.restype = wintypes.DWORD
            
            # 프린터 정보 가져오기 함수
            self.get_device_info = self.dll.HITI_GetDeviceInfoA
            self.get_device_info.argtypes = [
                c_char_p, 
                wintypes.DWORD, 
                POINTER(ctypes.c_ubyte), 
                POINTER(wintypes.DWORD)
            ]
            self.get_device_info.restype = wintypes.DWORD
            
            # 한 페이지 인쇄 함수
            self.print_one_page = self.dll.HITI_PrintOnePageA
            self.print_one_page.argtypes = [c_char_p, POINTER(HITI_JOB_PROPERTY_RT), POINTER(BITMAP)]
            self.print_one_page.restype = wintypes.DWORD
            
            # 인쇄 설정 적용 함수
            self.apply_job_setting = self.dll.HITI_ApplyJobSettingA
            self.apply_job_setting.argtypes = [c_char_p, wintypes.HDC, POINTER(ctypes.c_ubyte), POINTER(ctypes.c_ubyte)]
            self.apply_job_setting.restype = wintypes.DWORD
        
        else:
            # CFFI 사용하는 경우 (비Windows)
            self.enum_usb_printers = self.lib.HITI_EnumUsbPrinters
            self.check_printer_status = self.lib.HITI_CheckPrinterStatusA
            self.do_command = self.lib.HITI_DoCommandA
            self.get_device_info = self.lib.HITI_GetDeviceInfoA
            self.print_one_page = self.lib.HITI_PrintOnePageA
            self.apply_job_setting = self.lib.HITI_ApplyJobSettingA


class HiTiDevice:
    """HiTi 프린터 장치 클래스"""
    def __init__(self, printer_name, model_no=None, index_no=None):
        """
        HiTi 프린터 장치를 초기화합니다.
        
        Args:
            printer_name (str): 프린터 이름 또는 USB 경로
            model_no (int, optional): 프린터 모델 번호
            index_no (int, optional): 프린터 인덱스 번호
        """
        self.printer_name = printer_name
        self.model_no = model_no
        self.index_no = index_no
        
        try:
            # DLL 로드
            self.dll = HiTiDll()
            logger.info(f"장치 초기화 성공: {printer_name}")
        except DLLError as e:
            logger.error(f"장치 초기화 실패: {e}")
            raise
    
    def check_status(self):
        """
        프린터 상태를 확인합니다.
        
        Returns:
            tuple: (status_code, status_description)
        
        Raises:
            StatusError: 상태 확인 실패 시
        """
        try:
            status = wintypes.DWORD(0)
            printer_name_bytes = self.printer_name.encode('utf-8')
            
            result = self.dll.check_printer_status(printer_name_bytes, byref(status))
            
            if result != 0:
                raise DeviceError(f"프린터 상태 확인 실패", result)
            
            status_code = status.value
            
            # 특수 상태 코드 처리
            if status_code == 0x00000002:
                # 0x00000002는 일부 HiTi 프린터에서 사용하는 인쇄 진행 중 상태 코드
                # 이것은 정상적인 상태이므로 오류로 처리하지 않음
                status_desc = "인쇄 진행 중"
                logger.debug(f"프린터 상태: {status_desc} (0x{status_code:08X})")
                return status_code, status_desc
                
            status_desc = DeviceStatus.get_description(status_code)
            
            logger.debug(f"프린터 상태: {status_desc} (0x{status_code:08X})")
            
            return status_code, status_desc
            
        except Exception as e:
            logger.error(f"상태 확인 중 오류 발생: {e}")
            raise DeviceError(f"프린터 상태 확인 중 오류 발생: {e}")
        
    def send_command(self, command):
        """
        프린터에 명령을 전송합니다.
        
        Args:
            command (PrintCommand): 전송할 명령
            
        Returns:
            bool: 성공 여부
            
        Raises:
            DeviceError: 명령 전송 실패 시
        """
        try:
            printer_name_bytes = self.printer_name.encode('utf-8')
            
            result = self.dll.do_command(printer_name_bytes, command)
            
            if result != 0:
                raise DeviceError(f"명령 전송 실패 (명령: {command})", result)
            
            logger.debug(f"명령 전송 성공: {command}")
            return True
            
        except Exception as e:
            logger.error(f"명령 전송 중 오류 발생: {e}")
            raise DeviceError(f"프린터 명령 전송 중 오류 발생: {e}")
    
    def get_device_info(self, info_type):
        """
        프린터 정보를 가져옵니다.
        
        Args:
            info_type (DeviceInfoType): 요청할 정보 유형
            
        Returns:
            다양한 타입: 요청한 정보 유형에 따른 결과
            
        Raises:
            DeviceError: 정보 조회 실패 시
        """
        try:
            printer_name_bytes = self.printer_name.encode('utf-8')
            
            # 정보 유형에 따라 버퍼 크기 결정
            if info_type in [DeviceInfoType.MFG_SERIAL, DeviceInfoType.MODEL_NAME, DeviceInfoType.FIRMWARE_VERSION]:
                buffer_size = 256
                data_buf = (ctypes.c_ubyte * buffer_size)()
            elif info_type == DeviceInfoType.RIBBON_INFO:
                buffer_size = 8  # 2개의 DWORD (8바이트)
                data_buf = (ctypes.c_ubyte * buffer_size)()
            elif info_type in [DeviceInfoType.PRINT_COUNT, DeviceInfoType.CUTTER_COUNT]:
                buffer_size = 4  # 1개의 DWORD (4바이트)
                data_buf = (ctypes.c_ubyte * buffer_size)()
            else:
                raise ValueError(f"지원하지 않는 정보 유형: {info_type}")
            
            data_len = wintypes.DWORD(buffer_size)
            
            result = self.dll.get_device_info(
                printer_name_bytes,
                info_type,
                data_buf,
                byref(data_len)
            )
            
            if result != 0:
                raise DeviceError(f"프린터 정보 조회 실패 (유형: {info_type})", result)
            
            # 결과 데이터 파싱
            if info_type in [DeviceInfoType.MFG_SERIAL, DeviceInfoType.MODEL_NAME, DeviceInfoType.FIRMWARE_VERSION]:
                # 문자열 데이터
                return ctypes.cast(data_buf, c_char_p).value.decode('utf-8', errors='ignore')
            
            elif info_type == DeviceInfoType.RIBBON_INFO:
                # 리본 정보 (2개의 DWORD)
                ribbon_type = int.from_bytes(data_buf[0:4], byteorder='little')
                ribbon_count = int.from_bytes(data_buf[4:8], byteorder='little')
                
                return {
                    "type": ribbon_type,
                    "type_name": self._get_ribbon_type_name(ribbon_type),
                    "count": ribbon_count
                }
            
            elif info_type in [DeviceInfoType.PRINT_COUNT, DeviceInfoType.CUTTER_COUNT]:
                # 카운트 정보 (1개의 DWORD)
                return int.from_bytes(data_buf[0:4], byteorder='little')
        
        except Exception as e:
            logger.error(f"정보 조회 중 오류 발생: {e}")
            raise DeviceError(f"프린터 정보 조회 중 오류 발생: {e}")
    
    def _get_ribbon_type_name(self, ribbon_type):
        """리본 유형 코드에 대한 이름 반환"""
        ribbon_types = {
            RibbonType.RIBBON_4X6: "4x6 리본",
            RibbonType.RIBBON_5X7: "5x7 리본",
            RibbonType.RIBBON_6X9: "6x9 리본",
            RibbonType.RIBBON_6X8: "6x8 리본",
            RibbonType.RIBBON_5X3dot5: "5x3.5 리본",
            RibbonType.RIBBON_6X12: "6x12 리본",
            RibbonType.RIBBON_8X12: "8x12 리본"
        }
        return ribbon_types.get(ribbon_type, f"알 수 없는 리본 유형 ({ribbon_type})")
    
    def reset(self):
        """프린터를 재설정합니다."""
        return self.send_command(PrintCommand.RESET_PRINTER)
    
    def lock(self):
        """프린터를 잠급니다."""
        return self.send_command(PrintCommand.LOCK_PRINTER)
    
    def unlock(self):
        """프린터 잠금을 해제합니다."""
        return self.send_command(PrintCommand.UNLOCK_PRINTER)
    
    def cut_paper(self):
        """용지를 절단합니다."""
        return self.send_command(PrintCommand.CUT_PAPER)
    
    def wait_until_ready(self, timeout=60, check_interval=0.5):
        """
        프린터가 사용 가능할 때까지 대기합니다.
        
        Args:
            timeout (float): 최대 대기 시간(초)
            check_interval (float): 상태 확인 간격(초)
            
        Returns:
            bool: 프린터가 준비되었으면 True, 타임아웃 발생 시 False
            
        Raises:
            DeviceError: 상태 확인 중 오류 발생 시
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                status_code, _ = self.check_status()
                
                # 프린터 상태 확인
                # BUSY, PRINTING, PROCESSING_DATA, SENDING_DATA 상태는 대기
                if (status_code != DeviceStatus.BUSY and 
                    status_code != DeviceStatus.PRINTING and 
                    status_code != DeviceStatus.PROCESSING_DATA and
                    status_code != DeviceStatus.SENDING_DATA and
                    status_code != 0x00000002):  # 0x00000002 추가 - 일부 프린터에서 인쇄 중 상태
                    
                    # OK 상태면 준비 완료
                    if status_code == 0:
                        return True
                        
                    # 심각한 오류 상태 확인 - 0x8으로 시작하는 비트는 심각한 오류
                    if (status_code & 0x00080000) or (status_code & 0x00008000):
                        logger.warning(f"프린터 오류 상태: 0x{status_code:08X}")
                        return False
                        
                    # 그 외 상태는 일시적인 상태로 간주하고 준비 완료로 판단
                    logger.debug(f"프린터 상태: 0x{status_code:08X} - 준비된 것으로 간주")
                    return True
                
                # 대기 상태면 계속 대기
                logger.debug(f"프린터 대기 중: 0x{status_code:08X}")
                
            except Exception as e:
                logger.error(f"프린터 상태 확인 중 오류: {e}")
                time.sleep(check_interval * 2)  # 오류 발생 시 대기 시간 증가
            
            time.sleep(check_interval)
        
        # 타임아웃
        logger.warning(f"프린터 준비 대기 타임아웃: {timeout}초")
        return False
def find_printers():
    """
    연결된 HiTi USB 프린터 목록을 검색합니다.
    
    Returns:
        list: HiTiDevice 객체 목록
        
    Raises:
        ConnectionError: 프린터 검색 실패 시
    """
    try:
        # DLL 로드
        dll = HiTiDll()
        
        # 필요한 버퍼 크기 확인
        needed = wintypes.DWORD(0)
        returned = wintypes.DWORD(0)
        
        result = dll.enum_usb_printers(None, 0, byref(needed), byref(returned))
        
        if needed.value <= 0:
            logger.info("연결된 USB 프린터를 찾을 수 없습니다.")
            return []
        
        # 버퍼 크기에 맞게 메모리 할당
        buffer_size = needed.value
        max_printers = buffer_size // ctypes.sizeof(HITI_USB_PRINTER)
        
        if max_printers <= 0:
            logger.warning("프린터 구조체 크기 계산 오류")
            return []
        
        printer_enum = (HITI_USB_PRINTER * max_printers)()
        result = dll.enum_usb_printers(printer_enum, buffer_size, byref(needed), byref(returned))
        
        if result != 0:
            raise ConnectionError(f"프린터 열거 실패", result)
        
        if returned.value <= 0:
            logger.info("연결된 프린터가 없습니다.")
            return []
        
        # 프린터 정보 파싱
        printers = []
        for i in range(returned.value):
            try:
                # 프린터 이름 추출
                name_bytes = bytes(printer_enum[i].PrinterName).split(b'\0')[0]
                name = name_bytes.decode('utf-8', errors='ignore')
                
                # 유효한 프린터 이름인지 확인
                if name and name.strip() and len(name.strip()) > 1:
                    model = printer_enum[i].bModelNo
                    index = printer_enum[i].bIndexNo
                    
                    device = HiTiDevice(
                        printer_name=name.strip(),
                        model_no=model,
                        index_no=index
                    )
                    
                    printers.append(device)
                    logger.info(f"프린터 발견: 이름='{name.strip()}', 모델={model}, 인덱스={index}")
            
            except Exception as e:
                logger.error(f"프린터 정보 파싱 중 오류: {e}")
        
        return printers
        
    except Exception as e:
        logger.error(f"프린터 검색 중 오류 발생: {e}")
        if isinstance(e, ConnectionError):
            raise
        raise ConnectionError(f"HiTi 프린터 검색 중 오류 발생: {e}")