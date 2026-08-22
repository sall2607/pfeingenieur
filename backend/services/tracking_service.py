# services/tracking_service.py
import supervision as sv
import numpy as np
import cv2
import os
from config import settings
from loguru import logger
from typing import List, Dict


class TrackingService:
    def __init__(self):
        self.tracker = sv.ByteTrack()
        logger.info("✅ ByteTrack initialized")

    def track_and_get_best_shots(
        self, frames: List[np.ndarray], detections_list: List
    ) -> List[Dict]:
        """Track objets entre frames et selectionne le meilleur crop par objet"""

        # ── DIAGNOSTIC ───────────────────────────────────────
        total_boxes = 0
        for results in detections_list:
            if results is not None and results.boxes is not None:
                total_boxes += len(results.boxes)
        logger.info(
            f"DIAGNOSTIC: {total_boxes} boxes total "
            f"sur {len(frames)} frames"
        )

        # ── Réinitialiser le tracker à chaque vidéo ──────────
        # Utiliser self.tracker (initialisé dans __init__)
        # sans paramètres supplémentaires
        try:
            self.tracker.reset()
        except Exception:
            # Certaines versions n'ont pas reset()
            # → recréer le tracker sans paramètres
            self.tracker = sv.ByteTrack()

        track_best = {}

        for frame, results in zip(frames, detections_list):
            if results is None:
                continue
            if not hasattr(results, "boxes") or results.boxes is None:
                continue
            if len(results.boxes) == 0:
                continue

            try:
                boxes     = results.boxes.xyxy.cpu().numpy()
                scores    = results.boxes.conf.cpu().numpy()
                class_ids = results.boxes.cls.cpu().numpy().astype(int)

                logger.debug(
                    f"  Frame: {len(boxes)} boxes, "
                    f"conf=[{scores.min():.2f}-{scores.max():.2f}]"
                )

                sv_dets = sv.Detections(
                    xyxy=boxes,
                    confidence=scores,
                    class_id=class_ids
                )

                # ── Utiliser self.tracker (pas un tracker local) ──
                tracked = self.tracker.update_with_detections(sv_dets)

                if tracked.tracker_id is None:
                    continue

                logger.debug(f"  Tracked: {len(tracked.tracker_id)} objects")

                for i, track_id in enumerate(tracked.tracker_id):
                    if track_id is None:
                        continue

                    bbox = tracked.xyxy[i]
                    area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])

                    if (track_id not in track_best
                            or area > track_best[track_id]["area"]):
                        track_best[track_id] = {
                            "frame": frame.copy(),
                            "bbox":  bbox,
                            "area":  area
                        }

            except Exception as e:
                logger.warning(f"Tracking error on frame: {e}")
                continue

        # ── Extraire les crops uniques ────────────────────────
        os.makedirs("crops", exist_ok=True)
        unique_crops = []

        for track_id, data in track_best.items():
            try:
                x1, y1, x2, y2 = map(int, data["bbox"])
                h, w = data["frame"].shape[:2]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)

                if x2 <= x1 or y2 <= y1:
                    continue

                crop      = data["frame"][y1:y2, x1:x2]
                crop_path = f"crops/track_{track_id}.jpg"
                cv2.imwrite(crop_path, crop)

                unique_crops.append({
                    "path":       crop_path,
                    "bbox":       [x1, y1, x2, y2],
                    "confidence": 1.0,
                    "track_id":   int(track_id)
                })

                logger.debug(f"  Crop saved: track_{track_id} area={area:.0f}")

            except Exception as e:
                logger.warning(f"Crop error for track {track_id}: {e}")
                continue

        logger.info(f"ByteTrack: {len(unique_crops)} unique crops")
        return unique_crops
