import os
import cv2
from .detector import DetectedPanel


class PanelExporter:

    def export(self, image_path: str, panels: list[DetectedPanel],
               output_dir: str, prefix: str = "shot") -> list[str]:
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Cannot load: {image_path}")

        os.makedirs(output_dir, exist_ok=True)

        saved = []
        for panel in panels:
            if panel.is_title:
                continue

            cropped = img[
                panel.y: panel.y + panel.height,
                panel.x: panel.x + panel.width
            ]

            filename = f"{prefix}{panel.index:03d}.png"
            filepath = os.path.join(output_dir, filename)
            cv2.imwrite(filepath, cropped)
            saved.append(filepath)

        return saved
