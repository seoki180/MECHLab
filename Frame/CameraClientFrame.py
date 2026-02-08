import wx
import cv2
import threading
import socket
import struct
import pickle
import numpy as np

from Panel.Menubar import MenuBar


class CameraClientFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent=None, title='App name - Camera Client', size=(1200, 700))
        self.first_frame = parent
        self.client_socket = None
        self.is_running = False
        self.last_bitmap = None  # 마지막 프레임 캐싱

        # 패널 생성
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(240, 240, 240))

        # 메인 레이아웃
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 상단 메뉴바 영역
        menubar_panel = MenuBar(panel)

        # 콘텐츠 영역
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        # 연결 정보 입력
        input_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 연결 타입 선택
        connection_type_label = wx.StaticText(panel, label='연결 타입:')
        self.connection_type = wx.Choice(panel, choices=[
            '같은 Wi-Fi/라우터',
            '직접 연결 (크로스오버)',
            '인터넷 원격 연결',
            '직접 입력'
        ])
        self.connection_type.SetSelection(0)
        self.connection_type.Bind(wx.EVT_CHOICE, self.on_connection_type_change)

        ip_label = wx.StaticText(panel, label='서버 IP:')
        self.ip_input = wx.TextCtrl(panel, value='192.168.0.100', size=(150, 25))

        port_label = wx.StaticText(panel, label='포트:')
        self.port_input = wx.TextCtrl(panel, value='9999', size=(80, 25))

        input_sizer.Add(connection_type_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        input_sizer.Add(self.connection_type, 0, wx.ALL, 5)
        input_sizer.Add((10, 0))  # 간격
        input_sizer.Add(ip_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        input_sizer.Add(self.ip_input, 0, wx.ALL, 5)
        input_sizer.Add(port_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        input_sizer.Add(self.port_input, 0, wx.ALL, 5)

        # 연결 상태 표시
        self.status_text = wx.StaticText(panel, label='연결 대기 중')
        self.status_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        # 카메라 영상을 표시할 StaticBitmap
        self.camera_display = wx.StaticBitmap(panel, -1, size=(640, 480))
        self.camera_display.SetBackgroundColour(wx.Colour(50, 50, 50))

        # 버튼들
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.connect_btn = wx.Button(panel, label='연결', size=(150, 40))
        self.connect_btn.Bind(wx.EVT_BUTTON, self.on_connect)

        self.disconnect_btn = wx.Button(panel, label='연결 해제', size=(150, 40))
        self.disconnect_btn.Bind(wx.EVT_BUTTON, self.on_disconnect)
        self.disconnect_btn.Enable(False)

        back_btn = wx.Button(panel, label='뒤로가기', size=(150, 40))
        back_btn.Bind(wx.EVT_BUTTON, self.on_back)

        button_sizer.Add(self.connect_btn, 0, wx.ALL, 10)
        button_sizer.Add(self.disconnect_btn, 0, wx.ALL, 10)
        button_sizer.Add(back_btn, 0, wx.ALL, 10)

        # 레이아웃 구성
        content_sizer.Add(input_sizer, 0, wx.CENTER | wx.TOP, 10)
        content_sizer.Add(self.status_text, 0, wx.CENTER | wx.ALL, 10)
        content_sizer.AddStretchSpacer()
        content_sizer.Add(self.camera_display, 0, wx.ALL | wx.CENTER, 20)
        content_sizer.Add(button_sizer, 0, wx.CENTER)
        content_sizer.AddStretchSpacer()

        main_sizer.Add(menubar_panel, 0, wx.EXPAND)
        main_sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND)
        main_sizer.Add(content_sizer, 1, wx.EXPAND)

        panel.SetSizer(main_sizer)

        self.Centre()

        # 창 닫기 이벤트
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_connection_type_change(self, event):
        """연결 타입 변경 시 IP 프리셋 적용"""
        selection = self.connection_type.GetSelection()

        if selection == 0:  # 같은 Wi-Fi/라우터
            self.ip_input.SetValue('192.168.0.100')
            self.status_text.SetLabel('같은 라우터에 연결된 서버 IP를 입력하세요')
        elif selection == 1:  # 직접 연결
            self.ip_input.SetValue('192.168.137.1')
            self.status_text.SetLabel('직접 연결: 서버를 192.168.137.1로 설정하세요')
        elif selection == 2:  # 인터넷 원격
            self.ip_input.SetValue('')
            self.status_text.SetLabel('서버의 공인 IP를 입력하세요')
        else:  # 직접 입력
            self.ip_input.SetValue('')
            self.status_text.SetLabel('서버 IP를 직접 입력하세요')

    def on_connect(self, event):
        """서버에 연결"""
        if not self.is_running:
            server_ip = self.ip_input.GetValue()
            server_port = int(self.port_input.GetValue())

            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # 저지연 최적화
                # TCP_NODELAY 설정으로 지연 감소
                self.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                # 수신 버퍼 크기 축소 (버퍼링 지연 감소)
                self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)  # 64KB
                # TCP Quick ACK 활성화 (Linux)
                try:
                    self.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
                except (AttributeError, OSError):
                    pass  # Windows/Mac에서는 지원 안 함

                self.client_socket.connect((server_ip, server_port))

                self.is_running = True
                self.connect_btn.Enable(False)
                self.disconnect_btn.Enable(True)
                self.ip_input.Enable(False)
                self.port_input.Enable(False)

                self.status_text.SetLabel(f'서버 연결됨: {server_ip}:{server_port}')

                # 수신 스레드 시작
                self.receive_thread = threading.Thread(target=self.receive_frames, daemon=True)
                self.receive_thread.start()

            except Exception as e:
                wx.MessageBox(f'연결 실패: {str(e)}', '오류', wx.OK | wx.ICON_ERROR)
                if self.client_socket:
                    self.client_socket.close()
                    self.client_socket = None

    def on_disconnect(self, event):
        """연결 해제"""
        self.is_running = False

        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None

        self.connect_btn.Enable(True)
        self.disconnect_btn.Enable(False)
        self.ip_input.Enable(True)
        self.port_input.Enable(True)

        self.status_text.SetLabel('연결 해제됨')

        # 마지막 프레임 캐시 초기화
        self.last_bitmap = None

        # 검은 화면으로 초기화
        self.camera_display.SetBitmap(wx.Bitmap.FromRGBA(640, 480, 50, 50, 50, 255))

    def receive_frames(self):
        """프레임 수신 및 표시 (저지연 최적화 + 안정성)"""
        data = b""
        payload_size = struct.calcsize("!I")  # 4바이트

        # 타임아웃을 짧게 설정 (1초)
        self.client_socket.settimeout(1.0)

        consecutive_errors = 0  # 연속 에러 카운트
        max_consecutive_errors = 10  # 최대 허용 연속 에러

        while self.is_running:
            try:
                # 데이터 크기 수신 (4바이트)
                while len(data) < payload_size:
                    try:
                        packet = self.client_socket.recv(4096)
                        if not packet:
                            raise ConnectionError("서버 연결 끊김")
                        data += packet
                    except socket.timeout:
                        # 타임아웃 시 마지막 프레임 유지 (화면 깜빡임 방지)
                        continue

                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("!I", packed_msg_size)[0]

                # 비정상적인 메시지 크기 검증
                if msg_size > 10 * 1024 * 1024:  # 10MB 이상이면 비정상
                    print(f"[클라이언트] 비정상적인 메시지 크기: {msg_size}, 버퍼 초기화")
                    data = b""
                    continue

                # 실제 데이터 수신
                while len(data) < msg_size:
                    try:
                        remaining = msg_size - len(data)
                        packet = self.client_socket.recv(min(8192, remaining))  # 버퍼 크기 증가
                        if not packet:
                            raise ConnectionError("서버 연결 끊김")
                        data += packet
                    except socket.timeout:
                        continue

                frame_data = data[:msg_size]
                data = data[msg_size:]

                # 데이터 역직렬화 및 디코딩
                try:
                    frame = pickle.loads(frame_data)
                    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

                    if frame is None:
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            raise Exception("연속적인 프레임 디코딩 실패")
                        continue

                    # 성공적으로 디코딩됨 - 에러 카운트 리셋
                    consecutive_errors = 0

                    # BGR to RGB 변환
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # 원본 비율 유지하면서 640x480 영역에 맞추기
                    original_height, original_width = frame_rgb.shape[:2]
                    target_width = 640
                    target_height = 480

                    # 비율 계산
                    scale = min(target_width / original_width, target_height / original_height)
                    new_width = int(original_width * scale)
                    new_height = int(original_height * scale)

                    # 리사이즈 (비율 유지)
                    resized_frame = cv2.resize(frame_rgb, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

                    # 검은 배경에 중앙 정렬
                    display_frame = np.zeros((target_height, target_width, 3), dtype=np.uint8)
                    y_offset = (target_height - new_height) // 2
                    x_offset = (target_width - new_width) // 2
                    display_frame[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_frame

                    # 화면에 표시
                    image = wx.Image(target_width, target_height, display_frame.tobytes())
                    bitmap = wx.Bitmap(image)

                    # 마지막 프레임 저장
                    self.last_bitmap = bitmap

                    # UI 업데이트
                    wx.CallAfter(self.camera_display.SetBitmap, bitmap)

                except pickle.UnpicklingError:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        raise Exception("연속적인 pickle 역직렬화 실패")
                    # 버퍼 손상 가능성 - 버퍼 일부 클리어
                    data = b""
                    continue
                except cv2.error:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        raise Exception("연속적인 OpenCV 오류")
                    continue

            except ConnectionError as e:
                print(f'[클라이언트] 연결 오류: {e}')
                wx.CallAfter(self.status_text.SetLabel, '연결 끊김')
                self.is_running = False
                wx.CallAfter(self.on_disconnect, None)
                break
            except Exception as e:
                print(f'[클라이언트] 수신 오류: {e}')
                wx.CallAfter(self.status_text.SetLabel, '연결 끊김')
                self.is_running = False
                wx.CallAfter(self.on_disconnect, None)
                break

    def on_back(self, event):
        """뒤로가기"""
        self.on_disconnect(None)
        self.Hide()
        self.first_frame.Show()
        self.Destroy()

    def on_close(self, event):
        """창 닫기"""
        self.on_disconnect(None)
        if self.first_frame:
            self.first_frame.Destroy()
        self.Destroy()