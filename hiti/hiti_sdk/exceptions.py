# hiti_sdk/exceptions.py
"""
HiTi 프린터 SDK 예외 클래스 정의
"""


class PrinterError(Exception):
    """HiTi 프린터 관련 기본 예외 클래스"""
    def __init__(self, message, error_code=None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        if self.error_code is not None:
            return f"{self.message} (오류 코드: 0x{self.error_code:08X})"
        return self.message


class ConnectionError(PrinterError):
    """프린터 연결 관련 예외"""
    pass


class PrintError(PrinterError):
    """인쇄 관련 예외"""
    pass


class DeviceError(PrinterError):
    """장치 오류 관련 예외"""
    pass


class StatusError(PrinterError):
    """프린터 상태 관련 예외"""
    pass


class ImageError(PrinterError):
    """이미지 처리 관련 예외"""
    pass


class DLLError(PrinterError):
    """DLL 로드 및 함수 호출 관련 예외"""
    pass