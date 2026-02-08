import socket
import threading
import struct
import pickle
import cv2
import time


class CameraServer:
    def __init__(self, host='0.0.0.0', port=9999, target_fps=20, low_latency=True):
        self.host = host
        self.port = port
        self.target_fps = target_fps  # 목표 FPS (기본 30fps - 저지연 모드)
        self.frame_interval = 1.0 / target_fps  # 프레임 간격 (초)
        self.last_frame_time = 0  # 마지막 프레임 전송 시간
        self.low_latency = low_latency  # 저지연 모드
        self.jpeg_quality = 70  # JPEG 압축 품질 (기본 70)
        self.server_socket = None
        self.client_socket = None
        self.is_running = False
        self.client_address = None

        # 콜백 함수들
        self.on_client_connected = None
        self.on_client_disconnected = None
        self.on_send_error = None
        self.on_server_started = None

    def start(self):
        """서버 시작"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # TCP_NODELAY 설정으로 Nagle 알고리즘 비활성화 (지연 감소)
            self.server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            if self.low_latency:
                # 저지연 모드 최적화
                # 송신 버퍼 크기 줄이기 (버퍼링 지연 감소)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # 64KB
                # TCP Quick ACK 활성화 (Linux)
                try:
                    self.server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
                except (AttributeError, OSError):
                    pass  # Windows/Mac에서는 지원 안 함

            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)

            self.is_running = True

            # 클라이언트 연결 대기 스레드 시작
            accept_thread = threading.Thread(target=self._accept_client, daemon=True)
            accept_thread.start()

            # 로컬 IP 가져오기
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)

            if self.on_server_started:
                self.on_server_started(local_ip, self.port)

            return True, local_ip

        except Exception as e:
            return False, str(e)

    def stop(self):
        """서버 중지"""
        self.is_running = False

        # 클라이언트 소켓 종료
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None

        # 서버 소켓 종료
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None

    def _accept_client(self):
        """클라이언트 연결 대기 (내부 메서드)"""
        try:
            while self.is_running:
                if self.server_socket:
                    self.client_socket, self.client_address = self.server_socket.accept()

                    # 클라이언트 소켓 옵션 설정
                    self.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                    if self.low_latency:
                        # 저지연 모드 최적화
                        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # 64KB
                        # TCP Quick ACK 활성화 (Linux)
                        try:
                            self.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
                        except (AttributeError, OSError):
                            pass
                    else:
                        # 일반 모드
                        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)

                    if self.on_client_connected:
                        self.on_client_connected(self.client_address[0], self.client_address[1])

        except Exception as e:
            if self.is_running:
                if self.on_send_error:
                    self.on_send_error(f'클라이언트 연결 실패: {str(e)}')

    def send_frame(self, frame):
        """프레임 전송 (FPS 제어 포함)"""
        if not self.client_socket:
            return False

        # FPS 제어 - 프레임 간격 확인
        current_time = time.time()
        elapsed = current_time - self.last_frame_time

        if elapsed < self.frame_interval:
            # 아직 전송할 시간이 아님 - 프레임 스킵
            return True

        self.last_frame_time = current_time

        try:
            # 프레임 검증
            if frame is None or frame.size == 0:
                return False

            # 저지연 모드: 해상도 축소 및 압축 품질 조정
            if self.low_latency:
                # 해상도를 640x480 이하로 축소 (전송 데이터 크기 감소)
                height, width = frame.shape[:2]
                if width > 640 or height > 480:
                    scale = min(640 / width, 480 / height)
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

                # 사용자 설정 화질 사용 (기본 70)
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
            else:
                # 일반 모드: 사용자 설정 화질 사용
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]

            # JPEG로 압축
            result, buffer = cv2.imencode('.jpg', frame, encode_param)

            if not result:
                return False

            data = pickle.dumps(buffer)

            # 데이터 크기 먼저 전송 (네트워크 바이트 오더)
            message_size = struct.pack("!I", len(data))

            # sendall로 전체 데이터 전송 보장
            self.client_socket.sendall(message_size + data)

            return True

        except BrokenPipeError:
            # 클라이언트가 끊김
            self.client_socket = None
            if self.on_client_disconnected:
                self.on_client_disconnected()
            return False

        except Exception as e:
            # 전송 실패 - 클라이언트 연결 끊김
            self.client_socket = None

            if self.on_client_disconnected:
                self.on_client_disconnected()

            if self.on_send_error:
                self.on_send_error(f'전송 오류: {str(e)}')

            return False

    def is_client_connected(self):
        """클라이언트 연결 여부 확인"""
        return self.client_socket is not None

    def get_server_info(self):
        """서버 정보 반환"""
        if self.is_running:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return local_ip, self.port
        return None, None

    def set_target_fps(self, fps):
        """목표 FPS 설정 (1~30)"""
        if 1 <= fps <= 30:
            self.target_fps = fps
            self.frame_interval = 1.0 / fps
            print(f"[서버] 목표 FPS 설정: {fps}fps (간격: {self.frame_interval:.3f}초)")
        else:
            print(f"[서버] FPS는 1~30 사이여야 합니다")

    def get_current_fps(self):
        """현재 FPS 반환"""
        return self.target_fps