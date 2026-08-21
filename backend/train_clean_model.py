"""
Train a new YOLO model on dataset_clean without touching production weights.
Outputs to: runs/train/blueprint_clean/
"""

import os
from pathlib import Path
import torch
from ultralytics import YOLO

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATASET_YAML = PROJECT_DIR / "dataset_clean" / "data.yaml"
RUNS_DIR = PROJECT_DIR / "runs" / "train"

def main():
    print("=" * 64)
    print("STARTING TRAINING ON dataset_clean")
    print(f"Data YAML: {DATASET_YAML}")
    print(f"Output:    {RUNS_DIR / 'blueprint_clean'}")
    print("=" * 64)

    # Initialize model with yolov8n.pt pretrained backbone
    model = YOLO("yolov8n.pt")

    results = model.train(
        data=str(DATASET_YAML),
        epochs=10,
        imgsz=640,
        batch=16,
        device="cpu",
        project=str(RUNS_DIR),
        name="blueprint_clean",
        exist_ok=True,
        patience=5,
        save=True,
        plots=True,
        workers=0,
        verbose=True,
    )

    print("\nTraining Complete!")
    print(f"Best model saved at: {RUNS_DIR / 'blueprint_clean' / 'weights' / 'best.pt'}")

if __name__ == "__main__":
    main()
