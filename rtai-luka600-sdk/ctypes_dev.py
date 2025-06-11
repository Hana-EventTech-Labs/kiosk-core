import ctypes
import os
import time
from typing import List, Optional, Tuple


class R600PrinterError(Exception):
    """R600 프린터 관련 예외"""
    pass


class R600Printer:
    """R600 프린터 제어 클래스"""
    
    def __init__(self, dll_path: str = './libDSRetransfer600App.dll'):
        """
        R600 프린터 초기화
        
        Args:
            dll_path: DLL 파일 경로
        """
        self.lib = None
        self.selected_printer = None
        self.committed_img_info = None
        
        try:
            self.lib = ctypes.CDLL(dll_path)
            self._setup_function_signatures()
            self._initialize_library()
        except Exception as e:
            raise R600PrinterError(f"프린터 초기화 실패: {e}")
    
    def _setup_function_signatures(self):
        """함수 시그니처 정의"""
        # 프린터 열거
        self.lib.R600EnumTcpPrt.argtypes = [
            ctypes.POINTER(ctypes.c_char), 
            ctypes.POINTER(ctypes.c_uint), 
            ctypes.POINTER(ctypes.c_int)
        ]
        self.lib.R600EnumTcpPrt.restype = ctypes.c_uint
        
        # 타임아웃 설정
        self.lib.R600TcpSetTimeout.argtypes = [ctypes.c_int, ctypes.c_int]
        self.lib.R600TcpSetTimeout.restype = ctypes.c_uint
        
        # 프린터 선택
        self.lib.R600SelectPrt.argtypes = [ctypes.POINTER(ctypes.c_char)]
        self.lib.R600SelectPrt.restype = ctypes.c_uint
        
        # 카드 관련
        self.lib.R600CardInject.argtypes = [ctypes.c_int]
        self.lib.R600CardInject.restype = ctypes.c_uint
        
        self.lib.R600CardEject.argtypes = [ctypes.c_int]
        self.lib.R600CardEject.restype = ctypes.c_uint
        
        # 리본 옵션
        self.lib.R600SetRibbonOpt.argtypes = [
            ctypes.c_ubyte, ctypes.c_uint, ctypes.c_char_p, ctypes.c_uint
        ]
        self.lib.R600SetRibbonOpt.restype = ctypes.c_uint
        
        # 캔버스 관련
        self.lib.R600SetCanvasPortrait.argtypes = [ctypes.c_int]
        self.lib.R600SetCanvasPortrait.restype = ctypes.c_uint
        
        self.lib.R600PrepareCanvas.argtypes = [ctypes.c_int, ctypes.c_int]
        self.lib.R600PrepareCanvas.restype = ctypes.c_uint
        
        self.lib.R600CommitCanvas.argtypes = [
            ctypes.POINTER(ctypes.c_char), 
            ctypes.POINTER(ctypes.c_uint)
        ]
        self.lib.R600CommitCanvas.restype = ctypes.c_uint
        
        # 이미지 관련
        self.lib.R600SetImagePara.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_float]
        self.lib.R600SetImagePara.restype = ctypes.c_uint
        
        self.lib.R600DrawWaterMark.argtypes = [
            ctypes.c_double, ctypes.c_double, ctypes.c_double, 
            ctypes.c_double, ctypes.c_char_p
        ]
        self.lib.R600DrawWaterMark.restype = ctypes.c_uint
        
        self.lib.R600DrawImage.argtypes = [
            ctypes.c_double, ctypes.c_double, ctypes.c_double, 
            ctypes.c_double, ctypes.c_char_p, ctypes.c_int
        ]
        self.lib.R600DrawImage.restype = ctypes.c_uint
        
        self.lib.R600DrawLayerWhite.argtypes = [
            ctypes.c_double, ctypes.c_double, ctypes.c_double, 
            ctypes.c_double, ctypes.c_char_p
        ]
        self.lib.R600DrawLayerWhite.restype = ctypes.c_uint
        
        # 인쇄
        self.lib.R600PrintDraw.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.R600PrintDraw.restype = ctypes.c_uint
    
    def _initialize_library(self):
        """라이브러리 초기화"""
        ret = self.lib.R600LibInit()
        if ret != 0:
            raise R600PrinterError(f"라이브러리 초기화 실패: {ret}")
        print(f"라이브러리 초기화 성공: {ret}")
    
    def _check_result(self, result: int, operation: str):
        """결과 코드 확인"""
        if result == 0:
            print(f"{operation} 성공")
        else:
            raise R600PrinterError(f"{operation} 실패: 오류 코드 {result}")
    
    def enum_printers(self) -> List[str]:
        """TCP 프린터 목록 조회"""
        list_buffer_size = 1024
        printer_list_buffer = ctypes.create_string_buffer(list_buffer_size)
        enum_list_len = ctypes.c_uint(list_buffer_size)
        num_printers = ctypes.c_int()
        
        ret = self.lib.R600EnumTcpPrt(
            printer_list_buffer, 
            ctypes.byref(enum_list_len), 
            ctypes.byref(num_printers)
        )
        
        if ret != 0:
            raise R600PrinterError(f"프린터 열거 실패: {ret}")
        
        actual_len = enum_list_len.value
        printer_count = num_printers.value
        
        if actual_len > 0 and printer_count > 0:
            printer_names_str = printer_list_buffer.value.decode('cp949')
            printer_names = [name.strip() for name in printer_names_str.split('\n') if name.strip()]
            
            print(f"발견된 프린터 수: {printer_count}")
            print("프린터 목록:")
            for name in printer_names:
                print(f"- {name}")
            
            return printer_names
        else:
            print("프린터를 찾을 수 없습니다.")
            return []
    
    def set_timeout(self, timeout_ms: int = 10000):
        """타임아웃 설정"""
        ret = self.lib.R600TcpSetTimeout(timeout_ms, timeout_ms)
        self._check_result(ret, "타임아웃 설정")
    
    def select_printer(self, printer_name: str):
        """프린터 선택"""
        ret = self.lib.R600SelectPrt(printer_name.encode('cp949'))
        self._check_result(ret, f"프린터 선택 ({printer_name})")
        self.selected_printer = printer_name
    
    def inject_card(self):
        """카드 삽입"""
        ret = self.lib.R600CardInject(0)
        self._check_result(ret, "카드 삽입")
    
    def eject_card(self):
        """카드 배출"""
        ret = self.lib.R600CardEject(0)
        self._check_result(ret, "카드 배출")
    
    def set_ribbon_option(self, ribbon_type: int = 1, key: int = 0, value: str = "2"):
        """리본 옵션 설정"""
        value_bytes = value.encode('cp949')
        ret = self.lib.R600SetRibbonOpt(ribbon_type, key, value_bytes, len(value_bytes))
        self._check_result(ret, "리본 옵션 설정")
    
    def setup_canvas(self, portrait: bool = True):
        """캔버스 설정"""
        # 세로 방향 설정
        ret = self.lib.R600SetCanvasPortrait(1 if portrait else 0)
        self._check_result(ret, "캔버스 방향 설정")
        
        # 캔버스 준비
        ret = self.lib.R600PrepareCanvas(0, 0)
        self._check_result(ret, "캔버스 준비")
        
        # 이미지 파라미터 설정
        ret = self.lib.R600SetImagePara(1, 0, 0.0)
        self._check_result(ret, "이미지 파라미터 설정")
    
    def draw_watermark(self, x: float, y: float, width: float, height: float, image_path: str):
        """워터마크 그리기"""
        if not os.path.exists(image_path):
            raise R600PrinterError(f"이미지 파일 {image_path}이 존재하지 않습니다.")
        
        ret = self.lib.R600DrawWaterMark(x, y, width, height, image_path.encode('cp949'))
        self._check_result(ret, f"워터마크 그리기 ({image_path})")
    
    def draw_image(self, x: float, y: float, width: float, height: float, 
                   image_path: str, mode: int = 1):
        """이미지 그리기"""
        if not os.path.exists(image_path):
            raise R600PrinterError(f"이미지 파일 {image_path}이 존재하지 않습니다.")
        
        ret = self.lib.R600DrawImage(x, y, width, height, image_path.encode('cp949'), mode)
        self._check_result(ret, f"이미지 그리기 ({image_path})")
    
    def draw_layer_white(self, x: float, y: float, width: float, height: float, image_path: str):
        """화이트 레이어 그리기"""
        if not os.path.exists(image_path):
            raise R600PrinterError(f"이미지 파일 {image_path}이 존재하지 않습니다.")
        
        ret = self.lib.R600DrawLayerWhite(x, y, width, height, image_path.encode('cp949'))
        self._check_result(ret, f"화이트 레이어 그리기 ({image_path})")
    
    def commit_canvas(self) -> str:
        """캔버스 커밋"""
        img_info_buffer_size = 3072
        img_info_buffer = ctypes.create_string_buffer(img_info_buffer_size)
        p_img_info_len = ctypes.pointer(ctypes.c_uint(img_info_buffer_size))
        
        ret = self.lib.R600CommitCanvas(img_info_buffer, p_img_info_len)
        if ret != 0:
            raise R600PrinterError(f"캔버스 커밋 실패: {ret}")
        
        self.committed_img_info = img_info_buffer.value.decode('cp949')
        print(f"캔버스 커밋 성공. 이미지 정보: {self.committed_img_info}")
        print(f"실제 이미지 정보 길이: {p_img_info_len.contents.value}")
        
        return self.committed_img_info
    
    def print_draw(self, img_info: Optional[str] = None):
        """인쇄 실행"""
        if img_info is None:
            if self.committed_img_info is None:
                raise R600PrinterError("커밋된 이미지 정보가 없습니다. 먼저 commit_canvas()를 호출하세요.")
            img_info = self.committed_img_info
        
        ret = self.lib.R600PrintDraw(img_info.encode('cp949'), ctypes.c_char_p(None))
        self._check_result(ret, "인쇄 실행")
    
    def print_card(self, watermark_path: Optional[str] = None, image_path: Optional[str] = None,
                   card_width: float = 53.98, card_height: float = 85.6):
        """
        카드 인쇄 전체 프로세스
        
        Args:
            watermark_path: 워터마크 이미지 경로
            image_path: 메인 이미지 경로  
            card_width: 카드 너비 (mm)
            card_height: 카드 높이 (mm)
        """
        try:
            print("=== 카드 인쇄 시작 ===")
            
            # 1. 카드 삽입
            self.inject_card()
            
            # 2. 리본 옵션 설정
            self.set_ribbon_option()
            
            # 3. 캔버스 설정
            self.setup_canvas()
            
            # 4. 워터마크 그리기 (선택사항)
            if watermark_path:
                self.draw_watermark(0.0, 0.0, card_width, card_height, watermark_path)
            
            # 5. 메인 이미지 그리기 (선택사항)
            if image_path:
                self.draw_image(0.0, 0.0, card_width, card_height, image_path)
            
            # 6. 캔버스 커밋
            self.commit_canvas()
            
            # 7. 잠시 대기
            time.sleep(1)
            
            # 8. 인쇄 실행
            self.print_draw()
            
            # 9. 카드 배출
            self.eject_card()
            
            print("=== 카드 인쇄 완료 ===")
            
        except R600PrinterError as e:
            print(f"카드 인쇄 중 오류 발생: {e}")
            raise
    
    def close(self):
        """라이브러리 정리"""
        if self.lib:
            ret = self.lib.R600LibClear()
            print(f"라이브러리 정리: {ret}")
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.close()


def main():
    """메인 실행 함수"""
    try:
        # R600 프린터 인스턴스 생성 (컨텍스트 매니저 사용)
        with R600Printer() as printer:
            
            # 프린터 목록 조회
            printers = printer.enum_printers()
            if not printers:
                print("사용 가능한 프린터가 없습니다.")
                return
            
            # 타임아웃 설정
            printer.set_timeout(10000)
            
            # 첫 번째 프린터 선택
            printer.select_printer(printers[0])
            
            # 카드 인쇄 실행
            printer.print_card(
                watermark_path="12-B.jpg",  # 워터마크 이미지
                image_path="12.jpg"         # 메인 이미지
            )
            
    except R600PrinterError as e:
        print(f"프린터 오류: {e}")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")


if __name__ == "__main__":
    main()
    