# hiti_sdk/printer.py
"""
HiTi 프린터 제어를 위한 고수준 인터페이스
"""
import os
import sys
import logging
import time
import ctypes
from enum import IntEnum, auto
from pathlib import Path

from .constants import PaperType, Orientation, PrintMode, PrintFlag, DeviceStatus
from .exceptions import PrinterError, ConnectionError, PrintError, StatusError, ImageError
from .device import HiTiDevice, find_printers, HITI_JOB_PROPERTY_RT
from .image import prepare_image, create_split_image, ImageData

# 로깅 설정
logger = logging.getLogger(__name__)


class PrinterStatus(IntEnum):
    """프린터 상태"""
    READY = auto()           # 인쇄 준비 완료
    BUSY = auto()            # 사용 중
    PRINTING = auto()        # 인쇄 중
    ERROR = auto()           # 오류 상태
    OFFLINE = auto()         # 오프라인
    UNKNOWN = auto()         # 알 수 없는 상태


class HiTiPrinter:
    """HiTi 프린터 제어 클래스"""
    def __init__(self, printer_name=None):
        """
        HiTi 프린터를 초기화합니다.
        
        Args:
            printer_name (str, optional): 프린터 이름. None인 경우 첫 번째 발견된 프린터 사용
            
        Raises:
            ConnectionError: 프린터에 연결할 수 없는 경우
        """
        self.device = None
        
        if printer_name is None:
            # 자동으로 프린터 검색
            printers = find_printers()
            if not printers:
                raise ConnectionError("연결된 HiTi 프린터를 찾을 수 없습니다.")
            self.device = printers[0]
            logger.info(f"첫 번째 발견된 프린터 사용: {self.device.printer_name}")
        else:
            # 지정된 프린터 사용
            self.device = HiTiDevice(printer_name)
            logger.info(f"지정된 프린터 사용: {printer_name}")
        
        # 프린터 상태 확인
        self._check_connectivity()
    
    def _check_connectivity(self):
        """프린터 연결 상태 확인"""
        try:
            status_code, _ = self.device.check_status()
            if status_code == DeviceStatus.OFFLINE:
                raise ConnectionError("프린터가 오프라인 상태입니다.")
        except Exception as e:
            raise ConnectionError(f"프린터 연결 확인 중 오류 발생: {e}")
    
    def get_status(self):
        """
        프린터 상태를 확인합니다.
        
        Returns:
            tuple: (PrinterStatus, str) - 상태 코드와 설명
            
        Raises:
            StatusError: 상태 확인 실패 시
        """
        try:
            status_code, status_desc = self.device.check_status()
            
            if status_code == 0:
                return PrinterStatus.READY, "준비 완료"
            elif status_code == DeviceStatus.BUSY:
                return PrinterStatus.BUSY, "사용 중"
            elif status_code == DeviceStatus.PRINTING:
                return PrinterStatus.PRINTING, "인쇄 중"
            elif status_code == DeviceStatus.OFFLINE:
                return PrinterStatus.OFFLINE, "오프라인"
            else:
                return PrinterStatus.ERROR, status_desc
                
        except Exception as e:
            logger.error(f"프린터 상태 확인 중 오류 발생: {e}")
            raise StatusError(f"프린터 상태 확인 실패: {e}")
    
    def wait_until_ready(self, timeout=60):
        """
        프린터가 준비될 때까지 대기합니다.
        
        Args:
            timeout (float): 최대 대기 시간(초)
            
        Returns:
            bool: 프린터가 준비되었으면 True, 그렇지 않으면 False
            
        Raises:
            StatusError: 상태 확인 중 오류 발생 시
        """
        try:
            return self.device.wait_until_ready(timeout)
        except Exception as e:
            logger.error(f"프린터 대기 중 오류 발생: {e}")
            raise StatusError(f"프린터 대기 실패: {e}")
    
    def print_image(self, image_path, paper_type=PaperType.PHOTO_4X6, 
                orientation=Orientation.PORTRAIT, copies=1, print_mode=PrintMode.STANDARD,
                apply_matte=False, wait_for_completion=False, timeout=120):
        """
        이미지를 인쇄합니다.
        
        Args:
            image_path (str): 인쇄할 이미지 파일 경로
            paper_type (PaperType): 용지 유형
            orientation (Orientation): 인쇄 방향
            copies (int): 인쇄 매수
            print_mode (PrintMode): 인쇄 품질 모드
            apply_matte (bool): 무광택 코팅 적용 여부
            wait_for_completion (bool): 인쇄 완료까지 대기 여부
            timeout (float): 최대 대기 시간(초)
            
        Returns:
            bool: 성공 여부
            
        Raises:
            PrintError: 인쇄 실패 시
            ImageError: 이미지 처리 실패 시
        """
        try:
            # 이미지 경로 확인
            if not os.path.exists(image_path):
                raise ImageError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
            
            # 프린터 상태 확인
            status, status_desc = self.get_status()
            if status not in [PrinterStatus.READY, PrinterStatus.BUSY]:
                if status == PrinterStatus.ERROR:
                    raise PrintError(f"프린터 오류 상태: {status_desc}")
                elif status == PrinterStatus.OFFLINE:
                    raise PrintError("프린터가 오프라인 상태입니다.")
                elif status == PrinterStatus.PRINTING:
                    if not wait_for_completion:
                        raise PrintError("프린터가 이미 인쇄 중입니다.")
                    # 인쇄 중이면 완료될 때까지 대기
                    if not self.wait_until_ready(timeout):
                        raise PrintError("인쇄 중인 작업이 완료될 때까지 기다리는 동안 타임아웃 발생")
            
            # 이미지 준비
            image_data = prepare_image(image_path, paper_type, orientation)
            
            # 복수 매수 처리 방식 변경 - 한 장씩 개별 인쇄
            actual_copies = 1  # 항상 1로 설정
            success = True
            
            for i in range(copies):
                # 반복 인쇄 시 프린터 상태 확인
                if i > 0:
                    # 프린터가 준비될 때까지 대기
                    logger.info(f"다음 인쇄({i+1}/{copies})를 위해 프린터가 준비될 때까지 대기...")
                    if not self.wait_until_ready(30):  # 30초 타임아웃
                        raise PrintError(f"프린터가 준비 상태가 아닙니다. 매수 {i+1}/{copies} 인쇄 중단")
                
                # 인쇄 작업 속성 설정
                job_prop = HITI_JOB_PROPERTY_RT()
                job_prop.dwSize = ctypes.sizeof(HITI_JOB_PROPERTY_RT)
                job_prop.hParentWnd = None
                job_prop.dwPaperType = paper_type
                job_prop.dwPrintMode = print_mode
                job_prop.shOrientation = orientation
                job_prop.shCopies = actual_copies  # 항상 1장씩만 인쇄
                job_prop.dwFlags = PrintFlag.NOT_SHOW_ERROR_MSG_DLG
                job_prop.dwApplyMatte = 1 if apply_matte else 0
                
                # 비트맵 생성
                bitmap = image_data.to_bitmap()
                
                # 인쇄 실행
                if i == 0:
                    logger.info(f"이미지 인쇄 시작: {image_path}, 용지: {paper_type}, 방향: {orientation}, 매수: {copies} (1/{copies})")
                else:
                    logger.info(f"이미지 인쇄 계속: {i+1}/{copies}")
                    
                printer_name_bytes = self.device.printer_name.encode('utf-8')
                
                result = self.device.dll.print_one_page(
                    printer_name_bytes, 
                    ctypes.byref(job_prop), 
                    ctypes.byref(bitmap)
                )
                
                if result != 0 and result != 1801:  # 1801은 일부 프린터에서 성공 코드
                    raise PrintError(f"인쇄 작업 시작 실패 (매수 {i+1}/{copies})", result)
                
                logger.info(f"인쇄 작업 {i+1}/{copies}이(가) 성공적으로 시작되었습니다.")
                
                # 인쇄 완료까지 대기 (마지막 인쇄가 아닌 경우)
                if wait_for_completion and i < copies - 1:
                    logger.info(f"인쇄 완료까지 대기 중 ({i+1}/{copies})...")
                    start_time = time.time()
                    
                    while time.time() - start_time < (timeout // copies):
                        try:
                            status_code, status_desc = self.device.check_status()
                            
                            # 0x00000002는 인쇄 진행 중 상태 - 정상적인 상태이므로 계속 대기
                            if status_code == 0x00000002:
                                logger.debug(f"인쇄 진행 중... (0x{status_code:08X})")
                                time.sleep(1)
                                continue
                                
                            # 준비 완료 상태 확인
                            if status_code == 0:
                                logger.info(f"인쇄 {i+1}/{copies}이(가) 완료되었습니다.")
                                break
                                
                            # 심각한 오류 상태 확인
                            if (status_code & 0x00080000) or (status_code & 0x00008000):
                                raise PrintError(f"인쇄 중 오류 발생: {status_desc}", status_code)
                                
                            # 그 외 상태는 계속 대기
                            logger.debug(f"프린터 상태: {status_desc} (0x{status_code:08X})")
                            
                        except Exception as e:
                            if isinstance(e, PrintError):
                                raise
                            logger.warning(f"상태 확인 중 오류: {e}")
                        
                        time.sleep(1)  # 1초마다 확인
            
            # 마지막 인쇄 완료 대기 (wait_for_completion이 True인 경우)
            if wait_for_completion:
                logger.info(f"마지막 인쇄 완료까지 최대 {timeout//2}초 대기 중...")
                start_time = time.time()
                
                while time.time() - start_time < (timeout // 2):
                    status, _ = self.get_status()
                    
                    if status == PrinterStatus.READY:
                        logger.info("모든 인쇄가 완료되었습니다.")
                        return True
                    
                    if status == PrinterStatus.ERROR:
                        status_code, status_desc = self.device.check_status()
                        raise PrintError(f"인쇄 중 오류 발생: {status_desc}", status_code)
                    
                    time.sleep(1)  # 1초마다 확인
                
                # 타임아웃
                logger.warning(f"마지막 인쇄 완료 대기 중 타임아웃 발생 ({timeout//2}초)")
            
            return True
            
        except ImageError as e:
            # 이미지 오류는 그대로 전달
            raise
        except Exception as e:
            logger.error(f"인쇄 중 오류 발생: {e}")
            if isinstance(e, PrintError):
                raise
            raise PrintError(f"이미지 인쇄 중 오류 발생: {e}")
        
    def print_split_images(self, image_paths, paper_type=PaperType.PHOTO_6X9_SPLIT_2UP, 
                          orientation=Orientation.PORTRAIT, copies=1, print_mode=PrintMode.STANDARD,
                          apply_matte=False, wait_for_completion=False, timeout=120):
        """
        여러 이미지를 하나의 용지에 분할 인쇄합니다.
        
        Args:
            image_paths (list): 인쇄할 이미지 파일 경로 목록
            paper_type (PaperType): 용지 유형 (분할 타입이어야 함)
            orientation (Orientation): 인쇄 방향
            copies (int): 인쇄 매수
            print_mode (PrintMode): 인쇄 품질 모드
            apply_matte (bool): 무광택 코팅 적용 여부
            wait_for_completion (bool): 인쇄 완료까지 대기 여부
            timeout (float): 최대 대기 시간(초)
            
        Returns:
            bool: 성공 여부
            
        Raises:
            PrintError: 인쇄 실패 시
            ImageError: 이미지 처리 실패 시
        """
        try:
            # 용지 타입 확인
            if paper_type not in [
                PaperType.PHOTO_6X9_SPLIT_2UP, 
                PaperType.PHOTO_4X6_SPLIT_2UP, 
                PaperType.PHOTO_5X7_SPLIT_2UP, 
                PaperType.PHOTO_4X6_SPLIT_3UP
            ]:
                raise ValueError(f"분할 인쇄에 적합하지 않은 용지 타입: {paper_type}")
            
            # 이미지 경로 확인
            for path in image_paths:
                if not os.path.exists(path):
                    raise ImageError(f"이미지 파일을 찾을 수 없습니다: {path}")
            
            # 프린터 상태 확인
            status, status_desc = self.get_status()
            if status not in [PrinterStatus.READY, PrinterStatus.BUSY]:
                if status == PrinterStatus.ERROR:
                    raise PrintError(f"프린터 오류 상태: {status_desc}")
                elif status == PrinterStatus.OFFLINE:
                    raise PrintError("프린터가 오프라인 상태입니다.")
                elif status == PrinterStatus.PRINTING:
                    if not wait_for_completion:
                        raise PrintError("프린터가 이미 인쇄 중입니다.")
                    # 인쇄 중이면 완료될 때까지 대기
                    if not self.wait_until_ready(timeout):
                        raise PrintError("인쇄 중인 작업이 완료될 때까지 기다리는 동안 타임아웃 발생")
            
            # 분할 이미지 생성
            image_data = create_split_image(image_paths, paper_type, orientation)
            
            # 인쇄 작업 속성 설정
            job_prop = HITI_JOB_PROPERTY_RT()
            job_prop.dwSize = ctypes.sizeof(HITI_JOB_PROPERTY_RT)
            job_prop.hParentWnd = None
            job_prop.dwPaperType = paper_type
            job_prop.dwPrintMode = print_mode
            job_prop.shOrientation = orientation
            job_prop.shCopies = copies
            job_prop.dwFlags = PrintFlag.NOT_SHOW_ERROR_MSG_DLG
            job_prop.dwApplyMatte = 1 if apply_matte else 0
            
            # 비트맵 생성
            bitmap = image_data.to_bitmap()
            
            # 인쇄 실행
            logger.info(f"분할 이미지 인쇄 시작: {len(image_paths)}개 이미지, 용지: {paper_type}, 방향: {orientation}, 매수: {copies}")
            printer_name_bytes = self.device.printer_name.encode('utf-8')
            
            result = self.device.dll.print_one_page(
                printer_name_bytes, 
                ctypes.byref(job_prop), 
                ctypes.byref(bitmap)
            )
            
            if result != 0 and result != 1801:
                raise PrintError(f"인쇄 작업 시작 실패", result)
            
            logger.info("인쇄 작업이 성공적으로 시작되었습니다.")
            
            # 인쇄 완료까지 대기
            if wait_for_completion:
                logger.info(f"인쇄 완료까지 최대 {timeout}초 대기 중...")
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    status, _ = self.get_status()
                    
                    if status == PrinterStatus.READY:
                        logger.info("인쇄가 완료되었습니다.")
                        return True
                    
                    if status == PrinterStatus.ERROR:
                        status_code, status_desc = self.device.check_status()
                        raise PrintError(f"인쇄 중 오류 발생: {status_desc}", status_code)
                    
                    time.sleep(1)  # 1초마다 확인
                
                # 타임아웃
                raise PrintError(f"인쇄 완료 대기 중 타임아웃 발생 ({timeout}초)")
            
            return True
            
        except ImageError as e:
            # 이미지 오류는 그대로 전달
            raise
        except Exception as e:
            logger.error(f"분할 인쇄 중 오류 발생: {e}")
            if isinstance(e, PrintError):
                raise
            raise PrintError(f"분할 이미지 인쇄 중 오류 발생: {e}")
    
    def get_device_info(self):
        """
        프린터 장치 정보를 가져옵니다.
        
        Returns:
            dict: 프린터 정보
            
        Raises:
            PrinterError: 정보 조회 실패 시
        """
        try:
            from .constants import DeviceInfoType
            
            serial = self.device.get_device_info(DeviceInfoType.MFG_SERIAL)
            model = self.device.get_device_info(DeviceInfoType.MODEL_NAME)
            firmware = self.device.get_device_info(DeviceInfoType.FIRMWARE_VERSION)
            ribbon_info = self.device.get_device_info(DeviceInfoType.RIBBON_INFO)
            print_count = self.device.get_device_info(DeviceInfoType.PRINT_COUNT)
            
            return {
                "serial_number": serial,
                "model_name": model,
                "firmware_version": firmware,
                "ribbon_type": ribbon_info["type"],
                "ribbon_type_name": ribbon_info["type_name"],
                "ribbon_count": ribbon_info["count"],
                "print_count": print_count
            }
        except Exception as e:
            logger.error(f"장치 정보 조회 중 오류 발생: {e}")
            raise PrinterError(f"프린터 정보 조회 실패: {e}")
    
    def reset(self):
        """프린터를 재설정합니다."""
        return self.device.reset()
    
    def cut_paper(self):
        """용지를 절단합니다."""
        return self.device.cut_paper()