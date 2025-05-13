# hiti_sdk/constants.py
"""
HiTi 프린터 API에서 사용되는 상수들 정의
"""
from enum import IntEnum, auto


class PaperType(IntEnum):
    """용지 유형 상수"""
    PHOTO_4X6 = 0
    PHOTO_5X7 = 4
    PHOTO_6X8 = 6
    PHOTO_6X9 = 12
    PHOTO_6X9_SPLIT_2UP = 14  # 6x9 용지에 4x6 2장
    PHOTO_4X6_SPLIT_2UP = 17  # 4x6 용지에 2x6 2장
    PHOTO_5X7_SPLIT_2UP = 19  # 5x7 용지에 5x3.5 2장
    PHOTO_4X6_SPLIT_3UP = 21  # 4x6 용지에 1.3x6 3장
    PHOTO_8X4 = 40            # 8x12 용지에 4x6 2장
    PHOTO_8X6 = 42            # 8x12 용지에 4x6 2장
    PHOTO_8X8 = 43            # 8x12 용지에 8x8 1장
    PHOTO_8X12 = 47           # 8x12 용지
    
    @classmethod
    def get_dimensions(cls, paper_type):
        """용지 유형에 따른 픽셀 크기 반환"""
        dimensions = {
            cls.PHOTO_4X6: (1240, 1844),
            cls.PHOTO_5X7: (1548, 2140),
            cls.PHOTO_6X8: (1844, 2434),
            cls.PHOTO_6X9: (1844, 2740),
            cls.PHOTO_6X9_SPLIT_2UP: (1844, 2492),
            cls.PHOTO_4X6_SPLIT_2UP: (1240, 1844),
            cls.PHOTO_5X7_SPLIT_2UP: (1548, 2152),
            cls.PHOTO_4X6_SPLIT_3UP: (1240, 1844),
            cls.PHOTO_8X4: (2464, 1236),
            cls.PHOTO_8X6: (2464, 1836),
            cls.PHOTO_8X8: (2464, 2436),
            cls.PHOTO_8X12: (2464, 3636),
        }
        return dimensions.get(paper_type, (1240, 1844))  # 기본값은 4x6


class Orientation(IntEnum):
    """인쇄 방향 상수"""
    PORTRAIT = 1   # 세로
    LANDSCAPE = 2  # 가로


class PrintMode(IntEnum):
    """인쇄 품질 모드 상수"""
    STANDARD = 0    # 표준 모드
    FINE = 1        # 고품질 모드


class PrintFlag(IntEnum):
    """인쇄 제어 플래그 상수"""
    NOT_SHOW_ERROR_MSG_DLG = 0x00000001    # 오류 메시지 대화 상자 표시 안 함
    WAIT_MSG_DONE = 0x00000002             # 메시지 처리가 완료될 때까지 대기
    NOT_SHOW_CLEAN_MSG = 0x00000100        # 청소 메시지 대화 상자 표시 안 함


class PrintCommand(IntEnum):
    """프린터 명령 상수"""
    RESET_PRINTER = 100      # 프린터 초기화
    LOCK_PRINTER = 101       # 프린터 잠금
    UNLOCK_PRINTER = 102     # 프린터 잠금 해제
    CUT_PAPER = 103          # 용지 절단


class DeviceInfoType(IntEnum):
    """장치 정보 유형 상수"""
    MFG_SERIAL = 1           # 제조 일련번호
    MODEL_NAME = 2           # 모델 이름
    FIRMWARE_VERSION = 3     # 펌웨어 버전
    RIBBON_INFO = 4          # 리본 정보
    PRINT_COUNT = 5          # 인쇄 카운트
    CUTTER_COUNT = 6         # 절단 카운트


class RibbonType(IntEnum):
    """리본 유형 상수"""
    RIBBON_4X6 = 1           # 4x6 리본
    RIBBON_5X7 = 2           # 5x7 리본
    RIBBON_6X9 = 3           # 6x9 리본
    RIBBON_6X8 = 4           # 6x8 리본
    RIBBON_5X3dot5 = 5       # 5x3.5 리본
    RIBBON_6X12 = 6          # 6x12 리본
    RIBBON_8X12 = 7          # 8x12 리본


class DeviceStatus(IntEnum):
    """장치 상태 코드 상수"""
    # 기본 상태
    OK = 0                        # 정상
    BUSY = 0x00080000             # 프린터가 사용 중
    OFFLINE = 0x00000080          # 프린터가 오프라인 상태
    PRINTING = 0x00000400         # 프린터가 인쇄 중
    PROCESSING_DATA = 0x00000005  # 드라이버가 인쇄 데이터 처리 중
    SENDING_DATA = 0x00000006     # 드라이버가 데이터를 프린터로 전송 중
    
    # 커버 관련 오류
    COVER_OPEN = 0x00050001       # 커버 열림
    COVER_OPEN2 = 0x00050101      # 커버 열림 (추가)
    
    # 용지 관련 오류
    PAPER_OUT = 0x00008000        # 용지 없음
    PAPER_JAM = 0x00030000        # 용지 걸림
    PAPER_TYPE_MISMATCH = 0x000100FE  # 용지 유형 불일치
    PAPER_TRAY_MISMATCH = 0x00008010  # 용지 트레이 불일치
    TRAY_MISSING = 0x00008008     # 용지 트레이 없음
    
    # 리본 관련 오류
    RIBBON_MISSING = 0x00080004   # 리본 없음
    OUT_OF_RIBBON = 0x00080103    # 리본 부족
    RIBBON_TYPE_MISMATCH = 0x00080200  # 리본 유형 불일치
    RIBBON_ERROR = 0x000802FE     # 리본 오류
    
    # 하드웨어 관련 오류
    SRAM_ERROR = 0x00030001       # SRAM 오류
    SDRAM_ERROR = 0x00030101      # SDRAM 오류
    ADC_ERROR = 0x00030201        # ADC 오류
    NVRAM_ERROR = 0x00030301      # NVRAM 읽기/쓰기 오류
    FW_CHECKSUM_ERROR = 0x00030302  # 체크섬 오류 - SDRAM
    DSP_CHECKSUM_ERROR = 0x00030402  # DSP 코드 체크섬 오류
    HEAT_PARAMETER_INCOMPATIBLE = 0x000304FE  # 가열 매개변수 테이블 호환되지 않음
    CAM_PLATEN_ERROR = 0x00030501  # Cam Platen 오류
    ADF_ERROR = 0x00030601        # ADF Cam 오류
    
    # 통신 관련 오류
    WRITE_FAIL = 0x0000001F       # 프린터로 데이터 전송 실패
    READ_FAIL = 0x0000002F        # 프린터에서 데이터 수신 실패
    
    @classmethod
    def get_description(cls, status_code):
        """상태 코드에 대한 설명 반환"""
        descriptions = {
            cls.OK: "정상",
            cls.BUSY: "프린터가 사용 중입니다",
            cls.OFFLINE: "프린터가 오프라인 상태입니다",
            cls.PRINTING: "프린터가 인쇄 중입니다",
            cls.COVER_OPEN: "커버가 열려 있습니다",
            cls.COVER_OPEN2: "커버가 열려 있습니다",
            cls.PAPER_OUT: "용지가 없습니다",
            cls.PAPER_JAM: "용지 걸림이 발생했습니다",
            cls.PAPER_TYPE_MISMATCH: "용지 유형이 일치하지 않습니다",
            cls.PAPER_TRAY_MISMATCH: "용지 트레이가 일치하지 않습니다",
            cls.TRAY_MISSING: "용지 트레이가 없습니다",
            cls.RIBBON_MISSING: "리본이 없습니다",
            cls.OUT_OF_RIBBON: "리본이 부족합니다",
            cls.RIBBON_TYPE_MISMATCH: "리본 유형이 일치하지 않습니다",
            cls.RIBBON_ERROR: "리본 오류가 발생했습니다",
            cls.WRITE_FAIL: "프린터로 데이터 전송이 실패했습니다",
            cls.READ_FAIL: "프린터에서 데이터 수신이 실패했습니다",
            cls.PROCESSING_DATA: "드라이버가 인쇄 데이터를 처리 중입니다",
            cls.SENDING_DATA: "드라이버가 데이터를 프린터로 전송 중입니다",
            0x00000002: "인쇄 진행 중",  # 추가: 프린터 상태 코드 0x00000002,
        }
        return descriptions.get(status_code, f"알 수 없는 상태 코드: 0x{status_code:08X}")


# P720L/P728L/P520L/P750L 전용 추가 오류 코드
class DeviceStatusP7xx(IntEnum):
    """P720L/P728L/P520L/P750L 전용 상태 코드"""
    COVER_OPEN = 0x00000100
    COVER_OPEN_FAIL = 0x00000101
    IC_CHIP_MISSING = 0x00000200
    RIBBON_MISSING = 0x00000201
    RIBBON_MISMATCH_01 = 0x00000202
    SECURITY_CHECK_FAIL = 0x00000203
    RIBBON_MISMATCH_02 = 0x00000204
    RIBBON_MISMATCH_03 = 0x00000205
    RIBBON_OUT_01 = 0x00000300
    RIBBON_OUT_02 = 0x00000301
    PRINTING_FAIL = 0x00000302
    PAPER_OUT_01 = 0x00000400
    PAPER_OUT_02 = 0x00000401
    PAPER_NOT_READY = 0x00000402
    PAPER_JAM_01 = 0x00000500
    PAPER_JAM_02 = 0x00000501
    PAPER_JAM_03 = 0x00000502
    PAPER_JAM_04 = 0x00000503
    PAPER_JAM_05 = 0x00000504
    PAPER_MISMATCH = 0x00000600
    CAM_ERROR_01 = 0x00000700
    CAM_ERROR_02 = 0x00000800
    NVRAM_ERROR = 0x00000900
    IC_CHIP_ERROR = 0x00000A00
    ADC_ERROR = 0x00000C00
    FW_CHECK_ERROR = 0x00000D00
    CUTTER_ERROR = 0x00000F00