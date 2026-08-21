"""
Visual verification script for dataset_clean.
Draws YOLO bounding boxes on sample blueprint images and saves them to dataset_clean/visual_checks/
Colors:
  - Green  (0, 255, 0)   : Wall (0)
  - Blue   (255, 0, 0)   : Door (1)
  - Yellow (0, 255, 255) : Window (2)
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

DATASET_DIR = Path(r"C:\Users\ganiy\OneDrive\Desktop\AI BluePrint error detection\dataset_clean")
OUT_DIR = DATASET_DIR / "visual_checks"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CLASS_COLORS = {
    0: ("#22c55e", "Wall"),    # Green
    1: ("#3b82f6", "Door"),    # Blue
    2: ("#eab308", "Window"),  # Yellow
}

def draw_yolo_labels(img_path: Path, lbl_path: Path, out_path: Path):
    if not img_path.exists() or not lbl_path.exists():
        return False
        
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    w_img, h_img = img.size
    
    lines = lbl_path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        parts = line.strip().split()
        if len(parts) != 5:
            continue
        cls_id = int(parts[0])
        cx, cy, nw, nh = [float(x) for x in parts[1:]]
        
        # Convert normalized to pixel coords
        xmin = (cx - nw / 2) * w_img
        ymin = (cy - nh / 2) * h_img
        xmax = (cx + nw / 2) * w_img
        ymax = (cy + nh / 2) * h_img
        
        color_hex, label_name = CLASS_COLORS.get(cls_id, ("#ffffff", f"Class {cls_id}"))
        
        # Draw box
        draw.rectangle([xmin, ymin, xmax, ymax], outline=color_hex, width=3)
        # Draw small label tag
        draw.rectangle([xmin, max(0, ymin - 16), xmin + len(label_name) * 8 + 6, ymin], fill=color_hex)
        draw.text((xmin + 3, max(0, ymin - 15)), label_name, fill="black")
        
    img.save(out_path)
    return True

def main():
    train_imgs = sorted((DATASET_DIR / "images" / "train").glob("*.png"))
    val_imgs = sorted((DATASET_DIR / "images" / "val").glob("*.png"))
    all_imgs = train_imgs + val_imgs
    
    samples_found = {
        "with_doors_and_windows": [],
        "with_fire_doors": [],
        "walls_and_windows_only": [],
        "doors_only": [],
    }
    
    for img_p in all_imgs:
        lbl_p = img_p.parent.parent.parent / "labels" / img_p.parent.name / f"{img_p.stem}.txt"
        if not lbl_p.exists():
            continue
        lines = lbl_p.read_text(encoding="utf-8").splitlines()
        classes = [int(l.split()[0]) for l in lines if l.strip()]
        
        has_wall = 0 in classes
        has_door = 1 in classes
        has_win = 2 in classes
        
        if has_door and has_win and len(samples_found["with_doors_and_windows"]) < 3:
            samples_found["with_doors_and_windows"].append((img_p, lbl_p))
        elif has_wall and has_win and not has_door and len(samples_found["walls_and_windows_only"]) < 2:
            samples_found["walls_and_windows_only"].append((img_p, lbl_p))
        elif has_door and not has_win and len(samples_found["doors_only"]) < 1:
            samples_found["doors_only"].append((img_p, lbl_p))
            
    print(f"Generating visual checks in {OUT_DIR}...")
    idx = 1
    for category, pairs in samples_found.items():
        for img_p, lbl_p in pairs:
            out_p = OUT_DIR / f"sample_{idx:02d}_{category}_{img_p.name}"
            draw_yolo_labels(img_p, lbl_p, out_p)
            print(f"Rendered [{idx}]: {out_p.name}")
            idx += 1
            
    print("Done rendering visual verification samples.")

if __name__ == "__main__":
    main()
