import wx


class FirstFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='App name', size=(800, 600))

        # 패널 생성
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(240, 240, 240))

        # 메인 sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 상단 메뉴바 영역
        menubar_panel = wx.Panel(panel)
        menubar_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        menubar_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 메뉴 버튼들
        file_btn = wx.Button(menubar_panel, label='File', style=wx.BORDER_NONE)
        analyze_btn = wx.Button(menubar_panel, label='Analyze', style=wx.BORDER_NONE)
        extract_btn = wx.Button(menubar_panel, label='Extract', style=wx.BORDER_NONE)
        exit_btn = wx.Button(menubar_panel, label='Exit', style=wx.BORDER_NONE)

        menubar_sizer.Add(file_btn, 0, wx.ALL, 5)
        menubar_sizer.Add(analyze_btn, 0, wx.ALL, 5)
        menubar_sizer.Add(extract_btn, 0, wx.ALL, 5)
        menubar_sizer.Add(exit_btn, 0, wx.ALL, 5)

        menubar_panel.SetSizer(menubar_sizer)

        # 이미지 영역
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        img = wx.Image("./images/img.png", wx.BITMAP_TYPE_ANY)
        image_panel = wx.Panel(panel)
        image_panel.SetBackgroundColour(wx.Colour(70, 120, 150))
        image_panel.SetMinSize((410, 300))

        bitmap = wx.StaticBitmap(image_panel, -1, wx.Bitmap(img))
        image_sizer = wx.BoxSizer(wx.VERTICAL)
        image_sizer.Add(bitmap, 0, wx.ALL | wx.CENTER, 10)
        image_panel.SetSizer(image_sizer)

        # 다음 버튼
        next_btn = wx.Button(panel, label='Next', size=(150, 40))
        next_btn.Bind(wx.EVT_BUTTON, self.on_next)

        # 레이아웃 구성
        content_sizer.AddStretchSpacer()
        content_sizer.Add(image_panel, 0, wx.ALL | wx.CENTER, 20)
        content_sizer.AddStretchSpacer()
        content_sizer.Add(next_btn, 0, wx.ALL | wx.CENTER, 20)

        main_sizer.Add(menubar_panel, 0, wx.EXPAND)
        main_sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND)
        main_sizer.Add(content_sizer, 1, wx.EXPAND)

        panel.SetSizer(main_sizer)

        self.Centre()
        self.Show()

    def on_next(self, event):
        # 두 번째 화면으로 전환
        self.Hide()
        second_frame = SecondFrame(self)
        second_frame.Show()


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
        menubar_panel = wx.Panel(panel)
        menubar_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        menubar_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 메뉴 버튼들
        file_btn = wx.Button(menubar_panel, label='File', style=wx.BORDER_NONE)
        analyze_btn = wx.Button(menubar_panel, label='Analyze', style=wx.BORDER_NONE)
        extract_btn = wx.Button(menubar_panel, label='Extract', style=wx.BORDER_NONE)
        exit_btn = wx.Button(menubar_panel, label='Exit', style=wx.BORDER_NONE)

        # File 버튼 클릭 시 드롭다운 메뉴
        file_btn.Bind(wx.EVT_BUTTON, self.on_file_menu)

        menubar_sizer.Add(file_btn, 0, wx.ALL, 5)
        menubar_sizer.Add(analyze_btn, 0, wx.ALL, 5)
        menubar_sizer.Add(extract_btn, 0, wx.ALL, 5)
        menubar_sizer.Add(exit_btn, 0, wx.ALL, 5)

        menubar_panel.SetSizer(menubar_sizer)

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


if __name__ == '__main__':
    app = wx.App()
    frame = FirstFrame()
    app.MainLoop()