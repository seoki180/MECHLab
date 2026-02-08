import wx
import cv2
import threading
import numpy as np
import socket

from Panel.Menubar import MenuBar
from Config.CameraServer import CameraServer


class CameraFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent=None, title='App name - Camera Server', size=(1200, 700))
        self.first_frame = parent
        self.capture = None
        self.is_running = False

        # 스트리밍 서버 인스턴스 (기본값: 20fps, 저지연 모드)
        self.stream_server = CameraServer(host='0.0.0.0', port=9999, target_fps=20, low_latency=True)

        # 서버 콜백 설정
        self.stream_server.on_server_started = self.on_server_started_callback
        self.stream_server.on_client_connected = self.on_client_connected_callback
        self.stream_server.on_client_disconnected = self.on_client_disconnected_callback
        self.stream_server.on_send_error = self.on_send_error_callback

        # 패널 생성
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(240, 240, 240))

        # 메인 레이아웃
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 상단 메뉴바 영역
        menubar_panel = MenuBar(panel)

        # 콘텐츠 영역
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        # 서버 정보 표시
        info_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.server_info_text = wx.StaticText(panel, label='서버 대기 중... (포트: 9999)')
        self.server_info_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        info_sizer.Add(self.server_info_text, 0, wx.ALL, 10)

        # FPS 및 지연 설정 영역
        settings_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # FPS 설정
        fps_label = wx.StaticText(panel, label='전송 FPS:')
        self.fps_slider = wx.Slider(panel, value=20, minValue=5, maxValue=30,
                                    style=wx.SL_HORIZONTAL | wx.SL_LABELS, size=(200, -1))
        self.fps_slider.Bind(wx.EVT_SLIDER, self.on_fps_change)

        # 지연 모드 설정
        latency_label = wx.StaticText(panel, label='지연 모드:')
        self.latency_choice = wx.Choice(panel, choices=['초저지연 (권장)', '일반 모드'])
        self.latency_choice.SetSelection(0)  # 기본값: 초저지연
        self.latency_choice.Bind(wx.EVT_CHOICE, self.on_latency_change)

        # 압축 품질 설정
        quality_label = wx.StaticText(panel, label='화질:')
        self.quality_slider = wx.Slider(panel, value=70, minValue=30, maxValue=95,
                                        style=wx.SL_HORIZONTAL | wx.SL_LABELS, size=(150, -1))
        self.quality_slider.Bind(wx.EVT_SLIDER, self.on_quality_change)

        settings_sizer.Add(fps_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        settings_sizer.Add(self.fps_slider, 0, wx.ALL, 5)
        settings_sizer.Add((20, 0))  # 간격
        settings_sizer.Add(latency_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        settings_sizer.Add(self.latency_choice, 0, wx.ALL, 5)
        settings_sizer.Add((20, 0))  # 간격
        settings_sizer.Add(quality_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        settings_sizer.Add(self.quality_slider, 0, wx.ALL, 5)

        # 현재 설정 정보 표시
        self.settings_info_text = wx.StaticText(panel,
                                                label='현재 설정: 20 FPS, 초저지연 모드, 화질 70')
        self.settings_info_text.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))

        # 카메라 영상을 표시할 StaticBitmap
        self.camera_display = wx.StaticBitmap(panel, -1, size=(640, 480))
        self.camera_display.SetBackgroundColour(wx.Colour(50, 50, 50))

        # 버튼들
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.start_btn = wx.Button(panel, label='서버 시작', size=(150, 40))
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start_server)

        self.stop_btn = wx.Button(panel, label='서버 중지', size=(150, 40))
        self.stop_btn.Bind(wx.EVT_BUTTON, self.on_stop_server)
        self.stop_btn.Enable(False)

        back_btn = wx.Button(panel, label='뒤로가기', size=(150, 40))
        back_btn.Bind(wx.EVT_BUTTON, self.on_back)

        button_sizer.Add(self.start_btn, 0, wx.ALL, 10)
        button_sizer.Add(self.stop_btn, 0, wx.ALL, 10)
        button_sizer.Add(back_btn, 0, wx.ALL, 10)

        # 레이아웃 구성
        content_sizer.Add(info_sizer, 0, wx.CENTER)
        content_sizer.Add(settings_sizer, 0, wx.CENTER | wx.TOP, 10)
        content_sizer.Add(self.settings_info_text, 0, wx.CENTER | wx.TOP, 5)
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

    def on_fps_change(self, event):
        """FPS 변경"""
        fps = self.fps_slider.GetValue()
        self.stream_server.set_target_fps(fps)
        self.update_settings_info()

    def on_latency_change(self, event):
        """지연 모드 변경"""
        selection = self.latency_choice.GetSelection()
        self.stream_server.low_latency = (selection == 0)  # 0: 초저지연, 1: 일반
        self.update_settings_info()

    def on_quality_change(self, event):
        """화질 변경"""
        # 화질은 send_frame에서 직접 사용되므로 서버 인스턴스에 저장
        quality = self.quality_slider.GetValue()
        self.stream_server.jpeg_quality = quality
        self.update_settings_info()

    def update_settings_info(self):
        """설정 정보 업데이트"""
        fps = self.fps_slider.GetValue()
        latency_mode = "초저지연 모드" if self.latency_choice.GetSelection() == 0 else "일반 모드"
        quality = self.quality_slider.GetValue()
        self.settings_info_text.SetLabel(f'현재 설정: {fps} FPS, {latency_mode}, 화질 {quality}')

    # 서버 콜백 메서드들
    def on_server_started_callback(self, ip, port):
        """서버 시작 콜백"""
        # 모든 네트워크 인터페이스 정보 표시
        info_text = f'서버 실행 중 - IP: {ip}, 포트: {port}\n'

        # 추가 IP 주소 확인
        try:
            hostname = socket.gethostname()
            all_ips = []
            for info in socket.getaddrinfo(hostname, None):
                if info[0] == socket.AF_INET and info[4][0] != '127.0.0.1':
                    all_ips.append(info[4][0])

            if len(all_ips) > 1:
                info_text += f'다른 IP: {", ".join([ip for ip in all_ips if ip != ip])}'
        except:
            pass

        wx.CallAfter(self.server_info_text.SetLabel, info_text)

    def on_client_connected_callback(self, client_ip, client_port):
        """클라이언트 연결 콜백"""
        wx.CallAfter(self.server_info_text.SetLabel, f'클라이언트 연결됨: {client_ip}:{client_port}')

    def on_client_disconnected_callback(self):
        """클라이언트 연결 끊김 콜백"""
        wx.CallAfter(self.server_info_text.SetLabel, '클라이언트 연결 끊김 - 재연결 대기 중...')

    def on_send_error_callback(self, error_message):
        """전송 오류 콜백"""
        print(error_message)

    def on_start_server(self, event):
        """서버 및 카메라 시작"""
        if not self.stream_server.is_running:
            # 카메라 시작
            self.capture = cv2.VideoCapture(0)
            if not self.capture.isOpened():
                wx.MessageBox('카메라를 열 수 없습니다.', '오류', wx.OK | wx.ICON_ERROR)
                return

            # 서버 시작
            success, result = self.stream_server.start()

            if not success:
                wx.MessageBox(f'서버 시작 실패: {result}', '오류', wx.OK | wx.ICON_ERROR)
                if self.capture:
                    self.capture.release()
                    self.capture = None
                return

            self.is_running = True
            self.start_btn.Enable(False)
            self.stop_btn.Enable(True)

            # 설정 잠금 (서버 실행 중에는 변경 불가)
            self.fps_slider.Enable(False)
            self.latency_choice.Enable(False)
            self.quality_slider.Enable(False)

            # 카메라 스레드 시작
            self.camera_thread = threading.Thread(target=self.update_camera, daemon=True)
            self.camera_thread.start()

    def on_stop_server(self, event):
        """서버 및 카메라 중지"""
        self.is_running = False

        # 서버 중지
        self.stream_server.stop()

        # 카메라 종료
        if self.capture:
            self.capture.release()
            self.capture = None

        self.start_btn.Enable(True)
        self.stop_btn.Enable(False)

        # 설정 잠금 해제
        self.fps_slider.Enable(True)
        self.latency_choice.Enable(True)
        self.quality_slider.Enable(True)

        self.server_info_text.SetLabel('서버 중지됨')

        # 검은 화면으로 초기화
        self.camera_display.SetBitmap(wx.Bitmap.FromRGBA(640, 480, 50, 50, 50, 255))

    def update_camera(self):
        """카메라 프레임 업데이트 및 전송"""
        while self.is_running:
            if self.capture and self.capture.isOpened():
                ret, frame = self.capture.read()
                if ret:
                    # 원본 프레임 저장
                    original_frame = frame.copy()

                    # 로컬 화면 표시용 (비율 유지)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    original_height, original_width = frame_rgb.shape[:2]
                    target_width = 640
                    target_height = 480

                    scale = min(target_width / original_width, target_height / original_height)
                    new_width = int(original_width * scale)
                    new_height = int(original_height * scale)

                    resized_frame = cv2.resize(frame_rgb, (new_width, new_height))

                    # 검은 배경에 중앙 정렬
                    display_frame = np.zeros((target_height, target_width, 3), dtype=np.uint8)
                    y_offset = (target_height - new_height) // 2
                    x_offset = (target_width - new_width) // 2
                    display_frame[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_frame

                    # 로컬 화면에 표시
                    image = wx.Image(target_width, target_height, display_frame.tobytes())
                    bitmap = wx.Bitmap(image)
                    wx.CallAfter(self.camera_display.SetBitmap, bitmap)

                    # 클라이언트에게 전송 (원본 크기로 전송)
                    if self.stream_server.is_client_connected():
                        self.stream_server.send_frame(original_frame)

            # FPS에 맞춰 대기 시간 조정
            wait_time = max(1, int(1000 / self.fps_slider.GetValue()))
            cv2.waitKey(wait_time)

    def on_back(self, event):
        """뒤로가기"""
        self.on_stop_server(None)
        self.Hide()
        self.first_frame.Show()
        self.Destroy()

    def on_close(self, event):
        """창 닫기"""
        self.on_stop_server(None)
        if self.first_frame:
            self.first_frame.Destroy()
        self.Destroy()