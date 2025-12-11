import wx


class MenuBar(wx.Panel):
    """재사용 가능한 메뉴바 컴포넌트"""

    def __init__(self, parent):
        super().__init__(parent)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))

        # 메뉴바 레이아웃
        menubar_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 메뉴 버튼들 생성
        self.file_btn = wx.Button(self, label='File', style=wx.BORDER_NONE)
        self.analyze_btn = wx.Button(self, label='Analyze', style=wx.BORDER_NONE)
        self.extract_btn = wx.Button(self, label='Extract', style=wx.BORDER_NONE)
        self.exit_btn = wx.Button(self, label='Exit', style=wx.BORDER_NONE)

        # 버튼들 배치
        menubar_sizer.Add(self.file_btn, 0, wx.ALL, 5)
        menubar_sizer.Add(self.analyze_btn, 0, wx.ALL, 5)
        menubar_sizer.Add(self.extract_btn, 0, wx.ALL, 5)
        menubar_sizer.Add(self.exit_btn, 0, wx.ALL, 5)

        self.SetSizer(menubar_sizer)

    def bind_file_button(self, handler):
        """File 버튼에 이벤트 핸들러 연결"""
        self.file_btn.Bind(wx.EVT_BUTTON, handler)

    def bind_analyze_button(self, handler):
        """Analyze 버튼에 이벤트 핸들러 연결"""
        self.analyze_btn.Bind(wx.EVT_BUTTON, handler)

    def bind_extract_button(self, handler):
        """Extract 버튼에 이벤트 핸들러 연결"""
        self.extract_btn.Bind(wx.EVT_BUTTON, handler)

    def bind_exit_button(self, handler):
        """Exit 버튼에 이벤트 핸들러 연결"""
        self.exit_btn.Bind(wx.EVT_BUTTON, handler)
        print("hello")