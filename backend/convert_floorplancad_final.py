import random
import shutil
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from svgpathtools import parse_path


# ============================================================
# CONFIG
# ============================================================

SOURCE_DIR = Path(
    r"C:\Users\ganiy\OneDrive\Desktop\train-00"
)

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = PROJECT_DIR / "dataset_final"

MAX_FILES = 500
TRAIN_RATIO = 0.8
RANDOM_SEED = 42


# ============================================================
# FLOORPLANCAD SEMANTIC CLASSES
#
# For the first detector we use:
#
# 33 = wall
#
# The remaining IDs are kept here for inspection rather than
# guessing their meaning.
# ============================================================

WALL_SEMANTIC_ID = "33"


# ============================================================
# YOLO CLASSES
# ============================================================

CLASS_NAMES = {
    0: "wall",
    1: "door",
    2: "window",
}


# ============================================================
# DIRECTORIES
# ============================================================

TRAIN_IMAGES = DATASET_DIR / "images" / "train"
VAL_IMAGES = DATASET_DIR / "images" / "val"

TRAIN_LABELS = DATASET_DIR / "labels" / "train"
VAL_LABELS = DATASET_DIR / "labels" / "val"


for folder in [
    TRAIN_IMAGES,
    VAL_IMAGES,
    TRAIN_LABELS,
    VAL_LABELS,
]:
    folder.mkdir(
        parents=True,
        exist_ok=True
    )


# ============================================================
# XML NAMESPACE
# ============================================================

SVG_NS = "http://www.w3.org/2000/svg"


# ============================================================
# GET NUMERIC VIEWBOX
# ============================================================

def get_viewbox(root):

    viewbox = root.attrib.get(
        "viewBox"
    )

    if not viewbox:
        raise ValueError(
            "SVG does not contain viewBox"
        )

    values = [
        float(v)
        for v in viewbox.replace(
            ",",
            " "
        ).split()
    ]

    if len(values) != 4:
        raise ValueError(
            f"Invalid viewBox: {viewbox}"
        )

    return values


# ============================================================
# GET PATH BOUNDING BOX
# ============================================================

def path_bbox(path_data):

    if not path_data:
        return None

    try:
        path = parse_path(
            path_data
        )

        if len(path) == 0:
            return None

        xmin, xmax, ymin, ymax = (
            path.bbox()
        )

        return (
            xmin,
            ymin,
            xmax,
            ymax,
        )

    except Exception:
        return None


# ============================================================
# GET RECTANGLE BBOX
# ============================================================

def rect_bbox(element):

    try:
        x = float(
            element.attrib.get(
                "x",
                0
            )
        )

        y = float(
            element.attrib.get(
                "y",
                0
            )
        )

        width = float(
            element.attrib.get(
                "width",
                0
            )
        )

        height = float(
            element.attrib.get(
                "height",
                0
            )
        )

        if width <= 0 or height <= 0:
            return None

        return (
            x,
            y,
            x + width,
            y + height,
        )

    except Exception:
        return None


# ============================================================
# GET CIRCLE BBOX
# ============================================================

def circle_bbox(element):

    try:
        cx = float(
            element.attrib.get(
                "cx",
                0
            )
        )

        cy = float(
            element.attrib.get(
                "cy",
                0
            )
        )

        r = float(
            element.attrib.get(
                "r",
                0
            )
        )

        if r <= 0:
            return None

        return (
            cx - r,
            cy - r,
            cx + r,
            cy + r,
        )

    except Exception:
        return None


# ============================================================
# GET ELLIPSE BBOX
# ============================================================

def ellipse_bbox(element):

    try:
        cx = float(
            element.attrib.get(
                "cx",
                0
            )
        )

        cy = float(
            element.attrib.get(
                "cy",
                0
            )
        )

        rx = float(
            element.attrib.get(
                "rx",
                0
            )
        )

        ry = float(
            element.attrib.get(
                "ry",
                0
            )
        )

        if rx <= 0 or ry <= 0:
            return None

        return (
            cx - rx,
            cy - ry,
            cx + rx,
            cy + ry,
        )

    except Exception:
        return None


# ============================================================
# MERGE BBOXES
# ============================================================

def merge_bbox(current, new):

    if new is None:
        return current

    if current is None:
        return new

    return (
        min(
            current[0],
            new[0]
        ),
        min(
            current[1],
            new[1]
        ),
        max(
            current[2],
            new[2]
        ),
        max(
            current[3],
            new[3]
        ),
    )


# ============================================================
# GET ELEMENT BBOX
# ============================================================

def element_bbox(element):

    tag = element.tag.split(
        "}"
    )[-1].lower()

    if tag == "path":

        return path_bbox(
            element.attrib.get(
                "d"
            )
        )

    if tag == "rect":

        return rect_bbox(
            element
        )

    if tag == "circle":

        return circle_bbox(
            element
        )

    if tag == "ellipse":

        return ellipse_bbox(
            element
        )

    return None


# ============================================================
# DETERMINE CLASS
# ============================================================

def get_class_id(
    semantic_id,
    instance_id
):

    # Wall is confirmed as semantic 33.
    if semantic_id == WALL_SEMANTIC_ID:

        return 0

    # IMPORTANT:
    #
    # We deliberately do NOT guess door/window IDs here.
    #
    # Those will be detected from the official semantic
    # mapping before training.
    #
    return None


# ============================================================
# CONVERT ONE SVG
# ============================================================

def convert_svg(svg_file):

    tree = ET.parse(
        svg_file
    )

    root = tree.getroot()

    view_min_x, view_min_y, view_width, view_height = (
        get_viewbox(root)
    )

    # --------------------------------------------------------
    # Group by semantic + instance.
    # --------------------------------------------------------

    objects = defaultdict(
        lambda: None
    )

    # --------------------------------------------------------
    # Process SVG elements.
    # --------------------------------------------------------

    for element in root.iter():

        semantic_id = element.attrib.get(
            "semantic-id"
        )

        instance_id = element.attrib.get(
            "instance-id"
        )

        if semantic_id is None:
            continue

        if instance_id is None:
            instance_id = "-1"

        class_id = get_class_id(
            semantic_id,
            instance_id
        )

        if class_id is None:
            continue

        box = element_bbox(
            element
        )

        if box is None:
            continue

        key = (
            semantic_id,
            instance_id,
            class_id,
        )

        objects[key] = merge_bbox(
            objects[key],
            box
        )

    # --------------------------------------------------------
    # Convert to YOLO.
    # --------------------------------------------------------

    labels = []

    for (
        semantic_id,
        instance_id,
        class_id,
    ), box in objects.items():

        if box is None:
            continue

        x1, y1, x2, y2 = box

        # Convert viewBox origin.
        x1 -= view_min_x
        x2 -= view_min_x

        y1 -= view_min_y
        y2 -= view_min_y

        # Clamp.
        x1 = max(
            0,
            min(
                view_width,
                x1
            )
        )

        x2 = max(
            0,
            min(
                view_width,
                x2
            )
        )

        y1 = max(
            0,
            min(
                view_height,
                y1
            )
        )

        y2 = max(
            0,
            min(
                view_height,
                y2
            )
        )

        width = x2 - x1
        height = y2 - y1

        if width <= 0 or height <= 0:
            continue

        center_x = (
            (x1 + x2) / 2
        ) / view_width

        center_y = (
            (y1 + y2) / 2
        ) / view_height

        norm_width = (
            width / view_width
        )

        norm_height = (
            height / view_height
        )

        labels.append(
            f"{class_id} "
            f"{center_x:.6f} "
            f"{center_y:.6f} "
            f"{norm_width:.6f} "
            f"{norm_height:.6f}"
        )

    return labels


# ============================================================
# CREATE YAML
# ============================================================

def create_yaml():

    yaml_text = """path: ../dataset_final

train: images/train
val: images/val

names:
  0: wall
  1: door
  2: window
"""

    yaml_file = (
        DATASET_DIR
        / "data.yaml"
    )

    yaml_file.write_text(
        yaml_text,
        encoding="utf-8"
    )

    print(
        f"Created: {yaml_file}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("FloorPlanCAD FINAL CONVERTER")
    print("=" * 60)

    png_files = list(
        SOURCE_DIR.glob(
            "*.png"
        )
    )

    print(
        f"PNG files found: "
        f"{len(png_files)}"
    )

    if not png_files:

        print(
            "ERROR: No PNG files found."
        )

        return

    random.seed(
        RANDOM_SEED
    )

    random.shuffle(
        png_files
    )

    png_files = png_files[
        :MAX_FILES
    ]

    split_index = int(
        len(png_files)
        * TRAIN_RATIO
    )

    train_files = set(
        png_files[
            :split_index
        ]
    )

    processed = 0
    skipped = 0

    wall_count = 0

    for index, image_file in enumerate(
        png_files,
        start=1
    ):

        svg_file = (
            image_file.with_suffix(
                ".svg"
            )
        )

        if not svg_file.exists():

            skipped += 1

            continue

        try:

            labels = convert_svg(
                svg_file
            )

        except Exception as error:

            print(
                f"[ERROR] "
                f"{image_file.name}: "
                f"{error}"
            )

            skipped += 1

            continue

        if not labels:

            print(
                f"[SKIP] "
                f"{image_file.name}"
            )

            skipped += 1

            continue

        if image_file in train_files:

            image_dir = TRAIN_IMAGES
            label_dir = TRAIN_LABELS

        else:

            image_dir = VAL_IMAGES
            label_dir = VAL_LABELS

        shutil.copy2(
            image_file,
            image_dir
            / image_file.name
        )

        label_file = (
            label_dir
            / f"{image_file.stem}.txt"
        )

        label_file.write_text(
            "\n".join(labels),
            encoding="utf-8"
        )

        processed += 1

        wall_count += sum(
            1
            for label in labels
            if label.startswith(
                "0 "
            )
        )

        if (
            index % 25 == 0
            or index == 1
        ):

            print(
                f"[{index}/{len(png_files)}] "
                f"{image_file.name}"
            )

    create_yaml()

    print()
    print("=" * 60)
    print("FINAL CONVERSION COMPLETE")
    print("=" * 60)

    print(
        f"Processed: {processed}"
    )

    print(
        f"Skipped:   {skipped}"
    )

    print(
        f"Wall boxes: {wall_count}"
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "Only confirmed wall semantic ID "
        "33 is currently enabled."
    )

    print(
        "Door/window semantic IDs are NOT "
        "guessed."
    )


if __name__ == "__main__":
    main()