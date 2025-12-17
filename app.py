import wx

from Frame.MenuFrame import MenuFrame
from Panel.Menubar import MenuBar


class InitFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='App name', size=(800, 600))

        # 패널 생성
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(240, 240, 240))

        # 메인 sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 메뉴 버튼들
        menubar = MenuBar(panel)
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

        main_sizer.Add(menubar, 0, wx.EXPAND)
        main_sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND)
        main_sizer.Add(content_sizer, 1, wx.EXPAND)

        panel.SetSizer(main_sizer)

        self.Centre()
        self.Show()

    def on_next(self, event):
        # 두 번째 화면으로 전환
        self.Hide()
        menu_frame = MenuFrame(self)
        menu_frame.Show()



if __name__ == '__main__':
    app = wx.App()
    frame = InitFrame()
    app.MainLoop()