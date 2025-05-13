# hiti_sdk/image.py
"""
HiTi 프린터를 위한 이미지 처리 기능
"""
import os
import sys
import ctypes
import logging
from pathlib import Path
from PIL import Image

from .constants import PaperType, Orientation
from .exceptions import ImageError

# 로깅 설정
logger = logging.getLogger(__name__)


class ImageData:
    """HiTi 프린터에서 사용하는 이미지 데이터 클래스"""
    def __init__(self, width, height, data_buffer, bits_per_pixel=24):
        """
        이미지 데이터를 초기화합니다.
        
        Args:
            width (int): 이미지 너비 (픽셀)
            height (int): 이미지 높이 (픽셀)
            data_buffer (bytes): BGR 형식의 이미지 데이터
            bits_per_pixel (int): 픽셀당 비트 수 (기본값: 24)
        """
        self.width = width
        self.height = height
        self.data_buffer = data_buffer
        self.bits_per_pixel = bits_per_pixel
        self.width_bytes = ((width * (bits_per_pixel // 8) + 3) // 4) * 4  # 4바이트 정렬
    
    def to_bitmap(self):
        """이미지 데이터를 BITMAP 구조체로 변환"""
        from .device import BITMAP
        
        # 비트맵 구조체 설정
        bitmap = BITMAP()
        bitmap.bmType = 0  # 0 = 디바이스 의존적 비트맵
        bitmap.bmWidth = self.width
        bitmap.bmHeight = self.height
        bitmap.bmWidthBytes = self.width_bytes
        bitmap.bmPlanes = 1
        bitmap.bmBitsPixel = self.bits_per_pixel
        
        # 비트맵 데이터를 C 메모리로 복사
        buffer_size = len(self.data_buffer)
        c_buffer = (ctypes.c_ubyte * buffer_size)()
        ctypes.memmove(c_buffer, self.data_buffer, buffer_size)
        
        bitmap.bmBits = ctypes.cast(c_buffer, ctypes.c_void_p)
        
        # 참조 유지 (GC 방지)
        bitmap._buffer = c_buffer
        
        return bitmap


def prepare_image(image_path, paper_type=PaperType.PHOTO_4X6, orientation=Orientation.PORTRAIT):
    """
    이미지 파일을 HiTi 프린터 인쇄에 적합한 형식으로 준비합니다.
    
    Args:
        image_path (str): 이미지 파일 경로
        paper_type (PaperType): 용지 유형
        orientation (Orientation): 인쇄 방향 (1=세로, 2=가로)
        
    Returns:
        ImageData: 처리된 이미지 데이터
        
    Raises:
        ImageError: 이미지 처리 실패 시
    """
    try:
        # 이미지 로드
        img = Image.open(image_path)
        logger.info(f"이미지 로드: {image_path} (크기: {img.size}, 모드: {img.mode})")
        
        # 용지 크기 가져오기
        paper_width, paper_height = PaperType.get_dimensions(paper_type)
        
        # 인쇄 방향에 따라 용지 크기 조정
        if orientation == Orientation.LANDSCAPE:
            paper_width, paper_height = paper_height, paper_width
        
        # 이미지 크기 조정
        img = img.resize((paper_width, paper_height), Image.LANCZOS)
        
        # RGB 모드로 변환
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 이미지 데이터 추출 (BGR 형식으로 변환, 4바이트 경계로 정렬)
        width, height = img.size
        rowsize = ((width * 3 + 3) // 4) * 4  # 4바이트 경계로 정렬된 행 크기
        
        # 비트맵 데이터 생성
        bitmap_data = bytearray(rowsize * height)
        
        # 이미지 데이터를 BGR 형식으로 변환
        for y in range(height):
            for x in range(width):
                r, g, b = img.getpixel((x, y))
                idx = y * rowsize + x * 3
                bitmap_data[idx:idx+3] = bytes([b, g, r])  # RGB -> BGR
        
        # 메모리 누수 방지를 위해 이미지 객체 닫기
        img.close()
        
        logger.info(f"이미지 준비 완료: {width}x{height}, {rowsize} 바이트/행, 24비트/픽셀")
        
        return ImageData(width, height, bytes(bitmap_data))
        
    except Exception as e:
        logger.error(f"이미지 준비 중 오류 발생: {e}")
        raise ImageError(f"이미지 '{image_path}' 처리 중 오류 발생: {e}")


def create_split_image(image_paths, paper_type=PaperType.PHOTO_6X9_SPLIT_2UP, orientation=Orientation.PORTRAIT):
    """
    여러 이미지를 하나의 용지에 분할 인쇄하기 위한 이미지를 생성합니다.
    
    Args:
        image_paths (list): 이미지 파일 경로 목록
        paper_type (PaperType): 용지 유형 
        orientation (Orientation): 인쇄 방향
        
    Returns:
        ImageData: 처리된 이미지 데이터
        
    Raises:
        ImageError: 이미지 처리 실패 시
    """
    try:
        # 전체 용지 크기
        paper_width, paper_height = PaperType.get_dimensions(paper_type)
        
        # 인쇄 방향에 따라 용지 크기 조정
        if orientation == Orientation.LANDSCAPE:
            paper_width, paper_height = paper_height, paper_width
        
        # 분할 방식 확인
        if paper_type == PaperType.PHOTO_6X9_SPLIT_2UP:
            # 6x9 용지에 4x6 사진 2장 배치 (가로 분할)
            image_count = 2
            sub_width = paper_width
            sub_height = paper_height // 2
            layout = 'horizontal'
        elif paper_type == PaperType.PHOTO_4X6_SPLIT_2UP:
            # 4x6 용지에 2x6 사진 2장 배치 (세로 분할)
            image_count = 2
            sub_width = paper_width // 2
            sub_height = paper_height
            layout = 'vertical'
        elif paper_type == PaperType.PHOTO_5X7_SPLIT_2UP:
            # 5x7 용지에 5x3.5 사진 2장 배치 (가로 분할)
            image_count = 2
            sub_width = paper_width
            sub_height = paper_height // 2
            layout = 'horizontal'
        elif paper_type == PaperType.PHOTO_4X6_SPLIT_3UP:
            # 4x6 용지에 1.3x6 사진 3장 배치 (세로 분할)
            image_count = 3
            sub_width = paper_width // 3
            sub_height = paper_height
            layout = 'vertical'
        else:
            raise ValueError(f"지원하지 않는 분할 용지 유형: {paper_type}")
        
        # 전체 이미지 생성
        composite = Image.new('RGB', (paper_width, paper_height))
        
        # 이미지 개수 확인
        if len(image_paths) < image_count:
            logger.warning(f"이미지가 부족합니다: {len(image_paths)}/{image_count}")
        elif len(image_paths) > image_count:
            logger.warning(f"이미지가 초과됩니다: {len(image_paths)}/{image_count}. 처음 {image_count}개만 사용합니다.")
        
        # 이미지 배치
        for i, path in enumerate(image_paths[:image_count]):
            img = Image.open(path)
            
            # RGB 모드로 변환
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 이미지 크기 조정
            img = img.resize((sub_width, sub_height), Image.LANCZOS)
            
            # 이미지 위치 계산
            if layout == 'horizontal':
                # 가로 분할
                x, y = 0, i * sub_height
            else:
                # 세로 분할
                x, y = i * sub_width, 0
            
            # 이미지 배치
            composite.paste(img, (x, y))
            
            # 메모리 누수 방지
            img.close()
        
        # 이미지 데이터 추출 (BGR 형식으로 변환, 4바이트 경계로 정렬)
        width, height = composite.size
        rowsize = ((width * 3 + 3) // 4) * 4  # 4바이트 경계로 정렬된 행 크기
        
        # 비트맵 데이터 생성
        bitmap_data = bytearray(rowsize * height)
        
        # 이미지 데이터를 BGR 형식으로 변환
        for y in range(height):
            for x in range(width):
                r, g, b = composite.getpixel((x, y))
                idx = y * rowsize + x * 3
                bitmap_data[idx:idx+3] = bytes([b, g, r])  # RGB -> BGR
        
        # 메모리 누수 방지
        composite.close()
        
        logger.info(f"분할 이미지 준비 완료: {width}x{height}, {rowsize} 바이트/행, 24비트/픽셀")
        
        return ImageData(width, height, bytes(bitmap_data))
        
    except Exception as e:
        logger.error(f"분할 이미지 준비 중 오류 발생: {e}")
        raise ImageError(f"분할 이미지 처리 중 오류 발생: {e}")