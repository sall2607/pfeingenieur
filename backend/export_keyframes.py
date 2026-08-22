"""
Export des 60 keyframes pour annotation manuelle
PFE Oulimata SALL — ENICarthage 2026
"""
import cv2
import numpy as np
from pathlib import Path
from services.video_processor import VideoProcessor

# Configuration
VIDEOS = {
    "V1": "test_videos/ma_video.mp4",
    "V2": "test_videos/ma_video1.mp4",
    "V3": "test_videos/ma_video2.mp4",
    "V4": "test_videos/ma_video3.mp4",
}
OUTPUT_DIR = Path("annotations/images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Labels dir
LABELS_DIR = Path("annotations/labels")
LABELS_DIR.mkdir(parents=True, exist_ok=True)

# Classes
CLASSES = [
    "air_conditioner",      # 0
    "laptop",               # 1
    "computer_monitor",     # 2
    "network_switch",       # 3
    "television",           # 4
    "refrigerator",         # 5
    "microwave",            # 6
]

# Sauvegarder classes.txt
with open("annotations/classes.txt", "w") as f:
    for c in CLASSES:
        f.write(c + "\n")

vp = VideoProcessor()

total = 0
for video_key, video_path in VIDEOS.items():
    if not Path(video_path).exists():
        print(f"❌ Vidéo manquante : {video_path}")
        continue

    print(f"\n📹 Traitement {video_key} : {video_path}")
    keyframes = vp.extract_keyframes(
        video_path, max_keyframes=15
    )
    print(f"   {len(keyframes)} keyframes extraites")

    for i, frame in enumerate(keyframes, 1):
        name = f"{video_key}_{i:03d}"
        img_path = OUTPUT_DIR / f"{name}.jpg"
        lbl_path = LABELS_DIR / f"{name}.txt"

        # Sauvegarder l'image
        cv2.imwrite(str(img_path), frame)

        # Créer fichier label vide
        lbl_path.touch()

        total += 1
        print(f"   ✅ {name}.jpg sauvegardé")

print(f"\n✅ Total : {total} keyframes exportées")
print(f"   Images : annotations/images/")
print(f"   Labels : annotations/labels/")
print(f"   Classes: annotations/classes.txt")
print(f"\n👉 Ouvrez LabelImg et annotez les images !")