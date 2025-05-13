# hiti_sdk/__init__.py
"""
HiTi 프린터 SDK
===============

HiTi 프린터를 제어하기 위한 Python SDK 패키지입니다.
GDI 없이 명령어로 직접 프린터를 제어할 수 있습니다.
키오스크와 같은 응용 프로그램에 적합합니다.
"""

from .printer import HiTiPrinter, PrinterStatus, PaperType, Orientation, PrintMode
from .exceptions import PrinterError, ConnectionError, PrintError
from .device import find_printers, HiTiDevice
from .constants import DeviceStatus, RibbonType, PrintCommand, DeviceInfoType
from .image import prepare_image

__version__ = "0.1.0"
__all__ = [
    "HiTiPrinter", 
    "PrinterStatus", 
    "PaperType", 
    "Orientation", 
    "PrintMode",
    "PrinterError", 
    "ConnectionError", 
    "PrintError",
    "find_printers",
    "HiTiDevice",
    "DeviceStatus",
    "RibbonType",
    "PrintCommand",
    "DeviceInfoType",
    "prepare_image"
]