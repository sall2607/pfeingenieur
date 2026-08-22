"""Évalue le service YOLO-World du backend sur les annotations LabelImg."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

from services.yolo_service import YOLOService


CLASSES = [
    "air_conditioner",
    "laptop",
    "computer_monitor",
    "network_switch",
    "television",
    "refrigerator",
    "microwave",
]

ALIASES = {
    "air conditioner": 0,
    "climatiseur": 0,
    "laptop": 1,
    "computer": 1,
    "ordinateur": 1,
    "computer monitor": 2,
    "monitor": 2,
    "screen": 2,
    "network switch": 3,
    "switch": 3,
    "television": 4,
    "tv": 4,
    "refrigerator": 5,
    "réfrigérateur": 5,
    "fridge": 5,
    "freezer": 5,
    "microwave": 6,
    "microwave oven": 6,
}


def iou(first, second):
    x1, y1 = max(first[0], second[0]), max(first[1], second[1])
    x2, y2 = min(first[2], second[2]), min(first[3], second[3])
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area_first = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
    area_second = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
    union = area_first + area_second - intersection
    return intersection / union if union else 0.0


def average_precision(recalls, precisions):
    recalls = np.concatenate(([0.0], recalls, [1.0]))
    precisions = np.concatenate(([0.0], precisions, [0.0]))
    for index in range(len(precisions) - 1, 0, -1):
        precisions[index - 1] = max(precisions[index - 1], precisions[index])
    indices = np.where(recalls[1:] != recalls[:-1])[0]
    return float(np.sum((recalls[indices + 1] - recalls[indices]) * precisions[indices + 1]))


def load_dataset(images_dir, labels_dir):
    images = sorted(images_dir.glob("*.jpg"))
    ground_truths = []
    negative_images = []
    for image_path in images:
        image = cv2.imread(str(image_path))
        if image is None:
            raise RuntimeError(f"Image illisible : {image_path}")
        height, width = image.shape[:2]
        label_path = labels_dir / f"{image_path.stem}.txt"
        if not label_path.exists():
            raise RuntimeError(f"Annotation manquante : {label_path}")
        lines = [line.strip() for line in label_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        if not lines:
            negative_images.append(image_path.name)
        for line in lines:
            class_id, center_x, center_y, box_width, box_height = map(float, line.split())
            center_x, box_width = center_x * width, box_width * width
            center_y, box_height = center_y * height, box_height * height
            ground_truths.append({
                "image": image_path.name,
                "class_id": int(class_id),
                "box": (
                    center_x - box_width / 2,
                    center_y - box_height / 2,
                    center_x + box_width / 2,
                    center_y + box_height / 2,
                ),
            })
    return images, ground_truths, negative_images


def run_detector(images):
    detector = YOLOService()
    predictions = []
    ignored = Counter()
    for number, image_path in enumerate(images, 1):
        image = cv2.imread(str(image_path))
        result = detector.detect_equipments([image])[0]
        retained = 0
        if result is not None and result.boxes is not None:
            boxes = result.boxes.xyxy.cpu().numpy()
            scores = result.boxes.conf.cpu().numpy()
            class_ids = result.boxes.cls.cpu().numpy().astype(int)
            for box, score, raw_id in zip(boxes, scores, class_ids):
                raw_name = str(result.names[int(raw_id)]).strip().lower().replace("_", " ")
                class_id = ALIASES.get(raw_name)
                if class_id is None:
                    ignored[raw_name] += 1
                    continue
                predictions.append({
                    "image": image_path.name,
                    "class_id": class_id,
                    "raw_class": raw_name,
                    "confidence": float(score),
                    "box": tuple(map(float, box)),
                })
                retained += 1
        print(f"[{number:02d}/{len(images)}] {image_path.name}: {retained} prédiction(s)")
    return predictions, ignored


def evaluate_class(class_id, ground_truths, predictions, threshold=0.5):
    class_gt = [item for item in ground_truths if item["class_id"] == class_id]
    class_predictions = sorted(
        [item for item in predictions if item["class_id"] == class_id],
        key=lambda item: item["confidence"],
        reverse=True,
    )
    grouped = defaultdict(list)
    for item in class_gt:
        grouped[item["image"]].append(item)
    matched = {name: [False] * len(items) for name, items in grouped.items()}
    true_positives, false_positives = [], []
    for prediction in class_predictions:
        candidates = grouped.get(prediction["image"], [])
        best_iou, best_index = 0.0, -1
        for index, candidate in enumerate(candidates):
            if matched[prediction["image"]][index]:
                continue
            score = iou(prediction["box"], candidate["box"])
            if score > best_iou:
                best_iou, best_index = score, index
        if best_index >= 0 and best_iou >= threshold:
            matched[prediction["image"]][best_index] = True
            true_positives.append(1)
            false_positives.append(0)
        else:
            true_positives.append(0)
            false_positives.append(1)
    cumulative_tp = np.cumsum(true_positives)
    cumulative_fp = np.cumsum(false_positives)
    gt_count = len(class_gt)
    tp = int(cumulative_tp[-1]) if len(cumulative_tp) else 0
    fp = int(cumulative_fp[-1]) if len(cumulative_fp) else 0
    fn = gt_count - tp
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / gt_count if gt_count else None
    f1 = 2 * precision * recall / (precision + recall) if recall is not None and precision + recall else 0.0
    if gt_count:
        recalls = cumulative_tp / gt_count
        precisions = cumulative_tp / np.maximum(cumulative_tp + cumulative_fp, 1e-12)
        ap50 = average_precision(recalls, precisions)
    else:
        ap50 = None
    return {
        "class_id": class_id,
        "class_name": CLASSES[class_id],
        "ground_truths": gt_count,
        "predictions": len(class_predictions),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "ap50": ap50,
    }


def main():
    images_dir = Path("annotations/images")
    labels_dir = Path("annotations/labels")
    output_dir = Path("evaluation_results")
    output_dir.mkdir(exist_ok=True)
    images, ground_truths, negatives = load_dataset(images_dir, labels_dir)
    print(f"Dataset : {len(images)} images, {len(ground_truths)} boîtes, {len(negatives)} négatives")
    predictions, ignored = run_detector(images)
    rows = [evaluate_class(class_id, ground_truths, predictions) for class_id in range(len(CLASSES))]
    present = [row for row in rows if row["ground_truths"]]
    tp = sum(row["true_positives"] for row in rows)
    fp = sum(row["false_positives"] for row in rows)
    fn = sum(row["false_negatives"] for row in rows)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    map50 = float(np.mean([row["ap50"] for row in present]))
    summary = {
        "images": len(images),
        "negative_images": len(negatives),
        "ground_truth_boxes": len(ground_truths),
        "target_predictions": len(predictions),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "micro_precision": precision,
        "micro_recall": recall,
        "micro_f1": f1,
        "map50_present_classes": map50,
        "classes_without_ground_truth": [row["class_name"] for row in rows if not row["ground_truths"]],
        "ignored_prediction_classes": dict(ignored),
    }
    (output_dir / "metrics.json").write_text(
        json.dumps({"summary": summary, "per_class": rows}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    with (output_dir / "per_class_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    with (output_dir / "predictions.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["image", "class_id", "class_name", "raw_class", "confidence", "x1", "y1", "x2", "y2"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in predictions:
            writer.writerow({
                "image": item["image"],
                "class_id": item["class_id"],
                "class_name": CLASSES[item["class_id"]],
                "raw_class": item["raw_class"],
                "confidence": item["confidence"],
                "x1": item["box"][0], "y1": item["box"][1],
                "x2": item["box"][2], "y2": item["box"][3],
            })
    print("\nClasse                 GT Pred TP FP FN Précision Rappel F1 AP50")
    for row in rows:
        percent = lambda value: "N/A" if value is None else f"{100 * value:.1f}%"
        print(f"{row['class_name']:<21} {row['ground_truths']:>2} {row['predictions']:>4} "
              f"{row['true_positives']:>2} {row['false_positives']:>2} {row['false_negatives']:>2} "
              f"{percent(row['precision']):>9} {percent(row['recall']):>6} "
              f"{percent(row['f1']):>6} {percent(row['ap50']):>6}")
    print(f"\nPrécision micro : {100 * precision:.1f}%")
    print(f"Rappel micro    : {100 * recall:.1f}%")
    print(f"F1 micro        : {100 * f1:.1f}%")
    print(f"mAP@50          : {100 * map50:.1f}%")
    print("Résultats enregistrés dans evaluation_results")


if __name__ == "__main__":
    main()