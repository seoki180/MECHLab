import wx
import pandas as pd
import matplotlib

matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from Panel.Menubar import MenuBar


class FileFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent=None, title='Speed Data Viewer', size=(1600, 800))
        self.first_frame = parent
        self.current_file_path = None
        self.df = None

        # 애니메이션 관련 변수
        self.timer = None
        self.current_time_index = 0
        self.is_playing = False

        # 패널 생성
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(240, 240, 240))

        # 메인 레이아웃
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 상단 메뉴바 영역
        menubar_panel = MenuBar(panel)

        # 콘텐츠 영역
        content_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 왼쪽 영역 - 컨트롤 패널
        left_panel = wx.Panel(panel)
        left_panel.SetBackgroundColour(wx.Colour(250, 250, 250))
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        # open file 버튼
        open_btn = wx.Button(left_panel, label='Open File', size=(150, 40))
        open_btn.Bind(wx.EVT_BUTTON, self.on_open_file)

        # 재생 컨트롤 버튼들
        control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.play_btn = wx.Button(left_panel, label='▶ Play', size=(70, 35))
        self.pause_btn = wx.Button(left_panel, label='⏸ Pause', size=(70, 35))
        self.reset_btn = wx.Button(left_panel, label='⏮ Reset', size=(70, 35))

        self.play_btn.Bind(wx.EVT_BUTTON, self.on_play)
        self.pause_btn.Bind(wx.EVT_BUTTON, self.on_pause)
        self.reset_btn.Bind(wx.EVT_BUTTON, self.on_reset)

        self.play_btn.Enable(False)
        self.pause_btn.Enable(False)
        self.reset_btn.Enable(False)

        control_sizer.Add(self.play_btn, 0, wx.ALL, 2)
        control_sizer.Add(self.pause_btn, 0, wx.ALL, 2)
        control_sizer.Add(self.reset_btn, 0, wx.ALL, 2)

        # 속도 조절 슬라이더
        speed_label = wx.StaticText(left_panel, label="재생 속도:")
        self.speed_slider = wx.Slider(left_panel, value=50, minValue=10, maxValue=200,
                                      style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.speed_slider.SetTickFreq(10)

        # 진행 상태 표시
        self.progress_text = wx.StaticText(left_panel, label="진행: 0.0 / 0.0 초")

        # 파일 정보 텍스트
        self.file_info_text = wx.TextCtrl(
            left_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
            size=(200, -1)
        )
        self.file_info_text.SetValue("파일이 선택되지 않았습니다.")

        # 왼쪽 레이아웃 구성
        left_sizer.Add(open_btn, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        left_sizer.Add(wx.StaticLine(left_panel), 0, wx.EXPAND | wx.ALL, 5)
        left_sizer.Add(wx.StaticText(left_panel, label="재생 컨트롤:"), 0, wx.ALL, 5)
        left_sizer.Add(control_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 5)
        left_sizer.Add(speed_label, 0, wx.ALL, 5)
        left_sizer.Add(self.speed_slider, 0, wx.ALL | wx.EXPAND, 5)
        left_sizer.Add(self.progress_text, 0, wx.ALL, 5)
        left_sizer.Add(wx.StaticLine(left_panel), 0, wx.EXPAND | wx.ALL, 5)
        left_sizer.Add(wx.StaticText(left_panel, label="파일 정보:"), 0, wx.ALL, 5)
        left_sizer.Add(self.file_info_text, 1, wx.ALL | wx.EXPAND, 5)

        left_panel.SetSizer(left_sizer)

        # 그래프 영역
        graph_panel = wx.Panel(panel)
        graph_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        graph_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 왼쪽 그래프 - 전체 뷰 (세로)
        left_graph_panel = wx.Panel(graph_panel)
        left_graph_sizer = wx.BoxSizer(wx.VERTICAL)

        self.figure_left = Figure(figsize=(3, 8), facecolor='black')
        self.canvas_left = FigureCanvas(left_graph_panel, -1, self.figure_left)
        self.ax_left = self.figure_left.add_subplot(111)

        left_graph_sizer.Add(wx.StaticText(left_graph_panel, label="전체 그래프"),
                             0, wx.ALL | wx.ALIGN_CENTER, 5)
        left_graph_sizer.Add(self.canvas_left, 1, wx.EXPAND | wx.ALL, 5)
        left_graph_panel.SetSizer(left_graph_sizer)

        # 오른쪽 그래프 - 진행 뷰 (가로)
        right_graph_panel = wx.Panel(graph_panel)
        right_graph_sizer = wx.BoxSizer(wx.VERTICAL)

        self.figure_right = Figure(figsize=(10, 8), facecolor='black')
        self.canvas_right = FigureCanvas(right_graph_panel, -1, self.figure_right)
        self.ax_right = self.figure_right.add_subplot(111)

        right_graph_sizer.Add(wx.StaticText(right_graph_panel, label="진행 그래프"),
                              0, wx.ALL | wx.ALIGN_CENTER, 5)
        right_graph_sizer.Add(self.canvas_right, 1, wx.EXPAND | wx.ALL, 5)
        right_graph_panel.SetSizer(right_graph_sizer)

        # 그래프 레이아웃
        graph_sizer.Add(left_graph_panel, 0, wx.EXPAND | wx.ALL, 5)
        graph_sizer.Add(wx.StaticLine(graph_panel, style=wx.LI_VERTICAL), 0, wx.EXPAND)
        graph_sizer.Add(right_graph_panel, 1, wx.EXPAND | wx.ALL, 5)
        graph_panel.SetSizer(graph_sizer)

        # 초기 그래프 설정
        self.setup_empty_graphs()

        # 콘텐츠 레이아웃에 추가
        content_sizer.Add(left_panel, 0, wx.ALL | wx.EXPAND, 5)
        content_sizer.Add(wx.StaticLine(panel, style=wx.LI_VERTICAL), 0, wx.EXPAND)
        content_sizer.Add(graph_panel, 1, wx.ALL | wx.EXPAND, 5)

        # 메인 레이아웃 구성
        main_sizer.Add(menubar_panel, 0, wx.EXPAND)
        main_sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND)
        main_sizer.Add(content_sizer, 1, wx.EXPAND)

        panel.SetSizer(main_sizer)

        self.Centre()

        # 창 닫기 이벤트
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def setup_empty_graphs(self):
        """빈 그래프 초기 설정"""
        # 왼쪽 그래프 (전체 뷰 - 세로)
        self.ax_left.clear()
        self.ax_left.set_facecolor('black')
        self.ax_left.set_ylabel('km/h', fontsize=10, color='white')
        self.ax_left.set_xlabel('time (s)', fontsize=10, color='white')
        self.ax_left.grid(True, color='#333333', linestyle='-', linewidth=0.5, alpha=0.3)
        self.ax_left.tick_params(colors='white', labelsize=8)
        self.ax_left.spines['bottom'].set_color('white')
        self.ax_left.spines['top'].set_color('white')
        self.ax_left.spines['left'].set_color('white')
        self.ax_left.spines['right'].set_color('white')
        self.ax_left.text(0.5, 0.5, 'No Data',
                          horizontalalignment='center',
                          verticalalignment='center',
                          transform=self.ax_left.transAxes,
                          fontsize=14, color='gray', alpha=0.5)

        # 오른쪽 그래프 (진행 뷰 - 가로)
        self.ax_right.clear()
        self.ax_right.set_facecolor('black')
        self.ax_right.set_xlabel('time (s)', fontsize=12, color='white')
        self.ax_right.set_ylabel('km/h', fontsize=12, color='white')
        self.ax_right.grid(True, color='#333333', linestyle='-', linewidth=0.5, alpha=0.3)
        self.ax_right.tick_params(colors='white')
        self.ax_right.spines['bottom'].set_color('white')
        self.ax_right.spines['top'].set_color('white')
        self.ax_right.spines['left'].set_color('white')
        self.ax_right.spines['right'].set_color('white')
        self.ax_right.text(0.5, 0.5, 'No Data',
                           horizontalalignment='center',
                           verticalalignment='center',
                           transform=self.ax_right.transAxes,
                           fontsize=20, color='gray', alpha=0.5)


        self.canvas_left.draw()
        self.canvas_right.draw()

    def on_file_menu(self, event):
        """File 메뉴 버튼 클릭"""
        btn = event.GetEventObject()
        pos = btn.ClientToScreen((0, 0))
        menu = wx.Menu()
        menu.Append(wx.ID_ANY, 'Open File')
        menu.Append(wx.ID_ANY, 'New')
        menu.Append(wx.ID_ANY, 'Save')
        menu.Append(wx.ID_ANY, 'Close')

        self.Bind(wx.EVT_MENU, self.on_open_file, id=menu.GetMenuItems()[0].GetId())

        self.PopupMenu(menu, self.ScreenToClient(pos + (0, btn.GetSize()[1])))
        menu.Destroy()

    def on_open_file(self, event):
        """파일 열기 다이얼로그"""
        with wx.FileDialog(self, "엑셀 파일 열기",
                           wildcard="Excel files (*.xlsx;*.xls)|*.xlsx;*.xls|All files (*.*)|*.*",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            self.current_file_path = pathname

            # 파일 로드 및 그래프 그리기
            self.load_and_plot_data(pathname)

    def load_and_plot_data(self, file_path):
        """엑셀 파일을 로드하고 그래프를 그림"""
        try:
            # 기존 타이머 정지
            if self.timer:
                self.timer.Stop()
                self.timer = None

            # 엑셀 파일 읽기
            self.df = pd.read_excel(file_path)

            # 데이터 검증
            required_columns = ['time', 'ScheduledSpeed', 'SpeedFeedback']
            if not all(col in self.df.columns for col in required_columns):
                wx.MessageBox(
                    f"엑셀 파일에 필요한 컬럼이 없습니다.\n필요한 컬럼: {', '.join(required_columns)}",
                    "오류",
                    wx.OK | wx.ICON_ERROR
                )
                return

            # 파일 정보 업데이트
            file_info = f"파일명: {file_path.split('/')[-1]}\n\n"
            file_info += f"데이터 포인트: {len(self.df):,}개\n"
            file_info += f"총 시간: {self.df['time'].max():.2f}초\n"
            file_info += f"최대 목표 속도: {self.df['ScheduledSpeed'].max():.2f} km/h\n"
            file_info += f"최대 실제 속도: {self.df['SpeedFeedback'].max():.2f} km/h\n"
            self.file_info_text.SetValue(file_info)

            # 애니메이션 초기화
            self.current_time_index = 0
            self.is_playing = False

            # 컨트롤 버튼 활성화
            self.play_btn.Enable(True)
            self.pause_btn.Enable(False)
            self.reset_btn.Enable(True)

            # 그래프 그리기
            self.plot_full_graph()
            self.plot_progress_graph()

            wx.MessageBox("파일을 성공적으로 로드했습니다!", "완료", wx.OK | wx.ICON_INFORMATION)

        except Exception as e:
            wx.MessageBox(f"파일 로드 중 오류가 발생했습니다:\n{str(e)}", "오류", wx.OK | wx.ICON_ERROR)

    def plot_full_graph(self):
        """왼쪽에 전체 그래프 표시 (세로 방향)"""
        if self.df is None:
            return

        self.ax_left.clear()
        self.ax_left.set_facecolor('black')

        # 세로 방향으로 그래프 그리기 (time을 y축에, speed를 x축에)
        self.ax_left.plot(self.df['ScheduledSpeed'], self.df['time'],
                          color='#FF4444', linewidth=1.5, label='Scheduled')
        self.ax_left.plot(self.df['SpeedFeedback'], self.df['time'],
                          color='white', linewidth=1.5, label='Feedback')

        # 축 설정
        self.ax_left.set_xlabel('km/h', fontsize=10, color='white')
        self.ax_left.set_ylabel('time (s)', fontsize=10, color='white')
        self.ax_left.set_title('Full View', fontsize=11, color='white', pad=10)

        # y축 반전 (위에서 아래로)
        self.ax_left.invert_yaxis()

        # 그리드
        self.ax_left.grid(True, color='#333333', linestyle='-', linewidth=0.5, alpha=0.3)

        # 축 범위
        max_speed = max(self.df['ScheduledSpeed'].max(), self.df['SpeedFeedback'].max())
        self.ax_left.set_xlim(0, max_speed * 1.1)
        self.ax_left.set_ylim(self.df['time'].max(), 0)

        # 축 색상
        self.ax_left.spines['bottom'].set_color('white')
        self.ax_left.spines['top'].set_color('white')
        self.ax_left.spines['left'].set_color('white')
        self.ax_left.spines['right'].set_color('white')
        self.ax_left.tick_params(colors='white', labelsize=8)

        # 범례
        self.ax_left.legend(loc='lower right', fontsize=8, framealpha=0.8)

        # 현재 위치 표시 라인
        self.current_position_line = self.ax_left.axhline(y=0, color='lime', linewidth=2,
                                                          linestyle='--', alpha=0.8)

        self.figure_left.tight_layout()
        self.canvas_left.draw()

    def plot_progress_graph(self):
        """오른쪽에 진행 그래프 표시 (가로 방향)"""
        if self.df is None:
            return

        self.ax_right.clear()
        self.ax_right.set_facecolor('black')

        # 현재 시간까지의 데이터만 표시
        current_time = self.df['time'].iloc[self.current_time_index]
        mask = self.df['time'] <= current_time

        # 데이터 플롯
        # self.ax_right.plot( self.df[mask]['ScheduledSpeed'],self.df[mask]['time'],
        #                color='#FF4444', linewidth=2, label='Scheduled')

        self.ax_right.plot(self.df['ScheduledSpeed'], self.df['time'],
                           color='#FF4444', linewidth=2, label='Scheduled')
        self.ax_right.plot(self.df[mask]['SpeedFeedback'],self.df[mask]['time'],
                           color='white', linewidth=2, label='Feedback')

        # 축 설정
        self.ax_right.set_ylabel('time (s)', fontsize=12, color='white')
        self.ax_right.set_xlabel('km/h', fontsize=12, color='white')
        self.ax_right.set_title(f'Progress View - Current Time: {current_time:.1f}s',
                                fontsize=13, color='white', pad=15)

        # 그리드
        self.ax_right.grid(True, color='#333333', linestyle='-', linewidth=0.5, alpha=0.3)

        # 축 범위 - 현재 시간 기준으로 윈도우 설정 (30초 윈도우)
        window_size = 30  # 30초 윈도우
        max_speed = max(self.df['ScheduledSpeed'].max(), self.df['SpeedFeedback'].max())

        time_start = max(0, current_time - window_size)
        time_end = min(self.df['time'].max(), current_time + 5)

        self.ax_right.set_ylim(time_start, time_end)
        self.ax_right.set_xlim(0, max_speed * 1.1)

        # 현재 위치 표시 라인
        self.ax_right.axhline(y=current_time, color='lime', linewidth=2,
                              linestyle='--', alpha=0.8, label='Current')

        # 축 색상
        self.ax_right.spines['bottom'].set_color('white')
        self.ax_right.spines['top'].set_color('white')
        self.ax_right.spines['left'].set_color('white')
        self.ax_right.spines['right'].set_color('white')
        self.ax_right.tick_params(colors='white')

        # 범례
        self.ax_right.legend(loc='upper left', fontsize=10, framealpha=0.8)

        self.figure_right.tight_layout()
        self.canvas_right.draw()

        # 진행 상태 업데이트
        total_time = self.df['time'].max()
        self.progress_text.SetLabel(
            f"진행: {current_time:.1f} / {total_time:.1f} 초 ({current_time / total_time * 100:.1f}%)")

    def on_play(self, event):
        """재생 시작"""
        if self.df is None:
            return

        self.is_playing = True
        self.play_btn.Enable(False)
        self.pause_btn.Enable(True)

        # 타이머 시작 (속도 조절 반영)
        speed_factor = self.speed_slider.GetValue() / 50.0  # 50이 기본 속도 (1배속)
        interval = max(10, int(100 / speed_factor))  # 최소 10ms

        if not self.timer:
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.on_timer)

        self.timer.Start(interval)

    def on_pause(self, event):
        """재생 일시정지"""
        self.is_playing = False
        self.play_btn.Enable(True)
        self.pause_btn.Enable(False)

        if self.timer:
            self.timer.Stop()

    def on_reset(self, event):
        """처음으로 리셋"""
        self.is_playing = False
        self.current_time_index = 0

        if self.timer:
            self.timer.Stop()

        self.play_btn.Enable(True)
        self.pause_btn.Enable(False)

        # 그래프 업데이트
        if self.df is not None:
            self.plot_full_graph()
            self.plot_progress_graph()

    def on_timer(self, event):
        """타이머 이벤트 - 그래프 업데이트"""
        if self.df is None or not self.is_playing:
            return

        # 인덱스 증가 (속도에 따라)
        speed_factor = self.speed_slider.GetValue() / 50.0
        step = max(1, int(10 * speed_factor))

        self.current_time_index += step

        # 끝에 도달하면 정지
        if self.current_time_index >= len(self.df):
            self.current_time_index = len(self.df) - 1
            self.on_pause(None)
            return

        # 왼쪽 그래프의 현재 위치 라인 업데이트
        current_time = self.df['time'].iloc[self.current_time_index]
        if hasattr(self, 'current_position_line'):
            self.current_position_line.set_ydata([current_time, current_time])
            self.canvas_left.draw_idle()

        # 오른쪽 그래프 업데이트
        self.plot_progress_graph()

    def on_close(self, event):
        """창 닫기"""
        if self.timer:
            self.timer.Stop()

        if self.first_frame:
            self.first_frame.Destroy()
        self.Destroy()


if __name__ == '__main__':
    app = wx.App()
    frame = FileFrame(None)
    frame.Show()
