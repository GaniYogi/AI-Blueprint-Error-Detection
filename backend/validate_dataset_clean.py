"""
validate_dataset_clean.py
=========================
Validates the dataset_clean/ directory before training.

Reports:
  - Total images (train / val)
  - Total label boxes (train / val)
  - Per-class counts (wall / door / window)
  - Min / max / average box dimensions
  - Tiny box count  (<0.01 × 0.01 normalized)
  - Huge box count  (>0.80 × 0.80 normalized)
  - Duplicate box count (IoU > 0.90 same-class pairs per image)
  - Images with zero labels
  - Comparison against dataset_v2 baseline

Writes a report to: dataset_clean/validation_report.txt
"""

from pathlib import Path
from collections import defaultdict
import sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_DIR   = Path(__file__).resolve().parent.parent
DATASET_DIR   = PROJECT_DIR / "dataset_clean"
DATASET_V2    = PROJECT_DIR / "dataset_v2"

TINY_THRESH  = 0.01    # both sides < this → tiny
HUGE_THRESH  = 0.80    # both sides > this → huge
DUP_IOU      = 0.90
MIN_SIDE     = 0.005   # same as converter


# ── IoU helper ────────────────────────────────────────────────────────────────

def iou(a, b):
    def xyxy(box):
        cx, cy, w, h = box
        return cx-w/2, cy-h/2, cx+w/2, cy+h/2
    ax1,ay1,ax2,ay2 = xyxy(a)
    bx1,by1,bx2,by2 = xyxy(b)
    ix1=max(ax1,bx1); iy1=max(ay1,by1); ix2=min(ax2,bx2); iy2=min(ay2,by2)
    inter = max(0,ix2-ix1)*max(0,iy2-iy1)
    if inter == 0: return 0.0
    ua = (ax2-ax1)*(ay2-ay1); ub = (bx2-bx1)*(by2-by1)
    union = ua+ub-inter
    return inter/union if union>0 else 0.0


# ── Per-split statistics ──────────────────────────────────────────────────────

def analyze_split(label_dir: Path, split_name: str):
    txt_files = sorted(label_dir.glob("*.txt"))

    n_images       = len(txt_files)
    n_total        = 0
    class_counts   = defaultdict(int)
    widths         = []
    heights        = []
    tiny_count     = 0
    huge_count     = 0
    dup_count      = 0
    zero_label_img = 0

    for txt in txt_files:
        lines = [l.strip() for l in txt.read_text(encoding="utf-8").splitlines()
                 if l.strip()]
        if not lines:
            zero_label_img += 1
            continue

        boxes_by_class = defaultdict(list)
        file_dups = 0

        for line in lines:
            parts = line.split()
            if len(parts) != 5:
                continue
            cls, cx, cy, w, h = int(parts[0]), *[float(x) for x in parts[1:]]
            class_counts[cls] += 1
            n_total += 1
            widths.append(w); heights.append(h)

            if w < TINY_THRESH and h < TINY_THRESH:
                tiny_count += 1
            if w > HUGE_THRESH and h > HUGE_THRESH:
                huge_count += 1

            boxes_by_class[cls].append((cx, cy, w, h))

        # Duplicate check (per class, per image)
        for cls, bxs in boxes_by_class.items():
            for i in range(len(bxs)):
                for j in range(i+1, len(bxs)):
                    if iou(bxs[i], bxs[j]) >= DUP_IOU:
                        file_dups += 1
        dup_count += file_dups

    return {
        "split":          split_name,
        "n_images":       n_images,
        "n_total":        n_total,
        "class_counts":   dict(class_counts),
        "widths":         widths,
        "heights":        heights,
        "tiny_count":     tiny_count,
        "huge_count":     huge_count,
        "dup_count":      dup_count,
        "zero_label_img": zero_label_img,
    }


def stat(vals):
    if not vals:
        return 0.0, 0.0, 0.0
    return min(vals), max(vals), sum(vals)/len(vals)


def print_split(s):
    print(f"\n  ── {s['split'].upper()} ──")
    print(f"  Images        : {s['n_images']}")
    print(f"  Total boxes   : {s['n_total']}")
    print(f"  CLASS 0 wall  : {s['class_counts'].get(0, 0)}")
    print(f"  CLASS 1 door  : {s['class_counts'].get(1, 0)}")
    print(f"  CLASS 2 window: {s['class_counts'].get(2, 0)}")

    mn_w, mx_w, av_w = stat(s["widths"])
    mn_h, mx_h, av_h = stat(s["heights"])
    print(f"  Width  min/avg/max : {mn_w:.4f} / {av_w:.4f} / {mx_w:.4f}")
    print(f"  Height min/avg/max : {mn_h:.4f} / {av_h:.4f} / {mx_h:.4f}")
    print(f"  Tiny boxes (<0.01²): {s['tiny_count']}")
    print(f"  Huge boxes (>0.80²): {s['huge_count']}")
    print(f"  Duplicate boxes    : {s['dup_count']}")
    print(f"  Zero-label images  : {s['zero_label_img']}")


# ── Baseline (dataset_v2) comparison ─────────────────────────────────────────

def baseline_counts(v2_dir: Path):
    counts = defaultdict(int)
    total  = 0
    tiny   = 0
    dups   = 0
    for split in ("train", "val"):
        ldir = v2_dir / "labels" / split
        if not ldir.exists(): continue
        for txt in ldir.glob("*.txt"):
            lines = [l.strip() for l in txt.read_text(encoding="utf-8").splitlines()
                     if l.strip()]
            boxes_by_cls = defaultdict(list)
            for line in lines:
                parts = line.split()
                if len(parts) != 5: continue
                cls, cx, cy, w, h = int(parts[0]), *[float(x) for x in parts[1:]]
                counts[cls] += 1
                total += 1
                if w < TINY_THRESH and h < TINY_THRESH: tiny += 1
                boxes_by_cls[cls].append((cx,cy,w,h))
            for cls, bxs in boxes_by_cls.items():
                for i in range(len(bxs)):
                    for j in range(i+1, len(bxs)):
                        if iou(bxs[i],bxs[j]) >= DUP_IOU: dups += 1
    return counts, total, tiny, dups


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    lines_out = []

    def out(s=""):
        print(s)
        lines_out.append(s)

    out("=" * 64)
    out("DATASET_CLEAN VALIDATION REPORT")
    out("=" * 64)

    if not DATASET_DIR.exists():
        out(f"ERROR: {DATASET_DIR} does not exist. Run convert_svg_clean.py first.")
        return

    train_stats = analyze_split(DATASET_DIR / "labels" / "train", "train")
    val_stats   = analyze_split(DATASET_DIR / "labels" / "val",   "val")

    for s in (train_stats, val_stats):
        print_split(s)
        lines_out.append(
            f"\n  ── {s['split'].upper()} ──\n"
            f"  Images: {s['n_images']}  Total boxes: {s['n_total']}\n"
            f"  wall={s['class_counts'].get(0,0)}  "
            f"door={s['class_counts'].get(1,0)}  "
            f"window={s['class_counts'].get(2,0)}\n"
            f"  tiny={s['tiny_count']}  huge={s['huge_count']}  "
            f"dups={s['dup_count']}  zero-label-imgs={s['zero_label_img']}"
        )

    # Overall totals
    total_boxes = train_stats["n_total"] + val_stats["n_total"]
    total_wall  = (train_stats["class_counts"].get(0,0) +
                   val_stats["class_counts"].get(0,0))
    total_door  = (train_stats["class_counts"].get(1,0) +
                   val_stats["class_counts"].get(1,0))
    total_win   = (train_stats["class_counts"].get(2,0) +
                   val_stats["class_counts"].get(2,0))
    total_tiny  = train_stats["tiny_count"] + val_stats["tiny_count"]
    total_dups  = train_stats["dup_count"]  + val_stats["dup_count"]

    out("\n" + "=" * 64)
    out("OVERALL TOTALS (train + val)")
    out("=" * 64)
    out(f"  Total images : {train_stats['n_images'] + val_stats['n_images']}")
    out(f"  Total boxes  : {total_boxes}")
    out(f"  wall  (0)    : {total_wall}")
    out(f"  door  (1)    : {total_door}")
    out(f"  window(2)    : {total_win}")
    out(f"  Tiny boxes   : {total_tiny}")
    out(f"  Duplicates   : {total_dups}")

    # Baseline comparison
    out("\n" + "=" * 64)
    out("COMPARISON vs dataset_v2 (baseline)")
    out("=" * 64)
    if DATASET_V2.exists():
        bc, bt, btin, bdup = baseline_counts(DATASET_V2)
        out(f"  dataset_v2 total boxes: {bt}")
        out(f"    wall  : {bc.get(0,0)}")
        out(f"    door  : {bc.get(1,0)}")
        out(f"    window: {bc.get(2,0)}")
        out(f"    tiny  : {btin}")
        out(f"    dups  : {bdup}")
        out()
        out(f"  dataset_clean total boxes: {total_boxes}")
        out(f"    wall  : {total_wall:+d} vs {bc.get(0,0)}")
        out(f"    door  : {total_door:+d} vs {bc.get(1,0)}")
        out(f"    window: {total_win:+d} vs {bc.get(2,0)}")
        out(f"    tiny improvement  : {btin - total_tiny:+d}")
        out(f"    dup  improvement  : {bdup - total_dups:+d}")
    else:
        out("  dataset_v2 not found — skipping comparison")

    # Verdict
    out("\n" + "=" * 64)
    out("VERDICT")
    out("=" * 64)
    issues = []
    if total_tiny > 0:
        issues.append(f"  ⚠ {total_tiny} tiny boxes remain")
    if total_dups > 0:
        issues.append(f"  ⚠ {total_dups} duplicate boxes remain")
    if total_door == 0:
        issues.append("  ✗ CRITICAL: zero door boxes — check door layer detection")
    if total_win == 0:
        issues.append("  ✗ CRITICAL: zero window boxes — check window layer detection")
    if total_wall == 0:
        issues.append("  ✗ CRITICAL: zero wall boxes — check wall layer detection")

    if issues:
        out("  ISSUES FOUND:")
        for i in issues: out(i)
        out("\n  → Fix issues before training.")
    else:
        out("  ✓ All checks passed. Safe to proceed with training.")

    # Write report
    report_path = DATASET_DIR / "validation_report.txt"
    report_path.write_text("\n".join(lines_out), encoding="utf-8")
    out(f"\nReport saved: {report_path}")


if __name__ == "__main__":
    main()
