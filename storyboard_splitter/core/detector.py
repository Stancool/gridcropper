import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class DetectedPanel:
    index: int
    x: int
    y: int
    width: int
    height: int
    is_title: bool = False


class StoryboardDetector:

    def __init__(self):
        self.panels: list[DetectedPanel] = []

    def detect(self, image_path: str) -> list[DetectedPanel]:
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Cannot load image: {image_path}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        binary = self._binarize(gray)
        grid_mask = self._extract_grid_lines(binary, w, h)
        candidates = self._find_panel_contours(grid_mask, w, h)

        if not candidates:
            raise ValueError("No panels detected in the image.")

        panels = self._regularize_grid(candidates, w, h)
        panels = self._filter_title(panels)
        panels = self._sort_reading_order(panels)
        self.panels = panels
        return panels

    def _binarize(self, gray: np.ndarray) -> np.ndarray:
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        binary = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 15, 4
        )
        return binary

    def _extract_grid_lines(self, binary: np.ndarray, w: int, h: int) -> np.ndarray:
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(w // 15, 1), 1))
        h_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel, iterations=2)

        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(h // 15, 1)))
        v_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel, iterations=2)

        combined = cv2.add(h_lines, v_lines)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        grid_mask = cv2.dilate(combined, kernel, iterations=2)
        return grid_mask

    def _find_panel_contours(self, grid_mask: np.ndarray, w: int, h: int) -> list[tuple]:
        contours, _ = cv2.findContours(
            grid_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        total_area = w * h
        min_area = total_area * 0.005
        max_area = total_area * 0.25

        candidates = []
        for cnt in contours:
            x, y, cw, ch = cv2.boundingRect(cnt)
            area = cw * ch
            contour_area = cv2.contourArea(cnt)

            if area < min_area or area > max_area:
                continue
            if contour_area / area < 0.7:
                continue

            aspect = cw / ch if ch > 0 else 0
            if aspect < 0.3 or aspect > 3.5:
                continue

            candidates.append((x, y, cw, ch))

        return candidates

    def _regularize_grid(self, candidates: list[tuple], img_w: int, img_h: int) -> list[DetectedPanel]:
        if not candidates:
            return []

        y_centers = sorted(set(y + h // 2 for _, y, _, h in candidates))
        rows = self._cluster_values(y_centers, img_h * 0.04)

        x_centers = sorted(set(x + w // 2 for x, _, w, _ in candidates))
        cols = self._cluster_values(x_centers, img_w * 0.04)

        widths = [w for _, _, w, _ in candidates]
        heights = [h for _, _, _, h in candidates]
        med_w = int(np.median(widths))
        med_h = int(np.median(heights))

        panels = []
        for row_y in rows:
            for col_x in cols:
                best = None
                best_dist = float('inf')
                for (cx, cy, cw, ch) in candidates:
                    dist = abs((cx + cw // 2) - col_x) + abs((cy + ch // 2) - row_y)
                    if dist < best_dist:
                        best_dist = dist
                        best = (cx, cy, cw, ch)

                tolerance = (med_w + med_h) * 0.4
                if best and best_dist < tolerance:
                    panels.append(DetectedPanel(
                        index=0, x=best[0], y=best[1],
                        width=best[2], height=best[3]
                    ))

        return panels

    @staticmethod
    def _cluster_values(values: list[float], tolerance: float) -> list[float]:
        if not values:
            return []
        clusters = [[values[0]]]
        for v in values[1:]:
            if v - clusters[-1][-1] < tolerance:
                clusters[-1].append(v)
            else:
                clusters.append([v])
        return [sum(c) / len(c) for c in clusters]

    def _filter_title(self, panels: list[DetectedPanel]) -> list[DetectedPanel]:
        if not panels:
            return panels

        med_w = float(np.median([p.width for p in panels]))
        med_h = float(np.median([p.height for p in panels]))

        for p in panels:
            if p.width > med_w * 1.8:
                p.is_title = True
            if p.height < med_h * 0.4 or p.height > med_h * 2.0:
                p.is_title = True
            panel_aspect = p.width / p.height if p.height > 0 else 0
            med_aspect = med_w / med_h if med_h > 0 else 1
            if panel_aspect > med_aspect * 2.0:
                p.is_title = True

        return panels

    def _sort_reading_order(self, panels: list[DetectedPanel]) -> list[DetectedPanel]:
        content_panels = [p for p in panels if not p.is_title]
        if not content_panels:
            return content_panels

        med_h = float(np.median([p.height for p in content_panels]))

        content_panels.sort(key=lambda p: (p.y, p.x))
        rows: list[list[DetectedPanel]] = []
        current_row = [content_panels[0]]
        for p in content_panels[1:]:
            if abs(p.y - current_row[0].y) < med_h * 0.3:
                current_row.append(p)
            else:
                rows.append(sorted(current_row, key=lambda p: p.x))
                current_row = [p]
        rows.append(sorted(current_row, key=lambda p: p.x))

        idx = 1
        result = []
        for row in rows:
            for p in row:
                p.index = idx
                idx += 1
                result.append(p)

        return result
