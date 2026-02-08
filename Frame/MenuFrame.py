import wx

from Frame.CameraClientFrame import CameraClientFrame
from Frame.CameraFrame import CameraFrame
from Frame.FileFrame import FileFrame
from Frame.ReportFrame.ReportFrame import ReportFrame
from Panel.Menubar import MenuBar


class MenuFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent=None, title='App name - Menu', size=(800, 600))
        self.first_frame = parent

        # 패널 생성
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(240, 240, 240))

        # 메인 sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 상단 메뉴바 영역
        menubar_panel = MenuBar(panel)
        # 콘텐츠 영역
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        # 타이틀
        title_text = wx.StaticText(panel, label='화면을 선택하세요')
        title_font = title_text.GetFont()
        title_font.PointSize += 6
        title_font = title_font.Bold()
        title_text.SetFont(title_font)

        # 버튼들을 담을 sizer
        buttons_sizer = wx.BoxSizer(wx.VERTICAL)

        # 3개의 메뉴 버튼 생성
        option1_btn = wx.Button(panel, label='파일 분석 화면', size=(250, 50))
        option1_btn.Bind(wx.EVT_BUTTON, self.on_option1)

        option2_btn = wx.Button(panel, label="카메라-서버", size=(250, 50))
        option2_btn.Bind(wx.EVT_BUTTON, self.on_option2)

        option3_btn = wx.Button(panel, label='카메라-클라이언트', size=(250, 50))
        option3_btn.Bind(wx.EVT_BUTTON, self.on_option3)

        option4_btn = wx.Button(panel, label='실험리포트', size=(250, 50))
        option4_btn.Bind(wx.EVT_BUTTON, self.on_option4)

        # 뒤로가기 버튼
        back_btn = wx.Button(panel, label='뒤로가기', size=(150, 40))
        back_btn.Bind(wx.EVT_BUTTON, self.on_back)

        # 버튼들 배치
        buttons_sizer.Add(option1_btn, 0, wx.ALL | wx.CENTER, 15)
        buttons_sizer.Add(option2_btn, 0, wx.ALL | wx.CENTER, 15)
        buttons_sizer.Add(option3_btn, 0, wx.ALL | wx.CENTER, 15)
        buttons_sizer.Add(option4_btn, 0, wx.ALL | wx.CENTER, 15)

        # 레이아웃 구성
        content_sizer.AddStretchSpacer()
        content_sizer.Add(title_text, 0, wx.ALL | wx.CENTER, 20)
        content_sizer.Add(buttons_sizer, 0, wx.CENTER)
        content_sizer.AddStretchSpacer()
        content_sizer.Add(back_btn, 0, wx.ALL | wx.CENTER, 20)

        main_sizer.Add(menubar_panel, 0, wx.EXPAND)
        main_sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND)
        main_sizer.Add(content_sizer, 1, wx.EXPAND)

        panel.SetSizer(main_sizer)

        self.Centre()

        # 창 닫기 이벤트
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_option1(self, event):
        # 첫 번째 버튼 - SecondFrame으로 이동
        self.Hide()
        file_frame = FileFrame(self.first_frame)
        file_frame.Show()
        self.Destroy()

    def on_option2(self, event):
        self.Hide()
        camera_frame = CameraFrame(self.first_frame)
        camera_frame.Show()
        self.Destroy()

    def on_option3(self, event):
        self.Hide()
        camera_client_frame = CameraClientFrame(self.first_frame)
        camera_client_frame.Show()
        self.Destroy()

    def on_option4(self, event):
        self.Hide()
        report_frame = ReportFrame(self.first_frame)
        report_frame.Show()
        self.Destroy()

    def on_back(self, event):
        # 첫 번째 프레임으로 돌아가기
        self.Hide()
        self.first_frame.Show()
        self.Destroy()

    def on_close(self, event):
        # 첫 번째 프레임도 함께 종료
        if self.first_frame:
            self.first_frame.Destroy()
        self.Destroy()