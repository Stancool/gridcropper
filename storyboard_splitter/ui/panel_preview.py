import cv2
from PyQt6.QtWidgets import QWidget, QGridLayout, QCheckBox, QLabel, QVBoxLayout, QScrollArea
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from core.detector import DetectedPanel


class PanelPreview(QScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self._container = QWidget()
        self._grid = QGridLayout(self._container)
        self._grid.setSpacing(8)
        self.setWidget(self._container)
        self.checkboxes: list[tuple[QCheckBox, DetectedPanel]] = []

    def load_panels(self, image_path: str, panels: list[DetectedPanel]):
        self._clear()

        img = cv2.imread(image_path)
        if img is None:
            return

        content_panels = [p for p in panels if not p.is_title]

        # Determine column count from the data
        if content_panels:
            med_h = max(p.height for p in content_panels) * 0.3
            rows_grouped: list[list[DetectedPanel]] = []
            sorted_panels = sorted(content_panels, key=lambda p: (p.y, p.x))
            current_row = [sorted_panels[0]]
            for p in sorted_panels[1:]:
                if abs(p.y - current_row[0].y) < med_h:
                    current_row.append(p)
                else:
                    rows_grouped.append(current_row)
                    current_row = [p]
            rows_grouped.append(current_row)
            columns = max(len(r) for r in rows_grouped)
        else:
            columns = 6

        for i, panel in enumerate(content_panels):
            row, col = divmod(i, columns)

            cropped = img[panel.y:panel.y + panel.height, panel.x:panel.x + panel.width]
            thumb = cv2.resize(cropped, (160, 120))
            thumb_rgb = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)

            h, w, ch = thumb_rgb.shape
            bytes_per_line = ch * w
            qimg = QImage(thumb_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)

            cell_widget = QWidget()
            cell_layout = QVBoxLayout(cell_widget)
            cell_layout.setContentsMargins(4, 4, 4, 4)

            img_label = QLabel()
            img_label.setPixmap(pixmap)
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_layout.addWidget(img_label)

            checkbox = QCheckBox(f"Shot {panel.index:03d}")
            checkbox.setChecked(True)
            cell_layout.addWidget(checkbox, alignment=Qt.AlignmentFlag.AlignCenter)

            self._grid.addWidget(cell_widget, row, col)
            self.checkboxes.append((checkbox, panel))

    def get_selected_panels(self) -> list[DetectedPanel]:
        return [panel for cb, panel in self.checkboxes if cb.isChecked()]

    def select_all(self):
        for cb, _ in self.checkboxes:
            cb.setChecked(True)

    def deselect_all(self):
        for cb, _ in self.checkboxes:
            cb.setChecked(False)

    def _clear(self):
        self.checkboxes.clear()
        while self._grid.count():
            child = self._grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
