import wx
import numpy as np
import pandas as pd
import matplotlib
import os

from Frame.ReportFrame.SAE_J2951 import SAE_J2951
from Frame.ReportFrame.sae_report_generator import create_radar_chart, create_excel_report_from_template, \
    create_pdf_report
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime

from Panel.Menubar import MenuBar

matplotlib.use('WXAgg')

class ReportFrame(wx.Frame):
    """메인 프레임"""

    def __init__(self,parent):
        super().__init__(parent=None, title="SAE J2951 Analyzer", size=(1400, 900))

        self.results = None
        self.test_info = None
        self.time_data = None
        self.vsched_data = None
        self.vroll_data = None

        # 메인 패널
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 좌측 패널 (고정 크기)
        self.left_panel = LeftPanel(panel, self)
        main_sizer.Add(self.left_panel, 0, wx.EXPAND | wx.ALL, 5)

        # 구분선
        main_sizer.Add(wx.StaticLine(panel, style=wx.LI_VERTICAL), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)

        # 우측 패널 (메인 화면)
        right_panel = wx.Panel(panel)
        right_sizer = wx.BoxSizer(wx.VERTICAL)

        # 상단: 결과 요약 (이동됨)
        self.summary_panel = ResultsSummaryPanel(right_panel)
        right_sizer.Add(self.summary_panel, 0, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(wx.StaticLine(right_panel), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # 메인: 레이더 차트
        self.radar_panel = RadarChartPanel(right_panel)
        right_sizer.Add(self.radar_panel, 1, wx.EXPAND | wx.ALL, 10)

        right_panel.SetSizer(right_sizer)
        main_sizer.Add(right_panel, 1, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(main_sizer)

        # 상태바
        self.CreateStatusBar()
        self.SetStatusText("Ready")
        self.Centre()


    def update_results(self, results, test_info, time_data, vsched_data, vroll_data):
        """결과 업데이트"""
        self.results = results
        self.test_info = test_info
        self.time_data = time_data
        self.vsched_data = vsched_data
        self.vroll_data = vroll_data

        # 요약 업데이트 (먼저)
        self.summary_panel.update_results(results)

        # 차트 업데이트
        self.radar_panel.update_chart(results)

        self.SetStatusText(f"Analysis completed - DQM: {results.get('DQM', 0):.4f}")

    def export_excel(self):
        wildcard = "Excel files (*.xlsx)|*.xlsx"
        dlg = wx.FileDialog(self, "Save Excel Report",
                            defaultFile=f"sae_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            wildcard=wildcard,
                            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()

            try:
                chart_path = filepath.replace('.xlsx', '_chart.png')
                create_radar_chart(
                    self.results['ER_pct'], self.results['DR_pct'],
                    self.results['EER_pct'], self.results['ASCR_pct'],
                    self.results['IWR_pct'], self.results['RMSSE_mph'],
                    save_path=chart_path
                )

                template_path = self.left_panel.template_picker.GetPath()
                if not template_path or not os.path.exists(template_path):
                    template_path = None

                create_excel_report_from_template(
                    self.results, self.test_info, filepath, chart_path, template_path
                )

                wx.MessageBox(f"Excel report saved:\n{filepath}", "Success", wx.OK | wx.ICON_INFORMATION)
                self.SetStatusText(f"Excel exported: {os.path.basename(filepath)}")

            except Exception as e:
                wx.MessageBox(f"Error exporting Excel:\n{str(e)}", "Error", wx.OK | wx.ICON_ERROR)

        dlg.Destroy()

    def export_pdf(self):

        wildcard = "PDF files (*.pdf)|*.pdf"
        dlg = wx.FileDialog(self, "Save PDF Report",
                            defaultFile=f"sae_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            wildcard=wildcard,
                            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()

            try:
                create_pdf_report(self.results, self.test_info, filepath)
                wx.MessageBox(f"PDF report saved:\n{filepath}", "Success", wx.OK | wx.ICON_INFORMATION)
                self.SetStatusText(f"PDF exported: {os.path.basename(filepath)}")

            except Exception as e:
                wx.MessageBox(f"Error exporting PDF:\n{str(e)}", "Error", wx.OK | wx.ICON_ERROR)

        dlg.Destroy()

    def export_both(self):

        dlg = wx.DirDialog(self, "Choose output directory")

        if dlg.ShowModal() == wx.ID_OK:
            output_dir = dlg.GetPath()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            try:
                template_path = self.left_panel.template_picker.GetPath()
                if not template_path or not os.path.exists(template_path):
                    template_path = None

                excel_path = os.path.join(output_dir, f"sae_report_{timestamp}.xlsx")
                pdf_path = os.path.join(output_dir, f"sae_report_{timestamp}.pdf")
                chart_path = os.path.join(output_dir, f"sae_report_{timestamp}_chart.png")

                create_radar_chart(
                    self.results['ER_pct'], self.results['DR_pct'],
                    self.results['EER_pct'], self.results['ASCR_pct'],
                    self.results['IWR_pct'], self.results['RMSSE_mph'],
                    save_path=chart_path
                )

                create_excel_report_from_template(
                    self.results, self.test_info, excel_path, chart_path, template_path
                )

                create_pdf_report(self.results, self.test_info, pdf_path)

                wx.MessageBox(
                    f"Reports saved to:\n{output_dir}\n\n" +
                    f"• {os.path.basename(excel_path)}\n" +
                    f"• {os.path.basename(pdf_path)}\n" +
                    f"• {os.path.basename(chart_path)}",
                    "Success", wx.OK | wx.ICON_INFORMATION
                )
                self.SetStatusText(f"Both reports exported to: {output_dir}")

            except Exception as e:
                wx.MessageBox(f"Error exporting reports:\n{str(e)}", "Error", wx.OK | wx.ICON_ERROR)

        dlg.Destroy()

    def on_exit(self, event):
        self.Close(True)

    def on_about(self, event):
        info = wx.adv.AboutDialogInfo()
        info.SetName("SAE J2951 Analyzer")
        info.SetVersion("1.0")
        info.SetDescription(
            "Drive quality metrics analyzer for vehicle testing\n\nCalculates ER, DR, EER, ASCR, IWR, RMSSE, and DQM according to SAE J2951 standard.")
        wx.adv.AboutBox(info)


class LeftPanel(wx.Panel):
    """좌측 패널 - 파일 업로드 및 설정"""

    def __init__(self, parent, main_frame):
        super().__init__(parent)
        self.main_frame = main_frame
        self.SetBackgroundColour(wx.Colour(240, 240, 240))

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(self, label="SAE J2951 Analyzer")
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL | wx.CENTER, 15)

        main_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        main_sizer.AddSpacer(10)
       

        # 1. 파일 업로드
        file_box = wx.StaticBox(self, label="1. Input File")
        file_sizer = wx.StaticBoxSizer(file_box, wx.VERTICAL)

        self.file_picker = wx.FilePickerCtrl(
            self,
            message="Choose CSV file",
            wildcard="CSV files (*.csv)|*.csv",
            style=wx.FLP_USE_TEXTCTRL | wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST
        )
        file_sizer.Add(self.file_picker, 0, wx.EXPAND | wx.ALL, 5)

        self.load_btn = wx.Button(self, label="Load & Analyze")
        self.load_btn.Bind(wx.EVT_BUTTON, self.on_load_file)
        file_sizer.Add(self.load_btn, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(file_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # 2. 차량 파라미터
        param_box = wx.StaticBox(self, label="2. Vehicle Parameters")
        param_sizer = wx.StaticBoxSizer(param_box, wx.VERTICAL)

        grid = wx.FlexGridSizer(4, 2, 5, 5)

        grid.Add(wx.StaticText(self, label="Mass (kg):"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.mass_ctrl = wx.TextCtrl(self, value="1726.9")
        grid.Add(self.mass_ctrl, 1, wx.EXPAND)

        grid.Add(wx.StaticText(self, label="F₀ (N):"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.f0_ctrl = wx.TextCtrl(self, value="35.5")
        grid.Add(self.f0_ctrl, 1, wx.EXPAND)

        grid.Add(wx.StaticText(self, label="F₁ (N/kph):"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.f1_ctrl = wx.TextCtrl(self, value="1.453")
        grid.Add(self.f1_ctrl, 1, wx.EXPAND)

        grid.Add(wx.StaticText(self, label="F₂ (N/kph²):"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.f2_ctrl = wx.TextCtrl(self, value="0.03011")
        grid.Add(self.f2_ctrl, 1, wx.EXPAND)

        grid.AddGrowableCol(1)
        param_sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(param_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # 3. 테스트 정보
        info_box = wx.StaticBox(self, label="3. Test Information")
        info_sizer = wx.StaticBoxSizer(info_box, wx.VERTICAL)

        grid2 = wx.FlexGridSizer(3, 2, 5, 5)

        grid2.Add(wx.StaticText(self, label="Test ID:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.test_id_ctrl = wx.TextCtrl(self, value="TEST-001")
        grid2.Add(self.test_id_ctrl, 1, wx.EXPAND)

        grid2.Add(wx.StaticText(self, label="Vehicle:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.vehicle_ctrl = wx.TextCtrl(self, value="ACTYON2")
        grid2.Add(self.vehicle_ctrl, 1, wx.EXPAND)

        grid2.Add(wx.StaticText(self, label="Manufacturer:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.manufacturer_ctrl = wx.TextCtrl(self, value="Hyundai")
        grid2.Add(self.manufacturer_ctrl, 1, wx.EXPAND)

        grid2.AddGrowableCol(1)
        info_sizer.Add(grid2, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(info_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # 4. Export 옵션
        output_box = wx.StaticBox(self, label="4. Export Options")
        output_sizer = wx.StaticBoxSizer(output_box, wx.VERTICAL)

        self.excel_btn = wx.Button(self, label="📑 Export to Excel")
        self.excel_btn.Bind(wx.EVT_BUTTON, self.on_export_excel)
        output_sizer.Add(self.excel_btn, 0, wx.EXPAND | wx.ALL, 5)

        self.pdf_btn = wx.Button(self, label="📄 Export to PDF")
        self.pdf_btn.Bind(wx.EVT_BUTTON, self.on_export_pdf)
        output_sizer.Add(self.pdf_btn, 0, wx.EXPAND | wx.ALL, 5)

        self.both_btn = wx.Button(self, label="📦 Export Both (Excel + PDF)")
        self.both_btn.Bind(wx.EVT_BUTTON, self.on_export_both)
        output_sizer.Add(self.both_btn, 0, wx.EXPAND | wx.ALL, 5)

        output_sizer.AddSpacer(10)
        output_sizer.Add(wx.StaticText(self, label="Template (Optional):"), 0, wx.LEFT, 5)
        self.template_picker = wx.FilePickerCtrl(
            self,
            message="Choose Excel template",
            wildcard="Excel files (*.xlsx)|*.xlsx",
            style=wx.FLP_USE_TEXTCTRL | wx.FLP_OPEN
        )
        output_sizer.Add(self.template_picker, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(output_sizer, 0, wx.EXPAND | wx.ALL, 10)

        self.disable_export_buttons()

        self.SetSizer(main_sizer)

    def disable_export_buttons(self):
        self.excel_btn.Enable(False)
        self.pdf_btn.Enable(False)
        self.both_btn.Enable(False)

    def enable_export_buttons(self):
        self.excel_btn.Enable(True)
        self.pdf_btn.Enable(True)
        self.both_btn.Enable(True)

    def on_load_file(self, event):
        filepath = self.file_picker.GetPath()
        if not filepath or not os.path.exists(filepath):
            wx.MessageBox("Please select a valid CSV file", "Error", wx.OK | wx.ICON_ERROR)
            return

        try:
            mass_kg = float(self.mass_ctrl.GetValue())
            f0 = float(self.f0_ctrl.GetValue())
            f1 = float(self.f1_ctrl.GetValue())
            f2 = float(self.f2_ctrl.GetValue())

            progress = wx.ProgressDialog(
                "Loading",
                "Reading CSV file...",
                maximum=100,
                parent=self,
                style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE
            )

            progress.Update(20, "Reading CSV file...")

            df = pd.read_csv(filepath, sep=None, engine="python")
            cols = {c.lower(): c for c in df.columns}

            time_col = cols.get("time") or cols.get("t") or "time"
            vs_col = cols.get("vsched") or cols.get("vnom") or "Vsched"
            vr_col = cols.get("vroll") or cols.get("vact") or "Vroll"

            time_s = pd.to_numeric(df[time_col], errors="coerce").to_numpy()
            Vs_kph = pd.to_numeric(df[vs_col], errors="coerce").to_numpy()
            Vr_kph = pd.to_numeric(df[vr_col], errors="coerce").to_numpy()

            progress.Update(50, "Calculating SAE J2951 metrics...")

            ABCs_SI = np.array([f0, f1, f2])
            calculator = SAE_J2951()
            results = calculator.calculate(time_s, Vr_kph, Vs_kph, ABCs_SI, mass_kg)

            progress.Update(80, "Updating display...")

            test_info = {
                'Test ID': self.test_id_ctrl.GetValue(),
                'Vehicle ID': self.vehicle_ctrl.GetValue(),
                'Vehicle manufacturer': self.manufacturer_ctrl.GetValue(),
                'Vehicle type': self.vehicle_ctrl.GetValue(),
                'Test Date': datetime.now().strftime('%Y-%m-%d'),
                'Mass': str(mass_kg),
                'F0_N': str(f0),
                'F1_N_per_kph': str(f1),
                'F2_N_per_kph2': str(f2),
                'Test cycle': 'WLTC',
            }

            self.main_frame.update_results(results, test_info, time_s, Vs_kph, Vr_kph)

            self.enable_export_buttons()

            progress.Update(100, "Done!")
            progress.Destroy()

            wx.MessageBox("Analysis completed successfully!", "Success", wx.OK | wx.ICON_INFORMATION)

        except Exception as e:
            if 'progress' in locals():
                progress.Destroy()
            wx.MessageBox(f"Error during analysis:\n{str(e)}", "Error", wx.OK | wx.ICON_ERROR)



    def on_export_excel(self, event):
        self.main_frame.export_excel()

    def on_export_pdf(self, event):
        self.main_frame.export_pdf()

    def on_export_both(self, event):
        self.main_frame.export_both()


class RadarChartPanel(wx.Panel):
    """레이더 차트 패널"""

    def __init__(self, parent):
        super().__init__(parent)
        self.SetBackgroundColour(wx.WHITE)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.title = wx.StaticText(self, label="SAE J2951 Radar Chart")
        title_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title.SetFont(title_font)
        main_sizer.Add(self.title, 0, wx.ALL | wx.CENTER, 15)

        self.figure = Figure(figsize=(8, 8), dpi=100)
        self.canvas = FigureCanvas(self, -1, self.figure)

        main_sizer.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 10)

        self.empty_label = wx.StaticText(self, label="Load a CSV file to view results")
        self.empty_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        self.empty_label.SetForegroundColour(wx.Colour(128, 128, 128))

        self.canvas.Hide()
        main_sizer.Add(self.empty_label, 0, wx.ALL | wx.CENTER, 50)

        self.SetSizer(main_sizer)

        self.results = None

    def update_chart(self, results):
        """차트 업데이트 - 스케일 수정"""
        self.results = results

        self.empty_label.Hide()
        self.canvas.Show()

        self.figure.clear()

        ax = self.figure.add_subplot(111, projection='polar')

        categories = ['ER', 'DR', 'EER', 'ASCR', 'IWR', 'RMSSE']
        values = [
            results.get('ER_pct', 0),
            results.get('DR_pct', 0),
            results.get('EER_pct', 0),
            results.get('ASCR_pct', 0),
            results.get('IWR_pct', 0),
            results.get('RMSSE_mph', 0)
        ]

        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values_plot = values + values[:1]
        angles_plot = angles + angles[:1]

        # 고정 스케일: -3 ~ 3
        y_limit = 4
        ax.set_ylim(-y_limit, y_limit)

        # Y축 틱: -2, -1, 0, 1, 2만 표시
        yticks = [-3,-2, -1, 0, 1, 2,3]
        ax.set_yticks(yticks)
        ax.set_yticklabels([str(y) for y in yticks], size=9, color='gray')

        ax.set_xticks(angles)
        ax.set_xticklabels([])

        ax.grid(True, linestyle='-', alpha=0.3, color='gray', linewidth=0.5)

        # 기준선 (파란색)
        zeros = [0] * len(angles_plot)
        ax.plot(angles_plot, zeros, '--', linewidth=2,
                color='#4169E1', alpha=0.8, zorder=3)

        # 실제 데이터 (빨간색)
        ax.plot(angles_plot, values_plot, '--', linewidth=2,
                color='#DC143C', alpha=0.8, zorder=4)

        ax.fill(angles_plot, values_plot, alpha=0.25, color='#DC143C', zorder=2)
        ax.fill(angles_plot, zeros, alpha=0.15, color='#4169E1', zorder=1)

        ax.plot(angles_plot, values_plot, 'o',
                color='#DC143C', markersize=8, markeredgecolor='white',
                markeredgewidth=1.5, zorder=5)

        # 레이블 배치
        for angle, category in zip(angles, categories):
            label_distance = y_limit + 0.8
            x = angle
            y = label_distance

            ha = 'center'
            va = 'center'

            if angle == 0:
                ha = 'left'
            elif angle < np.pi:
                if angle < np.pi / 2:
                    ha = 'left'
                else:
                    ha = 'right'
            else:
                if angle < 3 * np.pi / 2:
                    ha = 'right'
                else:
                    ha = 'left'

            ax.text(x, y, category,
                    ha=ha, va=va,
                    fontsize=12, fontweight='bold',
                    color='black')

        ax.set_theta_zero_location('E')
        ax.set_theta_direction(1)

        self.canvas.draw()
        self.Layout()


class ResultsSummaryPanel(wx.Panel):
    """결과 요약 패널 - 상단 배치, 큰 글자"""

    def __init__(self, parent):
        super().__init__(parent)
        self.SetBackgroundColour(wx.Colour(250, 250, 250))

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 제목
        title = wx.StaticText(self, label="Test Results Summary")
        title_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL | wx.CENTER, 10)

        # 결과 그리드 - 7분할 크게
        grid = wx.FlexGridSizer(2, 7, 8, 8)  # 간격 늘림
        for i in range(7):
            grid.AddGrowableCol(i, 1)  # 각 열 균등 확장

        # 헤더
        headers = ['ER (%)', 'DR (%)', 'EER (%)', 'ASCR (%)', 'IWR (%)', 'RMSSE (mph)', 'DQM']
        for header in headers:
            label = wx.StaticText(self, label=header)
            label.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            grid.Add(label, 1, wx.ALIGN_CENTER | wx.ALL, 5)  # proportion=1로 확장

        # 값 필드 - 큰 글자
        self.value_ctrls = []
        for _ in range(7):
            ctrl = wx.StaticText(self, label="-")
            ctrl.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))  # 16pt로 크게
            grid.Add(ctrl, 1, wx.ALIGN_CENTER | wx.ALL, 5)  # proportion=1로 확장
            self.value_ctrls.append(ctrl)

        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 10)  # proportion=1로 확장

        # 상태 표시 (필수!)
        self.status_text = wx.StaticText(self, label="No data loaded")
        self.status_text.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        main_sizer.Add(self.status_text, 0, wx.ALL | wx.CENTER, 8)

        self.SetSizer(main_sizer)

    def update_results(self, results):
        keys = ['ER_pct', 'DR_pct', 'EER_pct', 'ASCR_pct', 'IWR_pct', 'RMSSE_mph', 'DQM']

        for i, key in enumerate(keys):
            value = results.get(key, 0)
            self.value_ctrls[i].SetLabel(f"{value:.4f}")

            if key == 'DQM':
                if value < 1.0:
                    color = wx.Colour(198, 239, 206)
                elif value < 2.0:
                    color = wx.Colour(255, 235, 156)
                else:
                    color = wx.Colour(255, 199, 206)
            else:
                abs_val = abs(value)
                if abs_val < 1.0:
                    color = wx.Colour(198, 239, 206)
                elif abs_val < 2.0:
                    color = wx.Colour(255, 235, 156)
                else:
                    color = wx.Colour(255, 199, 206)

            self.value_ctrls[i].SetBackgroundColour(color)

        dqm = results.get('DQM', 0)
        if dqm < 1.0:
            status = "Excellent quality"
        elif dqm < 2.0:
            status = "Good quality"
        else:
            status = "Poor quality - Review recommended"

        self.status_text.SetLabel(f"Status: {status}")

        self.Layout()
        self.Refresh()


def main():
    app = wx.App()
    frame = ReportFrame()
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()