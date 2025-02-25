import cv2
import logging
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QMouseEvent
from PyQt6.QtWidgets import QLabel, QApplication, QWidget, QVBoxLayout
import time
import sys

def initialize_camera(camera_index=0, width=1920, height=1080, fps=60):
    """카메라 초기화 및 최적화"""
    camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not camera.isOpened():
        camera = cv2.VideoCapture(camera_index)
    
    if camera.isOpened():
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        camera.set(cv2.CAP_PROP_FPS, fps)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # 기본값 유지, 필요 시 변경 가능
        camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)  # 자동 노출을 부드럽게 조정
        for _ in range(5):  # 프레임 버퍼 줄이기
            camera.read()
        logging.info("카메라 초기화 완료")
        return camera
    logging.error("카메라 초기화 실패")
    return None

def get_frame(camera):
    """최신 프레임을 반환"""
    if camera and camera.isOpened():
        ret, frame = camera.read()
        if ret:
            return cv2.flip(frame, 1)  # 좌우 반전
    return None

def release_camera(camera):
    """카메라 자원 해제"""
    if camera and camera.isOpened():
        camera.release()
        logging.info("카메라 해제 완료")

def capture_and_save_photo(camera, save_path="captured_photo.jpg"):
    """현재 카메라 인스턴스를 사용하여 사진 촬영 후 저장"""
    frame = get_frame(camera)
    if frame is not None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        file_path = save_path.replace(".jpg", f"_{timestamp}.jpg")
        cv2.imwrite(file_path, frame)
        logging.info(f"📸 사진 저장 완료: {file_path}")
        return file_path
    logging.error("사진 촬영 실패")
    return None

class CountdownThread(QThread):
    countdown_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()

    def __init__(self, countdown_time):
        super().__init__()
        self.countdown_time = countdown_time

    def run(self):
        for i in range(self.countdown_time, 0, -1):
            self.countdown_signal.emit(i)
            time.sleep(1)
        self.finished_signal.emit()

class WebcamViewer(QWidget):
    """PyQt를 이용한 실시간 웹캠 프리뷰"""
    def __init__(self, camera_index=0, width=640, height=480, x=100, y=100, countdown=0):
        super().__init__()
        self.setWindowTitle("Webcam Viewer")
        self.setGeometry(x, y, width, height)  # 윈도우 위치 및 크기 설정
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # 윈도우 테두리 제거
        self.camera = initialize_camera(camera_index, width, height)
        self.preview_label = QLabel(self)
        self.preview_label.setFixedSize(width, height)

        self.countdown_label = QLabel(self)
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet("font-size: 80px; color: White;")  # 글자 크기 조정
        self.countdown_label.setGeometry(0, 0, width, int(height * 0.15))  # 중앙 상단 배치
        self.countdown_label.hide()
        
        self.countdown_time = countdown
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.preview_label)
        self.setLayout(self.layout)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(16)  # 60fps
    
    def update_frame(self):
        frame = get_frame(self.camera)
        if frame is not None:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            qimage = QImage(rgb_image.data, w, h, w * ch, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            self.preview_label.setPixmap(pixmap)
    
    def mousePressEvent(self, event: QMouseEvent):
        """마우스로 클릭 시 사진 촬영 (카운트다운 적용)"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.countdown_time > 0:
                self.countdown_label.show()
                self.countdown_thread = CountdownThread(self.countdown_time)
                self.countdown_thread.countdown_signal.connect(self.update_countdown)
                self.countdown_thread.finished_signal.connect(self.capture_photo)
                self.countdown_thread.start()
            else:
                self.capture_photo()
    
    def update_countdown(self, count):
        """카운트다운 업데이트"""
        self.countdown_label.setText(str(count))

    def capture_photo(self):
        """사진 촬영 후 카운트다운 숨기기"""
        self.countdown_label.hide()
        file_path = capture_and_save_photo(self.camera, "captured_image.jpg")
        if file_path:
            print(f"📸 사진 저장 완료: {file_path}")
    
    def closeEvent(self, event):
        """창 닫을 때 카메라 해제"""
        self.timer.stop()
        release_camera(self.camera)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = WebcamViewer(x=200, y=150, width=800, height=600, countdown=3)  # 카운트다운 3초 설정
    viewer.show()
    sys.exit(app.exec())
