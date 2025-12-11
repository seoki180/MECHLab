import wx
import cv2
import threading

from Panel.Menubar import MenuBar


class CameraFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent=None, title='App name - Camera', size=(1200, 700))
        self.first_frame = parent
        self.capture = None
        self.is_running = False

        # 패널 생성
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(240, 240, 240))

        # 메인 레이아웃
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 상단 메뉴바 영역
        menubar_panel = MenuBar(panel)

        # 콘텐츠 영역
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        # 카메라 영상을 표시할 StaticBitmap
        self.camera_display = wx.StaticBitmap(panel, -1, size=(640, 480))
        self.camera_display.SetBackgroundColour(wx.Colour(50, 50, 50))

        # 버튼들
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.start_btn = wx.Button(panel, label='카메라 시작', size=(150, 40))
        self.start_btn.Bind(wx.EVT_BUTTON, self.on_start_camera)

        self.stop_btn = wx.Button(panel, label='카메라 중지', size=(150, 40))
        self.stop_btn.Bind(wx.EVT_BUTTON, self.on_stop_camera)
        self.stop_btn.Enable(False)

        back_btn = wx.Button(panel, label='뒤로가기', size=(150, 40))
        back_btn.Bind(wx.EVT_BUTTON, self.on_back)

        button_sizer.Add(self.start_btn, 0, wx.ALL, 10)
        button_sizer.Add(self.stop_btn, 0, wx.ALL, 10)
        button_sizer.Add(back_btn, 0, wx.ALL, 10)

        # 레이아웃 구성
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

    def on_start_camera(self, event):
        """카메라 시작"""
        if not self.is_running:
            self.capture = cv2.VideoCapture(0)  # 0은 기본 카메라
            if self.capture.isOpened():
                self.is_running = True
                self.start_btn.Enable(False)
                self.stop_btn.Enable(True)
                # 카메라 스레드 시작
                self.camera_thread = threading.Thread(target=self.update_camera, daemon=True)
                self.camera_thread.start()
            else:
                wx.MessageBox('카메라를 열 수 없습니다.', '오류', wx.OK | wx.ICON_ERROR)

    def on_stop_camera(self, event):
        """카메라 중지"""
        self.is_running = False
        if self.capture:
            self.capture.release()
            self.capture = None
        self.start_btn.Enable(True)
        self.stop_btn.Enable(False)
        # 검은 화면으로 초기화
        self.camera_display.SetBitmap(wx.Bitmap.FromRGBA(640, 480, 50, 50, 50, 255))

    def update_camera(self):
        """카메라 프레임 업데이트"""
        while self.is_running:
            if self.capture and self.capture.isOpened():
                ret, frame = self.capture.read()
                if ret:
                    # OpenCV는 BGR, wxPython은 RGB를 사용하므로 변환
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # 프레임 크기 조정
                    frame = cv2.resize(frame, (640, 480))
                    # numpy array를 wx.Image로 변환
                    height, width = frame.shape[:2]
                    image = wx.Image(width, height, frame.tobytes())
                    # wx.Image를 wx.Bitmap으로 변환
                    bitmap = wx.Bitmap(image)
                    # UI 업데이트는 메인 스레드에서 실행
                    wx.CallAfter(self.camera_display.SetBitmap, bitmap)
            # 약간의 지연 (CPU 사용량 감소)
            cv2.waitKey(30)

    def on_back(self, event):
        """뒤로가기"""
        self.on_stop_camera(None)
        self.Hide()
        self.first_frame.Show()
        self.Destroy()

    def on_close(self, event):
        """창 닫기"""
        self.on_stop_camera(None)
        if self.first_frame:
            self.first_frame.Destroy()
        self.Destroy()
