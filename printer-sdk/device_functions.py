from cffi_defs import ffi, lib
from pathlib import Path

def get_device_list():
    printer_list = ffi.new("SMART_PRINTER_LIST *")
    result = lib.SmartComm_GetDeviceList2(printer_list)
    return result, printer_list

def get_device_id(printer_list, index):
    return printer_list.item[index].id

def open_device(device_id, open_device_by):
    device_handle = ffi.new("HSMART *")
    result = lib.SmartComm_OpenDevice2(device_handle, device_id, open_device_by)
    return result, device_handle[0]

def draw_image(device_handle, page, panel, x, y, cx, cy, image_filename):
    image_path = Path(__file__).parent / "resources" / image_filename
    image_path_str = str(image_path.resolve())
    image = ffi.new("wchar_t[]", image_path_str)
    rect_area = ffi.new("RECT *")
    result = lib.SmartComm_DrawImage(device_handle, page, panel, x, y, cx, cy, image, rect_area)
    return result

def get_preview_bitmap(device_handle, page):
    p_bitmap_info = ffi.new("BITMAPINFO **")
    result = lib.SmartComm_GetPreviewBitmap(device_handle, page, p_bitmap_info)
    return result, p_bitmap_info[0]

def print_image(device_handle):
    result = lib.SmartComm_Print(device_handle)
    return result

def close_device(device_handle):
    lib.SmartComm_CloseDevice(device_handle)

