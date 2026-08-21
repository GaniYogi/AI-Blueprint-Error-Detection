"""
test_real_blueprints.py
=======================
Tests both the current production model and the new clean model on real blueprint drawings.
Generates side-by-side detection images showing:
  - Green  : Walls
  - SkyBlue: Doors
  - Yellow : Windows
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw
from ultralytics import YOLO

PROJECT_DIR = Path(__file__).resolve().parent.parent
PROD_MODEL_PATH = PROJECT_DIR / "backend" / "models" / "best.pt"
CLEAN_MODEL_PATH = PROJECT_DIR / "runs" / "train" / "blueprint_clean" / "weights" / "best.pt"
OUT_DIR = PROJECT_DIR / "runs" / "model_comparisons"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CLASS_COLORS = {
    "wall": ("#22c55e", "Wall"),      # Green
    "door": ("#0ea5e9", "Door"),      # SkyBlue
    "window": ("#eab308", "Window"),  # Yellow
    0: ("#22c55e", "Wall"),
    1: ("#0ea5e9", "Door"),
    2: ("#eab308", "Window"),
}

def detect_and_draw(model, img_path: Path, title: str) -> Image.Image:
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    w_img, h_img = img.size
    
    results = model.predict(source=str(img_path), conf=0.20, verbose=False)
    
    counts = {"wall": 0, "door": 0, "window": 0}
    
    for r in results:
        if r.boxes is None: continue
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_idx = int(box.cls[0])
            conf = float(box.conf[0])
            label_name = model.names.get(cls_idx, str(cls_idx)).lower()
            
            counts[label_name] = counts.get(label_name, 0) + 1
            
            color_hex, display_name = CLASS_COLORS.get(label_name, ("#ffffff", label_name))
            
            draw.rectangle([x1, y1, x2, y2], outline=color_hex, width=3)
            tag_text = f"{display_name} {int(conf*100)}%"
            draw.rectangle([x1, max(0, y1 - 16), x1 + len(tag_text) * 7 + 4, y1], fill=color_hex)
            draw.text((x1 + 2, max(0, y1 - 15)), tag_text, fill="black")
            
    # Draw header overlay
    header_text = f"{title} | Walls: {counts.get('wall',0)}, Doors: {counts.get('door',0)}, Windows: {counts.get('window',0)}"
    draw.rectangle([0, 0, w_img, 30], fill="#0f172a")
    draw.text((10, 8), header_text, fill="white")
    
    return img, counts

def main():
    print("=" * 68)
    print("TESTING MODELS ON REAL BLUEPRINT IMAGES")
    print("=" * 68)
    
    if not PROD_MODEL_PATH.exists():
        print("Production model not found.")
        return
        
    prod_model = YOLO(str(PROD_MODEL_PATH))
    
    clean_model = None
    if CLEAN_MODEL_PATH.exists():
        clean_model = YOLO(str(CLEAN_MODEL_PATH))
    else:
        print("Note: clean model weights not yet found. Testing production model first.")
        
    # Gather test images (from uploads/ and val/)
    test_images = list((PROJECT_DIR / "uploads").glob("*.png"))[:3]
    val_images = list((PROJECT_DIR / "dataset_clean" / "images" / "val").glob("*.png"))[:3]
    all_tests = test_images + val_images
    
    for idx, img_p in enumerate(all_tests, 1):
        print(f"\n--- Testing Image {idx}: {img_p.name} ---")
        img_prod, prod_counts = detect_and_draw(prod_model, img_p, "CURRENT PRODUCTION MODEL")
        print(f"  Production Model Detections: Walls={prod_counts.get('wall',0)}, Doors={prod_counts.get('door',0)}, Windows={prod_counts.get('window',0)}")
        
        if clean_model:
            img_clean, clean_counts = detect_and_draw(clean_model, img_p, "NEW BLUEPRINT_CLEAN MODEL")
            print(f"  Clean Model Detections     : Walls={clean_counts.get('wall',0)}, Doors={clean_counts.get('door',0)}, Windows={clean_counts.get('window',0)}")
            
            # Combine side by side
            w1, h1 = img_prod.size
            w2, h2 = img_clean.size
            combined = Image.new("RGB", (w1 + w2 + 10, max(h1, h2)), "#1e293b")
            combined.paste(img_prod, (0, 0))
            combined.paste(img_clean, (w1 + 10, 0))
            
            out_path = OUT_DIR / f"comparison_{idx:02d}_{img_p.stem}.png"
            combined.save(out_path)
            print(f"  Saved comparison: {out_path.name}")
        else:
            out_path = OUT_DIR / f"prod_eval_{idx:02d}_{img_p.stem}.png"
            img_prod.save(out_path)
            print(f"  Saved production visual: {out_path.name}")

if __name__ == "__main__":
    main()
