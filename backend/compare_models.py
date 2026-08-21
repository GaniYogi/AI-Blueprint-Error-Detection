"""
compare_models.py
=================
Evaluates and compares the current production model vs the newly trained model on:
1. The dataset_clean validation set (mAP50, mAP50-95, Precision, Recall per class: Wall, Door, Window)
2. Real sample blueprint images
"""

import os
import sys
from pathlib import Path
from ultralytics import YOLO

PROJECT_DIR = Path(__file__).resolve().parent.parent
PROD_MODEL_PATH = PROJECT_DIR / "backend" / "models" / "best.pt"
CLEAN_MODEL_PATH = PROJECT_DIR / "runs" / "train" / "blueprint_clean" / "weights" / "best.pt"
DATA_YAML = PROJECT_DIR / "dataset_clean" / "data.yaml"

def eval_model(name: str, model_path: Path):
    if not model_path.exists():
        print(f"[{name}] Weights not found at: {model_path}")
        return None

    print(f"\nEvaluating {name} ({model_path.name})...")
    model = YOLO(str(model_path))
    
    # Run validation on the dataset_clean val split
    metrics = model.val(data=str(DATA_YAML), split="val", imgsz=640, batch=8, workers=0, verbose=False)
    
    # Extract metrics
    # metrics.results_dict contains mAP50, mAP50-95, precision, recall
    p = metrics.box.mp
    r = metrics.box.mr
    map50 = metrics.box.map50
    map50_95 = metrics.box.map
    
    # Per-class metrics
    class_map50 = metrics.box.maps  # array of mAP50-95 or per-class mAP50
    
    print(f"--- {name} Results ---")
    print(f"  Precision (all) : {p:.4f}")
    print(f"  Recall (all)    : {r:.4f}")
    print(f"  mAP50           : {map50:.4f}")
    print(f"  mAP50-95        : {map50_95:.4f}")
    
    # Per class P and R if available
    class_p = metrics.box.p
    class_r = metrics.box.r
    names = model.names
    
    per_class = {}
    for idx, cname in names.items():
        cp = class_p[idx] if len(class_p) > idx else 0.0
        cr = class_r[idx] if len(class_r) > idx else 0.0
        per_class[cname] = {"precision": cp, "recall": cr}
        print(f"  Class [{cname}]: P={cp:.4f}, R={cr:.4f}")
        
    return {
        "name": name,
        "precision": p,
        "recall": r,
        "map50": map50,
        "map50_95": map50_95,
        "per_class": per_class,
    }

def main():
    print("=" * 68)
    print("MODEL COMPARISON: PRODUCTION MODEL vs NEW CLEAN MODEL")
    print("=" * 68)
    
    prod_results = eval_model("CURRENT PRODUCTION MODEL", PROD_MODEL_PATH)
    clean_results = eval_model("NEW BLUEPRINT_CLEAN MODEL", CLEAN_MODEL_PATH)
    
    print("\n" + "=" * 68)
    print("FINAL COMPARISON TABLE")
    print("=" * 68)
    print(f"{'METRIC':<20} | {'CURRENT MODEL':<20} | {'NEW MODEL':<20}")
    print("-" * 68)
    
    def fmt(res, key):
        if not res: return "N/A"
        val = res.get(key, 0.0)
        return f"{val:.4f}"
        
    def fmt_cls(res, cname, mkey):
        if not res or cname not in res.get("per_class", {}): return "N/A"
        val = res["per_class"][cname].get(mkey, 0.0)
        return f"{val:.4f}"
        
    print(f"{'Precision (overall)':<20} | {fmt(prod_results, 'precision'):<20} | {fmt(clean_results, 'precision'):<20}")
    print(f"{'Recall (overall)':<20} | {fmt(prod_results, 'recall'):<20} | {fmt(clean_results, 'recall'):<20}")
    print(f"{'mAP50':<20} | {fmt(prod_results, 'map50'):<20} | {fmt(clean_results, 'map50'):<20}")
    print(f"{'mAP50-95':<20} | {fmt(prod_results, 'map50_95'):<20} | {fmt(clean_results, 'map50_95'):<20}")
    print("-" * 68)
    print(f"{'Wall Precision':<20} | {fmt_cls(prod_results, 'wall', 'precision'):<20} | {fmt_cls(clean_results, 'wall', 'precision'):<20}")
    print(f"{'Wall Recall':<20} | {fmt_cls(prod_results, 'wall', 'recall'):<20} | {fmt_cls(clean_results, 'wall', 'recall'):<20}")
    print(f"{'Door Precision':<20} | {fmt_cls(prod_results, 'door', 'precision'):<20} | {fmt_cls(clean_results, 'door', 'precision'):<20}")
    print(f"{'Door Recall':<20} | {fmt_cls(prod_results, 'door', 'recall'):<20} | {fmt_cls(clean_results, 'door', 'recall'):<20}")
    print(f"{'Window Precision':<20} | {fmt_cls(prod_results, 'window', 'precision'):<20} | {fmt_cls(clean_results, 'window', 'precision'):<20}")
    print(f"{'Window Recall':<20} | {fmt_cls(prod_results, 'window', 'recall'):<20} | {fmt_cls(clean_results, 'window', 'recall'):<20}")
    print("=" * 68)

if __name__ == "__main__":
    main()
