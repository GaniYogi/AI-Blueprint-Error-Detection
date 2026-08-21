"""
convert_svg_clean.py
====================
Clean SVG → YOLO label converter for the FloorPlanCAD dataset.

Labeling strategy (evidence-based, from investigation of 3,760 SVG files):

  CLASS 0 — WALL
    Source  : layerWALL, layerA-WALL (layer id/label contains "WALL")
    Filter  : elements with semantic-id = "1"
    Grouping: cluster by connected endpoint proximity (tol = 0.5 SVG units)
    Box     : union bbox of each connected cluster

  CLASS 1 — DOOR
    Source  : any layer whose id/label contains "DOOR" (excl. "_TEXT" layers)
    Grouping: by instance-id when present; otherwise spatial cluster
    Box     : union bbox using svgpathtools for arc-containing paths
    Fallback: layer0 arcs with stroke rgb(63,63,63) when NO door layer exists

  CLASS 2 — WINDOW
    Source  : layerWINDOW (layer id/label contains "WINDOW", excl. "_TEXT")
    Filter  : elements with semantic-id in ("3", "9") OR any semantic-id
    Grouping: by instance-id
    Box     : svgpathtools bbox for each instance group

Safety:
  - Does NOT overwrite dataset_v2, dataset_v3, dataset_final
  - Outputs to dataset_clean/
  - Skips SVGs with no valid labels (writes nothing)
"""

import math
import random
import re
import shutil
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

# svgpathtools for accurate arc bounding boxes
try:
    from svgpathtools import parse_path
    HAS_SVGPATHTOOLS = True
except ImportError:
    HAS_SVGPATHTOOLS = False
    print("WARNING: svgpathtools not available, using coordinate extraction fallback")

# ── Configuration ─────────────────────────────────────────────────────────────

SOURCE_DIR  = Path(r"C:\Users\ganiy\OneDrive\Desktop\train-00")
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_DIR / "dataset_clean"

MAX_FILES    = 5000        # process all available files
TRAIN_RATIO  = 0.8
RANDOM_SEED  = 42

# Minimum box dimensions in NORMALIZED coords (0–1)
MIN_BOX_SIDE = 0.005       # 0.5% of image side
MIN_BOX_AREA = MIN_BOX_SIDE * MIN_BOX_SIDE

# Maximum box dimensions for WINDOWS and DOORS in NORMALIZED coords
# A single window/door should not occupy > 60% of the image in EITHER axis
MAX_WIN_SIDE  = 0.60
MAX_DOOR_SIDE = 0.70

# Endpoint proximity tolerance (SVG coordinate units)
CLUSTER_TOL  = 0.8

# IoU threshold for duplicate removal
DUP_IOU_THRESH = 0.90

SVG_NS   = "http://www.w3.org/2000/svg"
INK_NS   = "http://www.inkscape.org/namespaces/inkscape"

# Confirmed semantic IDs
WALL_SEM_IDS   = {"1"}
WINDOW_SEM_IDS = {"3", "9"}   # 3=bay/arc window, 9=flat wall window
DOOR_SEM_IDS   = {"4"}         # fire door

# layer0 door-swing color (dark grey)
LAYER0_DOOR_COLOR = "rgb(63,63,63)"

# ── Directory setup ───────────────────────────────────────────────────────────

for folder in [
    DATASET_DIR / "images" / "train",
    DATASET_DIR / "images" / "val",
    DATASET_DIR / "labels" / "train",
    DATASET_DIR / "labels" / "val",
]:
    folder.mkdir(parents=True, exist_ok=True)


# ── Helper: safe ASCII string ─────────────────────────────────────────────────

def safe(s: str) -> str:
    return (s or "").encode("ascii", "replace").decode("ascii")


# ── Helper: get element tag without namespace ─────────────────────────────────

def elem_tag(e) -> str:
    return e.tag.split("}")[-1].lower()


# ── SVG viewBox extraction ────────────────────────────────────────────────────

def get_viewbox(root):
    vb = root.attrib.get("viewBox", "")
    nums = re.findall(r"[-+]?\d*\.?\d+", vb)
    if len(nums) < 4:
        raise ValueError(f"Cannot parse viewBox: {vb!r}")
    return tuple(float(n) for n in nums[:4])


# ── Coordinate extraction from SVG path d attribute ──────────────────────────

def _nums_from_d(d: str):
    """Return all numbers from a path d string."""
    return [float(x) for x in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", d)]


def bbox_from_d_simple(d: str):
    """
    Simple bounding box for pure M/L/H/V paths only (no arcs).
    Properly handles SVG path commands to avoid mixing in arc radii/flags.
    """
    xs, ys = [], []
    x, y = 0.0, 0.0
    tokens = re.findall(
        r"[MmLlHhVvZz]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?",
        d
    )
    cmd = None
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if re.fullmatch(r"[A-Za-z]", t):
            cmd = t; i += 1; continue
        try:
            v = float(t)
        except ValueError:
            i += 1; continue

        if cmd in ("M", "L"):
            if i + 1 < len(tokens):
                try:
                    x, y = v, float(tokens[i+1])
                    xs.append(x); ys.append(y)
                    i += 2; continue
                except (ValueError, IndexError): pass
        elif cmd in ("m", "l"):
            if i + 1 < len(tokens):
                try:
                    x += v; y += float(tokens[i+1])
                    xs.append(x); ys.append(y)
                    i += 2; continue
                except (ValueError, IndexError): pass
        elif cmd in ("H",):
            x = v; xs.append(x); ys.append(y)
        elif cmd in ("h",):
            x += v; xs.append(x); ys.append(y)
        elif cmd in ("V",):
            y = v; xs.append(x); ys.append(y)
        elif cmd in ("v",):
            y += v; xs.append(x); ys.append(y)
        elif cmd in ("A", "a"):
            # Arc: rx ry x-rot large-arc-flag sweep-flag x y
            # Skip 4 parameters (rx,ry,rot,flags) and read endpoint (x,y)
            # We'll extract just the destination coords
            try:
                # consume rx,ry,x-rot = 3 numbers, then 2 flags, then x,y
                # tokens i..i+6
                if i + 6 < len(tokens):
                    ex = float(tokens[i+5])
                    ey = float(tokens[i+6])
                    if cmd == "A":
                        x, y = ex, ey
                    else:
                        x += ex; y += ey
                    xs.append(x); ys.append(y)
                    i += 7; continue
            except (ValueError, IndexError): pass
        i += 1

    if not xs: return None
    return min(xs), min(ys), max(xs), max(ys)


def bbox_from_d_accurate(d: str):
    """
    Accurate bounding box using svgpathtools (handles arc curves properly).
    Falls back to simple extraction if unavailable or path is empty.
    """
    if HAS_SVGPATHTOOLS and d:
        try:
            path = parse_path(d)
            if len(path) > 0:
                xmin, xmax, ymin, ymax = path.bbox()
                return xmin, ymin, xmax, ymax
        except Exception:
            pass
    return bbox_from_d_simple(d)


def element_bbox(elem):
    """Return (x1,y1,x2,y2) for a path/circle/ellipse/rect element."""
    t = elem_tag(elem)
    if t == "path":
        d = elem.attrib.get("d", "")
        return bbox_from_d_accurate(d)
    if t == "circle":
        try:
            cx = float(elem.attrib.get("cx", 0))
            cy = float(elem.attrib.get("cy", 0))
            r  = float(elem.attrib.get("r",  0))
            if r <= 0: return None
            return cx - r, cy - r, cx + r, cy + r
        except Exception:
            return None
    if t == "ellipse":
        try:
            cx = float(elem.attrib.get("cx", 0))
            cy = float(elem.attrib.get("cy", 0))
            rx = float(elem.attrib.get("rx", 0))
            ry = float(elem.attrib.get("ry", 0))
            if rx <= 0 or ry <= 0: return None
            return cx - rx, cy - ry, cx + rx, cy + ry
        except Exception:
            return None
    if t == "rect":
        try:
            x = float(elem.attrib.get("x", 0))
            y = float(elem.attrib.get("y", 0))
            w = float(elem.attrib.get("width",  0))
            h = float(elem.attrib.get("height", 0))
            if w <= 0 or h <= 0: return None
            return x, y, x + w, y + h
        except Exception:
            return None
    return None


def merge_bbox(a, b):
    if a is None: return b
    if b is None: return a
    return min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])


# ── Endpoint extraction for clustering ───────────────────────────────────────

def endpoints_from_d(d: str):
    """Return start and end coordinate of a path."""
    nums = _nums_from_d(d)
    if len(nums) < 2:
        return None, None
    start = (nums[0], nums[1])
    end   = (nums[-2], nums[-1])
    return start, end


# ── Connected-component clustering ───────────────────────────────────────────

def cluster_by_endpoints(elements, tol=CLUSTER_TOL):
    """
    Group elements whose path endpoints are within `tol` SVG units of
    any element already in a group.  Returns list of lists of elements.
    """
    groups = []          # list of (list_of_elements, list_of_points)

    for elem in elements:
        d = elem.attrib.get("d", "")
        s, e = endpoints_from_d(d)
        pts = [p for p in (s, e) if p is not None]

        merged = False
        for group_elems, group_pts in groups:
            # Check if any endpoint of this element is near any group endpoint
            for ep in pts:
                for gp in group_pts:
                    if math.dist(ep, gp) < tol:
                        group_elems.append(elem)
                        group_pts.extend(pts)
                        merged = True
                        break
                if merged: break
            if merged: break

        if not merged:
            groups.append(([elem], list(pts)))

    return [g[0] for g in groups]


def cluster_by_spatial_proximity(elements, tol=5.0):
    """
    Group elements whose bounding boxes are within `tol` SVG units of
    each other (used for door layers without instance-id).
    """
    boxes = []
    for elem in elements:
        bb = element_bbox(elem)
        boxes.append((elem, bb))

    groups = []
    used = set()

    for i, (elem_i, bb_i) in enumerate(boxes):
        if i in used: continue
        if bb_i is None: continue
        group = [elem_i]
        used.add(i)
        # find all nearby elements
        cx_i = (bb_i[0] + bb_i[2]) / 2
        cy_i = (bb_i[1] + bb_i[3]) / 2
        for j, (elem_j, bb_j) in enumerate(boxes):
            if j in used: continue
            if bb_j is None: continue
            cx_j = (bb_j[0] + bb_j[2]) / 2
            cy_j = (bb_j[1] + bb_j[3]) / 2
            if math.dist((cx_i, cy_i), (cx_j, cy_j)) < tol:
                group.append(elem_j)
                used.add(j)
        groups.append(group)

    return groups


# ── YOLO box helper ───────────────────────────────────────────────────────────

def to_yolo(bbox, vb_w, vb_h, vb_x=0.0, vb_y=0.0,
            max_w=1.0, max_h=1.0):
    """
    Convert (x1,y1,x2,y2) SVG coords to YOLO normalized format.
    Returns (cx, cy, w, h) all in [0,1], or None if box is too small/large.
    """
    x1, y1, x2, y2 = bbox
    # Remove viewBox origin offset
    x1 -= vb_x;  x2 -= vb_x
    y1 -= vb_y;  y2 -= vb_y
    # Clamp to viewBox
    x1 = max(0.0, min(vb_w, x1));  x2 = max(0.0, min(vb_w, x2))
    y1 = max(0.0, min(vb_h, y1));  y2 = max(0.0, min(vb_h, y2))

    w = x2 - x1;  h = y2 - y1
    if w <= 0 or h <= 0: return None

    cx = (x1 + x2) / 2.0 / vb_w
    cy = (y1 + y2) / 2.0 / vb_h
    nw = w / vb_w
    nh = h / vb_h

    if nw < MIN_BOX_SIDE or nh < MIN_BOX_SIDE:
        return None
    if nw * nh < MIN_BOX_AREA:
        return None
    if nw > max_w or nh > max_h:
        return None  # reject oversized boxes

    return cx, cy, nw, nh


# ── Duplicate (IoU) removal ───────────────────────────────────────────────────

def iou(a, b):
    """Compute IoU of two YOLO boxes (cx,cy,w,h)."""
    def to_xyxy(box):
        cx, cy, w, h = box
        return cx - w/2, cy - h/2, cx + w/2, cy + h/2

    ax1, ay1, ax2, ay2 = to_xyxy(a)
    bx1, by1, bx2, by2 = to_xyxy(b)

    ix1 = max(ax1, bx1);  iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2);  iy2 = min(ay2, by2)

    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if inter == 0: return 0.0

    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union  = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def remove_duplicates(boxes, thresh=DUP_IOU_THRESH):
    """
    Remove duplicate YOLO boxes.  boxes = list of (class_id, cx, cy, w, h).
    Returns deduplicated list.
    """
    kept = []
    for box in boxes:
        cls, *yolo = box
        is_dup = False
        for kbox in kept:
            kcls, *kyolo = kbox
            if kcls == cls and iou(tuple(yolo), tuple(kyolo)) >= thresh:
                is_dup = True
                break
        if not is_dup:
            kept.append(box)
    return kept


# ── Layer classification ──────────────────────────────────────────────────────

def layer_type(layer_elem):
    """
    Determine if a <g> element is a wall/window/door/other layer.
    Returns 'WALL', 'WINDOW', 'WINDOW_TEXT', 'DOOR', 'DOOR_TEXT', 'OTHER', or None.
    """
    lid   = (layer_elem.attrib.get("id",  "") or "").upper()
    label = (layer_elem.attrib.get(f"{{{INK_NS}}}label", "") or "").upper()
    text  = lid + " " + label

    # Text annotation layers — ignore for geometry
    if "_TEXT" in text:
        return "TEXT"

    if "WALL"   in text: return "WALL"
    if "WINDOW" in text: return "WINDOW"
    if "DOOR"   in text: return "DOOR"
    return "OTHER"


# ── WALL extraction ───────────────────────────────────────────────────────────

def extract_walls(wall_layers, vb_x, vb_y, vb_w, vb_h):
    """
    Returns list of (0, cx, cy, w, h) YOLO tuples.
    Groups wall paths by connected endpoint proximity.
    """
    labels = []
    for layer in wall_layers:
        # Collect paths with semantic-id = "1" (confirmed wall)
        paths = [
            e for e in layer
            if elem_tag(e) in ("path", "rect", "polyline")
            and e.attrib.get("semantic-id") in WALL_SEM_IDS
        ]
        # If no semantic-id=1 elements, fall back to ALL paths in wall layer
        if not paths:
            paths = [
                e for e in layer
                if elem_tag(e) in ("path", "rect", "polyline")
            ]

        # Cluster by endpoint proximity
        clusters = cluster_by_endpoints(paths)

        for cluster in clusters:
            bb = None
            for elem in cluster:
                bb = merge_bbox(bb, element_bbox(elem))
            if bb is None: continue
            yolo = to_yolo(bb, vb_w, vb_h, vb_x, vb_y)
            if yolo:
                labels.append((0, *yolo))

    return labels


# ── WINDOW extraction ─────────────────────────────────────────────────────────

def extract_windows(window_layers, vb_x, vb_y, vb_w, vb_h):
    """
    Returns list of (2, cx, cy, w, h) YOLO tuples.
    Groups window paths by instance-id.
    """
    labels = []
    for layer in window_layers:
        paths = [
            e for e in layer
            if elem_tag(e) in ("path", "circle", "ellipse", "rect")
        ]

        # Group by instance-id
        instance_groups = defaultdict(list)
        untagged = []
        for e in paths:
            iid = e.attrib.get("instance-id")
            if iid:
                instance_groups[iid].append(e)
            else:
                untagged.append(e)

        # Process each instance group
        for iid, elems in instance_groups.items():
            bb = None
            for elem in elems:
                bb = merge_bbox(bb, element_bbox(elem))
            if bb is None: continue
            yolo = to_yolo(bb, vb_w, vb_h, vb_x, vb_y,
                           max_w=MAX_WIN_SIDE, max_h=MAX_WIN_SIDE)
            if yolo:
                labels.append((2, *yolo))

        # Untagged: cluster spatially
        if untagged:
            clusters = cluster_by_spatial_proximity(untagged, tol=3.0)
            for cluster in clusters:
                bb = None
                for elem in cluster:
                    bb = merge_bbox(bb, element_bbox(elem))
                if bb is None: continue
                yolo = to_yolo(bb, vb_w, vb_h, vb_x, vb_y,
                               max_w=MAX_WIN_SIDE, max_h=MAX_WIN_SIDE)
                if yolo:
                    labels.append((2, *yolo))

    return labels


# ── DOOR extraction ───────────────────────────────────────────────────────────

def extract_doors(door_layers, layer0, vb_x, vb_y, vb_w, vb_h):
    """
    Returns list of (1, cx, cy, w, h) YOLO tuples.

    Priority 1: named door layers (layerDOOR_FIRE, layerA-DOOR, etc.)
                grouped by instance-id when present, else spatial cluster.

    Priority 2: layer0 rgb(63,63,63) arcs when no door layers exist.
    """
    labels = []
    found_from_named_layers = False

    # ── Priority 1: named door layers ────────────────────────────────────────
    for layer in door_layers:
        paths = [
            e for e in layer
            if elem_tag(e) in ("path", "circle", "ellipse", "rect")
        ]
        if not paths:
            continue

        # Group by instance-id when available
        instance_groups = defaultdict(list)
        untagged = []
        for e in paths:
            iid = e.attrib.get("instance-id")
            if iid:
                instance_groups[iid].append(e)
            else:
                untagged.append(e)

        for iid, elems in instance_groups.items():
            bb = None
            for elem in elems:
                bb = merge_bbox(bb, element_bbox(elem))
            if bb is None: continue
            # Door boxes must have reasonable aspect ratio & size
            w_svgu = bb[2] - bb[0]
            h_svgu = bb[3] - bb[1]
            if w_svgu < 0.5 or h_svgu < 0.5:
                continue
            yolo = to_yolo(bb, vb_w, vb_h, vb_x, vb_y,
                           max_w=MAX_DOOR_SIDE, max_h=MAX_DOOR_SIDE)
            if yolo:
                labels.append((1, *yolo))
                found_from_named_layers = True

        if untagged:
            clusters = cluster_by_spatial_proximity(untagged, tol=8.0)
            for cluster in clusters:
                bb = None
                for elem in cluster:
                    bb = merge_bbox(bb, element_bbox(elem))
                if bb is None: continue
                w_svgu = bb[2] - bb[0]
                h_svgu = bb[3] - bb[1]
                if w_svgu < 0.5 or h_svgu < 0.5:
                    continue
                yolo = to_yolo(bb, vb_w, vb_h, vb_x, vb_y,
                               max_w=MAX_DOOR_SIDE, max_h=MAX_DOOR_SIDE)
                if yolo:
                    labels.append((1, *yolo))
                    found_from_named_layers = True

    # ── Priority 2: layer0 arc fallback (only when no named door layer found) ─
    if not found_from_named_layers and layer0 is not None:
        arc_paths = [
            e for e in layer0
            if elem_tag(e) == "path"
            and e.attrib.get("stroke") == LAYER0_DOOR_COLOR
            and "A " in e.attrib.get("d", "")
        ]
        for arc in arc_paths:
            d_arc = arc.attrib.get("d", "")
            # Use arc's OWN bbox only — connected lines inflate the box
            bb = bbox_from_d_accurate(d_arc)
            if bb is None: continue
            # Add a small padding equal to the arc's estimated radius
            # Arc: "A rx,ry ..." — extract first number after A
            try:
                m = re.search(r"A\s+([\d.]+)", d_arc)
                r = float(m.group(1)) if m else 2.0
            except Exception:
                r = 2.0
            bb = (bb[0] - r * 0.1, bb[1] - r * 0.1,
                  bb[2] + r * 0.1, bb[3] + r * 0.1)
            # Arc doors should be small (~4-unit radius → ~0.04–0.12 normalized)
            yolo = to_yolo(bb, vb_w, vb_h, vb_x, vb_y,
                           max_w=0.25, max_h=0.25)
            if yolo:
                labels.append((1, *yolo))

    return labels



# ── Main per-SVG converter ────────────────────────────────────────────────────

def convert_svg(svg_path: Path):
    """
    Parse one SVG and return a list of YOLO label strings.
    Returns empty list if no labels found.
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()

    vb_x, vb_y, vb_w, vb_h = get_viewbox(root)
    if vb_w <= 0 or vb_h <= 0:
        return []

    # Collect layers (direct children of <svg> that are <g>)
    wall_layers   = []
    window_layers = []
    door_layers   = []
    layer0        = None

    for g in root:
        if elem_tag(g) != "g":
            continue
        lid = g.attrib.get("id", "")
        if lid == "layer0":
            layer0 = g
        lt = layer_type(g)
        if lt == "WALL":
            wall_layers.append(g)
        elif lt == "WINDOW":
            window_layers.append(g)
        elif lt == "DOOR":
            door_layers.append(g)

    all_labels = []
    all_labels.extend(extract_walls(wall_layers, vb_x, vb_y, vb_w, vb_h))
    all_labels.extend(extract_windows(window_layers, vb_x, vb_y, vb_w, vb_h))
    all_labels.extend(extract_doors(door_layers, layer0, vb_x, vb_y, vb_w, vb_h))

    # Remove duplicates
    all_labels = remove_duplicates(all_labels)

    # Convert to YOLO label strings
    return [
        f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}"
        for cls_id, cx, cy, w, h in all_labels
    ]


# ── Main pipeline ─────────────────────────────────────────────────────────────

def create_data_yaml():
    yaml_text = (
        "path: ../dataset_clean\n"
        "\n"
        "train: images/train\n"
        "val:   images/val\n"
        "\n"
        "nc: 3\n"
        "\n"
        "names:\n"
        "  0: wall\n"
        "  1: door\n"
        "  2: window\n"
    )
    (DATASET_DIR / "data.yaml").write_text(yaml_text, encoding="utf-8")


def main():
    print("=" * 64)
    print("FloorPlanCAD CLEAN CONVERTER")
    print(f"Source : {SOURCE_DIR}")
    print(f"Output : {DATASET_DIR}")
    print("=" * 64)

    png_files = sorted(SOURCE_DIR.glob("*.png"))[:MAX_FILES]
    print(f"PNG files found: {len(png_files)}")

    random.seed(RANDOM_SEED)
    random.shuffle(png_files)

    split = int(len(png_files) * TRAIN_RATIO)
    train_set = set(png_files[:split])

    processed = skipped = 0
    counts = {0: 0, 1: 0, 2: 0}
    empty_label_files = 0

    for idx, png in enumerate(png_files, 1):
        svg = png.with_suffix(".svg")
        if not svg.exists():
            skipped += 1
            continue

        try:
            labels = convert_svg(svg)
        except Exception as err:
            print(f"[ERROR] {png.name}: {err}")
            skipped += 1
            continue

        # Files with no labels are still included (open-plan, parking, etc.)
        if not labels:
            empty_label_files += 1

        split_name = "train" if png in train_set else "val"
        img_dst    = DATASET_DIR / "images" / split_name / png.name
        lbl_dst    = DATASET_DIR / "labels" / split_name / f"{png.stem}.txt"

        shutil.copy2(png, img_dst)
        lbl_dst.write_text("\n".join(labels), encoding="utf-8")

        for line in labels:
            cls = int(line.split()[0])
            counts[cls] = counts.get(cls, 0) + 1

        processed += 1

        if idx % 100 == 0 or idx == 1:
            print(
                f"  [{idx:4d}/{len(png_files)}]  "
                f"wall={counts[0]:5d}  door={counts[1]:4d}  win={counts[2]:4d}"
            )

    create_data_yaml()

    print()
    print("=" * 64)
    print("CONVERSION COMPLETE")
    print("=" * 64)
    print(f"Processed  : {processed}")
    print(f"Skipped    : {skipped}")
    print(f"Empty labels: {empty_label_files} (images kept, label file empty)")
    print()
    print("Final label counts:")
    print(f"  CLASS 0 — wall   : {counts[0]:6d}")
    print(f"  CLASS 1 — door   : {counts[1]:6d}")
    print(f"  CLASS 2 — window : {counts[2]:6d}")
    print(f"  TOTAL            : {sum(counts.values()):6d}")
    print()
    print(f"Dataset written to: {DATASET_DIR}")
    print()
    print("Next step: run  python backend/validate_dataset_clean.py")


if __name__ == "__main__":
    main()
