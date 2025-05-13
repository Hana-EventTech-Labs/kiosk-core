# examples/kiosk_print.py
"""
HiTi 프린터 SDK를 이용한 키오스크 인쇄 예제

이 예제는 키오스크 응용프로그램에서 HiTi 프린터를 사용하여 
사진을 인쇄하는 기본적인 방법을 보여줍니다.
"""
import os
import sys
import logging
import time
import argparse
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('hiti_print.log')
    ]
)

logger = logging.getLogger("hiti_kiosk")

# 모듈 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import hiti_sdk
    from hiti_sdk import (
        HiTiPrinter, 
        PaperType, 
        Orientation, 
        PrintMode,
        PrinterError, 
        ConnectionError, 
        PrintError
    )
except ImportError as e:
    logger.error(f"HiTi SDK 가져오기 실패: {e}")
    sys.exit(1)


def print_device_info(printer):
    """프린터 장치 정보 출력"""
    try:
        info = printer.get_device_info()
        
        print("\n===== 프린터 정보 =====")
        print(f"모델명: {info['model_name']}")
        print(f"시리얼 번호: {info['serial_number']}")
        print(f"펌웨어 버전: {info['firmware_version']}")
        print(f"리본 유형: {info['ribbon_type_name']} ({info['ribbon_type']})")
        print(f"남은 리본 수: {info['ribbon_count']}")
        print(f"총 인쇄 횟수: {info['print_count']}")
        print("=====================\n")
        
        return True
    except Exception as e:
        logger.error(f"프린터 정보 조회 실패: {e}")
        return False


def print_photo(printer, image_path, copies=1):
    """단일 사진 인쇄"""
    try:
        # 상태 확인
        status, desc = printer.get_status()
        print(f"프린터 상태: {desc}")
        
        # 용지 정보 출력
        print("용지 크기: 6x8 (고정)")
        print("인쇄 방향: 가로 (고정)")
        
        # 인쇄 매수만큼 반복
        success = True
        for i in range(copies):
            # 첫 번째 인쇄가 아닌 경우, 프린터가 준비될 때까지 대기
            if i > 0:
                print(f"다음 인쇄({i+1}/{copies})를 위해 대기 중...")
                
                # 최대 30초 동안 기다림
                for wait_time in range(30):
                    try:
                        status_code, status_desc = printer.device.check_status()
                        
                        # 인쇄 진행 중(0x00000002) 상태이면 계속 대기
                        if status_code == 0x00000002:
                            print(f"인쇄 진행 중... ({wait_time+1}초 경과)")
                            time.sleep(1)
                            continue
                            
                        # 준비 완료(0)이면 다음 인쇄 진행
                        if status_code == 0:
                            print("프린터 준비 완료, 다음 인쇄 시작")
                            break
                            
                        # 그 외 상태인 경우, 심각한 오류인지 확인
                        if (status_code & 0x00080000) or (status_code & 0x00008000):
                            print(f"프린터 오류 발생: {status_desc}")
                            return False
                            
                    except Exception as e:
                        print(f"상태 확인 중 오류: {e}")
                    
                    time.sleep(1)
            
            # 현재 인쇄 시작
            print(f"'{image_path}' 인쇄 중... ({i+1}/{copies})")
            
            try:
                # 인쇄 작업 실행 (한 장씩)
                result = printer.print_image(
                    image_path=image_path,
                    paper_type=PaperType.PHOTO_4X6,
                    orientation=Orientation.PORTRAIT,  # 가로 방향 (고정)
                    copies=1,  # 항상 1장씩
                    print_mode=PrintMode.STANDARD,
                    apply_matte=False,
                    wait_for_completion=False,  # 대기하지 않음 (직접 관리)
                    timeout=30
                )
                
                if result:
                    print(f"인쇄 작업 {i+1}/{copies} 시작됨")
                else:
                    print(f"인쇄 작업 {i+1}/{copies} 시작 실패")
                    success = False
                    break
                
            except Exception as e:
                # 0x00000002(인쇄 진행 중) 오류는 무시
                if "0x00000002" in str(e):
                    print(f"인쇄 작업 {i+1}/{copies} 정상 진행 중...")
                else:
                    print(f"인쇄 작업 {i+1}/{copies} 시작 중 오류: {e}")
                    success = False
                    break
        
        if success:
            print("모든 인쇄 작업이 시작되었습니다!")
        
        return success
    except Exception as e:
        logger.error(f"인쇄 실패: {e}")
        print(f"인쇄 오류: {e}")
        return False


def main():
    """메인 함수"""
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description='HiTi 프린터 키오스크 인쇄')
    parser.add_argument('--copies', type=int, default=1, help='인쇄 매수 (기본값: 1)')
    parser.add_argument('--image_index', type=int, default=0, help='이미지 인덱스 (기본값: 0, 첫 번째 이미지)')
    args = parser.parse_args()
    
    print("HiTi 프린터 키오스크 자동 인쇄\n")
    
    try:
        # 프린터 연결
        print("프린터 연결 중...")
        printer = HiTiPrinter()  # 자동으로 첫 번째 발견된 프린터 사용
        print(f"프린터 연결됨: {printer.device.printer_name}")
        
        # 프린터 정보 출력
        print_device_info(printer)
        
        # 테스트 이미지 확인
        images_dir = Path(__file__).parent / "images"
        if not images_dir.exists():
            images_dir.mkdir(parents=True, exist_ok=True)
            print(f"테스트 이미지를 '{images_dir}' 디렉토리에 추가하세요")
            return
        
        # 사용 가능한 이미지 파일 목록
        image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
        
        if not image_files:
            print(f"'{images_dir}' 디렉토리에 이미지 파일이 없습니다.")
            return
        
        # 이미지 인덱스 확인
        image_index = args.image_index
        if image_index < 0 or image_index >= len(image_files):
            print(f"유효하지 않은 이미지 인덱스입니다. 첫 번째 이미지를 사용합니다.")
            image_index = 0
        
        # 인쇄 매수 확인
        copies = max(1, args.copies)  # 최소 1장
        
        # 선택한 이미지 정보 출력
        selected_image = image_files[image_index]
        print(f"\n선택된 이미지: {selected_image.name}")
        print(f"인쇄 매수: {copies}")
        
        # 인쇄 실행
        print_photo(printer, str(selected_image), copies)
        
    except ConnectionError as e:
        logger.error(f"프린터 연결 오류: {e}")
        print(f"프린터 연결 실패: {e}")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        print(f"오류 발생: {e}")


if __name__ == "__main__":
    main()