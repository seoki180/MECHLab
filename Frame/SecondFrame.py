import wx

from Panel.Menubar import MenuBar


class SecondFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent=None, title='App name', size=(1200, 700))
        self.first_frame = parent

        # 패널 생성
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(240, 240, 240))

        # 메인 레이아웃
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 상단 메뉴바 영역
        menubar_panel = MenuBar(panel)
        # 콘텐츠 영역
        content_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 왼쪽 영역 - open file 버튼과 파일 탐색기
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        # open file 버튼
        open_btn = wx.Button(panel, label='open file', size=(120, 35))
        open_btn.Bind(wx.EVT_BUTTON, self.on_open_file)

        # 왼쪽 레이아웃 구성
        left_sizer.Add(open_btn, 0, wx.ALL, 10)

        # 콘텐츠 레이아웃에 추가
        content_sizer.Add(left_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # 메인 레이아웃 구성
        main_sizer.Add(menubar_panel, 0, wx.EXPAND)
        main_sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND)
        main_sizer.Add(content_sizer, 1, wx.EXPAND)

        panel.SetSizer(main_sizer)

        self.Centre()

        # 창 닫기 이벤트
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_file_menu(self, event):
        # File 버튼 위치에서 드롭다운 메뉴 표시
        btn = event.GetEventObject()
        pos = btn.ClientToScreen((0, 0))
        menu = wx.Menu()
        menu.Append(wx.ID_ANY, 'open file')
        menu.Append(wx.ID_ANY, 'New')
        menu.Append(wx.ID_ANY, 'Save')
        menu.Append(wx.ID_ANY, 'Close')

        # 메뉴의 open file 선택 시 파일 다이얼로그
        self.Bind(wx.EVT_MENU, self.on_open_file, id=menu.GetMenuItems()[0].GetId())

        self.PopupMenu(menu, self.ScreenToClient(pos + (0, btn.GetSize()[1])))
        menu.Destroy()

    def on_open_file(self, event):
        # 파일 다이얼로그 표시
        with wx.FileDialog(self, "파일 열기",
                           wildcard="All files (*.*)|*.*",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()

    def on_close(self, event):
        # 첫 번째 프레임도 함께 종료
        if self.first_frame:
            self.first_frame.Destroy()
        self.Destroy()
