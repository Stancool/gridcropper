import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QStackedWidget
)
from PyQt6.QtCore import Qt
from ui.drop_area import DropArea
from ui.panel_preview import PanelPreview
from core.detector import StoryboardDetector
from core.exporter import PanelExporter


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Storyboard Splitter")
        self.setMinimumSize(900, 600)

        self.detector = StoryboardDetector()
        self.exporter = PanelExporter()
        self.current_image_path = None

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        self.stack = QStackedWidget()

        # Page 0: Drop area
        self.drop_area = DropArea()
        self.drop_area.file_dropped.connect(self._on_image_loaded)
        self.stack.addWidget(self.drop_area)

        # Page 1: Results
        results_page = QWidget()
        results_layout = QVBoxLayout(results_page)

        # Info bar
        info_bar = QHBoxLayout()
        self.info_label = QLabel()
        self.btn_reload = QPushButton("載入其他圖片")
        self.btn_reload.clicked.connect(self._reset)
        info_bar.addWidget(self.info_label)
        info_bar.addStretch()
        info_bar.addWidget(self.btn_reload)
        results_layout.addLayout(info_bar)

        # Panel preview
        self.panel_preview = PanelPreview()
        results_layout.addWidget(self.panel_preview, stretch=1)

        # Bottom bar
        bottom_bar = QHBoxLayout()

        self.btn_select_all = QPushButton("全選")
        self.btn_select_all.clicked.connect(self.panel_preview.select_all)
        self.btn_deselect_all = QPushButton("取消全選")
        self.btn_deselect_all.clicked.connect(self.panel_preview.deselect_all)
        bottom_bar.addWidget(self.btn_select_all)
        bottom_bar.addWidget(self.btn_deselect_all)
        bottom_bar.addStretch()

        self.btn_export = QPushButton("匯出選取的分鏡")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background: #6366f1; color: white;
                padding: 10px 24px; border-radius: 8px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: #4f46e5; }
        """)
        self.btn_export.clicked.connect(self._export)
        bottom_bar.addWidget(self.btn_export)
        results_layout.addLayout(bottom_bar)

        self.stack.addWidget(results_page)
        main_layout.addWidget(self.stack)

    def _on_image_loaded(self, path: str):
        self.current_image_path = path
        try:
            panels = self.detector.detect(path)
            content_count = sum(1 for p in panels if not p.is_title)
            self.info_label.setText(
                f"偵測到 {content_count} 個分鏡 — {os.path.basename(path)}"
            )
            self.panel_preview.load_panels(path, panels)
            self.stack.setCurrentIndex(1)
        except Exception as e:
            QMessageBox.warning(self, "偵測失敗", str(e))

    def _export(self):
        selected = self.panel_preview.get_selected_panels()
        if not selected:
            QMessageBox.information(self, "未選取", "請至少勾選一個分鏡。")
            return

        output_dir = QFileDialog.getExistingDirectory(self, "選擇輸出資料夾")
        if not output_dir:
            return

        try:
            saved = self.exporter.export(self.current_image_path, selected, output_dir)
            QMessageBox.information(
                self, "匯出完成",
                f"已儲存 {len(saved)} 張分鏡到：\n{output_dir}"
            )
        except Exception as e:
            QMessageBox.warning(self, "匯出失敗", str(e))

    def _reset(self):
        self.current_image_path = None
        self.stack.setCurrentIndex(0)
