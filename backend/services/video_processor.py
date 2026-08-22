# services/video_processor.py
import cv2
import numpy as np
from typing import List
from loguru import logger
from config import settings

class VideoProcessor:
    def extract_keyframes(self, video_path: str, max_keyframes: int = 20) -> List[np.ndarray]:
        """Extrait keyframes d'une vidéo"""
        cap = cv2.VideoCapture(video_path)
        frames = []
        frame_indices = []
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Calculer netteté (Laplacian)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            if sharpness > settings.SHARPNESS_THRESHOLD:
                frames.append((frame, sharpness, frame_idx))
            
            frame_idx += 1
        
        cap.release()
        
        if not frames:
            logger.warning("No sharp frames found")
            return []
        
        # Trier par netteté
        frames.sort(key=lambda x: x[1], reverse=True)
        
        # Sélectionner top keyframes avec diversité temporelle
        selected = []
        for frame, sharpness, idx in frames:
            if len(selected) >= max_keyframes:
                break
            
            # Vérifier diversité temporelle
            if not selected or min([abs(idx - s[2]) for s in selected]) > 5:
                selected.append((frame, sharpness, idx))
        
        logger.info(f"Selected {len(selected)} keyframes from {frame_idx} total frames")
        
        return [f[0] for f in selected]
