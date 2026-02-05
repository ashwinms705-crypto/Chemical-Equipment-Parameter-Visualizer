import sys
import requests
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

API_URL = "http://127.0.0.1:8000/api"

class UploadWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def run(self):
        try:
            with open(self.filename, "rb") as f:
                response = requests.post(f"{API_URL}/upload/", files={"file": f}, timeout=30)
            if response.status_code == 201:
                self.finished.emit(response.json())
            else:
                self.error.emit(response.text)
        except Exception as e:
            self.error.emit(str(e))

class HistoryWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def run(self):
        try:
            response = requests.get(f"{API_URL}/history/", timeout=10)
            if response.status_code == 200:
                self.finished.emit(response.json())
            else:
                self.error.emit(response.text)
        except Exception as e:
            self.error.emit(str(e))

class ReportWorker(QThread):
    finished = pyqtSignal(bytes)
    error = pyqtSignal(str)

    def run(self):
        try:
            response = requests.get(f"{API_URL}/report/", timeout=10)
            if response.status_code == 200:
                self.finished.emit(response.content)
            else:
                self.error.emit(response.text)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chemical Equipment Visualizer")
        self.setGeometry(100, 100, 1400, 900)

        self.upload_worker = None
        self.history_worker = None
        self.report_worker = None
        
        self.pie_ax = None
        self.annot = None

        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #0f172a; color: #f1f5f9; }
            QLabel { font-size: 14px; }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2563eb; }
            QPushButton:disabled { background-color: #334155; }
            QTabBar::tab { background: #1e293b; padding: 10px; }
            QTabBar::tab:selected { background: #3b82f6; }
            QTableWidget { background-color: #1e293b; color: #f1f5f9; }
            QHeaderView::section { background-color: #0f172a; color: #f1f5f9; padding: 5px; }
        """)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.dashboard_tab = QWidget()
        self.history_tab = QWidget()

        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.history_tab, "History")

        self.setup_dashboard()
        self.setup_history()

        self.load_history()

    def setup_dashboard(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        header_container = QWidget()
        header_container.setFixedHeight(50)
        header_container.setStyleSheet("background-color: #1e293b; border-radius: 6px;")
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(10, 5, 10, 5)

        title = QLabel("Chemical Visualizer Dashboard")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc; border: none;")
        
        self.upload_btn = QPushButton("Upload CSV")
        self.upload_btn.setCursor(Qt.PointingHandCursor)
        self.upload_btn.clicked.connect(self.upload_file)

        self.report_btn = QPushButton("Download PDF")
        self.report_btn.setCursor(Qt.PointingHandCursor)
        self.report_btn.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; border-radius: 4px; padding: 6px 12px;")
        self.report_btn.clicked.connect(self.download_report)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.upload_btn)
        header_layout.addWidget(self.report_btn)

        layout.addWidget(header_container)

        stats = QHBoxLayout()
        stats.setSpacing(5)
        self.stats = {}
        for key in ["Total Count", "Avg Flow", "Avg Pressure", "Avg Temp"]:
            lbl = QLabel(f"{key}\n-")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedHeight(60)
            lbl.setStyleSheet("background:#1e293b; padding:4px; border-radius:6px; font-weight:bold; font-size: 11px;")
            self.stats[key] = lbl
            stats.addWidget(lbl)

        layout.addLayout(stats)

        self.figure = Figure(facecolor="#1e293b", constrained_layout=True)
        self.figure.set_constrained_layout_pads(w_pad=0.02, h_pad=0.02, wspace=0.05, hspace=0.05)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.dashboard_tab.setLayout(layout)

        self.canvas.draw()

    def setup_history(self):
        layout = QVBoxLayout()

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Filename", "Count", "Avg Flow"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.history_tab.setLayout(layout)

    def upload_file(self):
        if self.upload_worker and self.upload_worker.isRunning():
            return

        fname, _ = QFileDialog.getOpenFileName(
            self, "Select CSV", "", "CSV Files (*.csv)",
            options=QFileDialog.DontUseNativeDialog
        )
        if not fname:
            return

        self.upload_btn.setDisabled(True)
        self.upload_btn.setEnabled(False)
        self.tabs.setEnabled(False)

        self.upload_worker = UploadWorker(fname)
        self.upload_worker.finished.connect(self.upload_success)
        self.upload_worker.error.connect(self.upload_error)
        self.upload_worker.start()

    def upload_success(self, data):
        self.update_dashboard(data)
        QMessageBox.information(self, "Success", "File uploaded successfully!")
        self.upload_btn.setEnabled(True)
        self.tabs.setEnabled(True)
        self.load_history()

    def upload_error(self, msg):
        self.upload_btn.setDisabled(False)
        self.upload_btn.setEnabled(True)
        self.tabs.setEnabled(True)
        QMessageBox.critical(self, "Error", msg)

    def download_report(self):
        if self.report_worker and self.report_worker.isRunning():
            return

        self.report_worker = ReportWorker()
        self.report_worker.finished.connect(self.save_report)
        self.report_worker.error.connect(self.upload_error)
        self.report_worker.start()

    def save_report(self, content):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", "report.pdf", "PDF Files (*.pdf)",
            options=QFileDialog.DontUseNativeDialog
        )
        if path:
            try:
                with open(path, "wb") as f:
                    f.write(content)
                QMessageBox.information(self, "Success", "Report downloaded")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Could not save file.\nError: {e}\n\nMake sure the file is not open in another program!")

    def update_dashboard(self, data):
        summary = data.get("summary", {})
        rows = data.get("data", [])

        self.stats["Total Count"].setText(f"Total Count\n{summary.get('total_count', 0)}")
        self.stats["Avg Flow"].setText(f"Avg Flow\n{summary.get('avg_flowrate', 0):.2f}")
        self.stats["Avg Pressure"].setText(f"Avg Pressure\n{summary.get('avg_pressure', 0):.2f}")
        self.stats["Avg Temp"].setText(f"Avg Temp\n{summary.get('avg_temperature', 0):.2f}")

        self.figure.clear()
        
        if not rows:
            self.canvas.draw()
            return

        df = pd.DataFrame(rows)

        def get_col(df, candidates):
            for col in df.columns:
                if col.lower() in [c.lower() for c in candidates]:
                    return col
            return None

        flow_col = get_col(df, ['Flowrate', 'Flow Rate', 'Flow_Rate'])
        press_col = get_col(df, ['Pressure'])
        temp_col = get_col(df, ['Temperature', 'Temp'])
        type_col = get_col(df, ['Type', 'EquipmentType'])
        
        gs = self.figure.add_gridspec(3, 2, height_ratios=[1.2, 1, 1.5], hspace=0.2, wspace=0.1)
        
        ax1 = self.figure.add_subplot(gs[0, :])
        self.style_axis(ax1, "Parameter Trends")
        
        if flow_col:
            line1, = ax1.plot(df.index, df[flow_col], color='#3b82f6', label='Flow Rate', linewidth=2.5)
            ax1.set_ylabel('Flow Rate', color='#3b82f6', fontsize=10)
            ax1.tick_params(axis='y', labelcolor='#3b82f6')
            
        if press_col:
            ax1_twin = ax1.twinx()
            line2, = ax1_twin.plot(df.index, df[press_col], color='#ef4444', label='Pressure', linewidth=2.5)
            ax1_twin.set_ylabel('Pressure', color='#ef4444', fontsize=10)
            ax1_twin.tick_params(axis='y', labelcolor='#ef4444')
            ax1_twin.spines['bottom'].set_color('#334155')
            ax1_twin.spines['top'].set_color('#334155') 
            ax1_twin.spines['left'].set_color('#334155')
            ax1_twin.spines['right'].set_color('#334155')
            
        lines = []
        labels = []
        if flow_col: lines.append(line1); labels.append(line1.get_label())
        if press_col: lines.append(line2); labels.append(line2.get_label())
        if lines:
            ax1.legend(lines, labels, facecolor='#1e293b', edgecolor='#334155', labelcolor='#cbd5e1', 
                      loc='upper left', bbox_to_anchor=(1.15, 1), borderaxespad=0)
        
        ax2 = self.figure.add_subplot(gs[1, 0])
        self.style_axis(ax2, "Avg Flow by Type")
        
        if type_col and flow_col:
            bar_data = df.groupby(type_col)[flow_col].mean()
            colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899']
            ax2.bar(bar_data.index, bar_data.values, color=colors[:len(bar_data)])
            ax2.tick_params(axis='x', rotation=20, labelsize=9)

        ax3 = self.figure.add_subplot(gs[1, 1])
        self.style_axis(ax3, "Flow vs Pressure")
        ax3.set_xlabel('Flow Rate', color='#cbd5e1', fontsize=10)
        ax3.set_ylabel('Pressure', color='#cbd5e1', fontsize=10)
        
        if flow_col and press_col:
            if type_col:
                groups = df.groupby(type_col)
                for i, (name, group) in enumerate(groups):
                    ax3.scatter(group[flow_col], group[press_col], label=name, alpha=0.75, s=45)
                ax3.legend(facecolor='#1e293b', edgecolor='#334155', labelcolor='#cbd5e1', fontsize=8, 
                          bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
            else:
                ax3.scatter(df[flow_col], df[press_col], color='#10b981', alpha=0.7, s=45)

        ax4 = self.figure.add_subplot(gs[2, 0])
        self.style_axis(ax4, "Temp Variability")
        
        if type_col and temp_col:
            types = df[type_col].unique()
            type_map = {t: i for i, t in enumerate(types)}
            x_vals = df[type_col].map(type_map)
            
            import numpy as np
            jitter = np.random.uniform(-0.15, 0.15, size=len(x_vals))
            
            ax4.scatter(x_vals + jitter, df[temp_col], color='#f59e0b', alpha=0.6, s=40)
            ax4.set_xticks(range(len(types)))
            ax4.set_xticklabels(types, rotation=20, fontsize=9)

        self.pie_ax = self.figure.add_subplot(gs[2, 1])
        self.pie_ax.set_facecolor("#1e293b")
        self.pie_ax.set_title("Equipment Distribution", color="#f1f5f9", fontsize=11, pad=5)
        
        dist = summary.get('equipment_distribution', {})
        if dist:
            labels = list(dist.keys())
            values = list(dist.values())
            total = sum(values)
            pie_colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', 
                          '#ec4899', '#06b6d4', '#84cc16', '#6366f1', '#14b8a6']
            
            def make_autopct(values):
                def my_autopct(pct):
                    total = sum(values)
                    val = int(round(pct*total/100.0))
                    return '{v:d}'.format(v=val)
                return my_autopct

            wedges, texts, autotexts = self.pie_ax.pie(values, labels=None, autopct=make_autopct(values), 
                                              colors=pie_colors[:len(values)], 
                                              textprops=dict(color="white"))
            for text in texts:
                text.set_color("#cbd5e1")
                text.set_fontsize(9)
            
            self.pie_ax.legend(wedges, labels, title="Equipment", loc="center left", 
                              bbox_to_anchor=(1, 0, 0.5, 1), 
                              facecolor='#1e293b', edgecolor='#334155', labelcolor='#cbd5e1', fontsize=9)

        self.canvas.draw()
        
    def style_axis(self, ax, title):
        ax.set_facecolor('#1e293b')
        ax.set_title(title, color='#f1f5f9', fontsize=11, pad=8)
        ax.tick_params(colors='#94a3b8', labelsize=9)
        for spine in ax.spines.values():
            spine.set_color('#334155')


    def load_history(self):
        if self.history_worker and self.history_worker.isRunning():
            return

        self.history_worker = HistoryWorker()
        self.history_worker.finished.connect(self.update_history)
        self.history_worker.error.connect(self.upload_error)
        self.history_worker.start()


    def update_history(self, history):
        if not history:
            return
        
        self.table.setRowCount(len(history))
        for i, row in enumerate(history):
            items = [
                QTableWidgetItem(str(row.get("upload_date", ""))),
                QTableWidgetItem(str(row.get("filename", ""))),
                QTableWidgetItem(str(row.get("total_count", ""))),
                QTableWidgetItem(str(row.get("avg_flowrate", "")))
            ]
            
            for col, item in enumerate(items):
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.table.setItem(i, col, item)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
