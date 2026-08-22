# services/yolo_service.py
from ultralytics import YOLOWorld
from config import settings
from loguru import logger
import numpy as np
from typing import List


class YOLOService:
    def __init__(self):
        model_path = settings.YOLO_MODEL

        if not model_path.endswith(".pt"):
            model_path += ".pt"

        self.model = YOLOWorld(model_path)
        self.model.set_classes(settings.YOLO_EQUIPMENT_CLASSES)
        logger.info(f"✅ YOLO-World loaded: {settings.YOLO_MODEL}")

    def is_ready(self):
        return self.model is not None

    def detect_equipments(self, frames: List[np.ndarray]) -> List:
        """Détecte équipements avec YOLO-World, retourne liste Results"""
        all_results = []

        for i, frame in enumerate(frames):
            try:
                results = self.model(
                    frame,
                    conf=settings.YOLO_CONFIDENCE,
                    iou=settings.YOLO_IOU_THRESHOLD,
                    verbose=False
                )
                # results est une liste, on prend le premier élément
                all_results.append(results[0])

            except Exception as e:
                logger.warning(f"YOLO error on frame {i}: {e}")
                all_results.append(None)

        logger.info(f"✅ YOLO processed {len(frames)} frames")
        return all_results
