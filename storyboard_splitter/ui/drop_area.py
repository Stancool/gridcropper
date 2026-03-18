from PyQt6.QtWidgets import QLabel, QFileDialog
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent


class DropArea(QLabel):
    file_dropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 200)
        self.setText("將分鏡圖拖放到這裡\n或點擊選擇檔案")
        self.setStyleSheet("""
            DropArea {
                border: 2px dashed #aaa;
                border-radius: 12px;
                background: #fafafa;
                font-size: 16px;
                color: #888;
                padding: 40px;
            }
            DropArea:hover {
                border-color: #6366f1;
                background: #f0f0ff;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp')):
                self.file_dropped.emit(path)

    def mousePressEvent(self, event):
        path, _ = QFileDialog.getOpenFileName(
            self, "選擇分鏡圖片", "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if path:
            self.file_dropped.emit(path)
