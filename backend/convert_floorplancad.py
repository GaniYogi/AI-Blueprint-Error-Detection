import random
import shutil
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from svgpathtools import parse_path


# ============================================================
# PATHS
# ============================================================

SOURCE_DIR = Path(
    r"C:\Users\ganiy\OneDrive\Desktop\train-00"
)

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = PROJECT_DIR / "dataset"

TRAIN_IMAGES = DATASET_DIR / "images" / "train"
VAL_IMAGES = DATASET_DIR / "images" / "val"

TRAIN_LABELS = DATASET_DIR / "labels" / "train"
VAL_LABELS = DATASET_DIR / "labels" / "val"

MAX_FILES = 500

TRAIN_RATIO = 0.8

RANDOM_SEED = 42


# ============================================================
# YOLO CLASSES
# ============================================================

CLASS_NAMES = {
    "WALL": 0,
    "DOOR": 1,
    "WINDOW": 2,
}


# ============================================================
# FLOORPLANCAD SEMANTIC IDS
# ============================================================
#
# IMPORTANT:
# FloorPlanCAD contains multiple door/window subclasses.
# We combine all door subclasses into DOOR and all window
# subclasses into WINDOW.
#
# Wall is semantic ID 33 in the released dataset.
#
# For your downloaded release, the exact thing-class IDs
# should be verified from the dataset metadata before training.
#
# We therefore first PRINT the semantic IDs found in the
# dataset so we can verify them rather than silently guessing.
# ============================================================

WALL_SEMANTIC_IDS = {
    "33"
}


# ============================================================
# CREATE DIRECTORIES
# ============================================================

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
# GET SVG VIEWBOX
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
        float(x)
        for x in viewbox.replace(
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
# GET PATH POINTS
# ============================================================

def get_path_points(path_data):

    if not path_data:

        return []

    try:

        path = parse_path(
            path_data
        )

        if len(path) == 0:

            return []

        points = []

        # Start point
        points.append(
            (
                path.point(0).real,
                path.point(0).imag
            )
        )

        # Middle point
        points.append(
            (
                path.point(0.5).real,
                path.point(0.5).imag
            )
        )

        # End point
        points.append(
            (
                path.point(1).real,
                path.point(1).imag
            )
        )

        return points

    except Exception:

        return []


# ============================================================
# GET ELEMENT GEOMETRY
# ============================================================

def get_element_points(element):

    tag = element.tag.split(
        "}"
    )[-1].lower()


    # --------------------------------------------------------
    # PATH
    # --------------------------------------------------------

    if tag == "path":

        return get_path_points(
            element.attrib.get("d")
        )


    # --------------------------------------------------------
    # CIRCLE
    # --------------------------------------------------------

    if tag == "circle":

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

            return [
                (cx - r, cy - r),
                (cx + r, cy + r),
                (cx, cy)
            ]

        except Exception:

            return []


    # --------------------------------------------------------
    # ELLIPSE
    # --------------------------------------------------------

    if tag == "ellipse":

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

            return [
                (cx - rx, cy - ry),
                (cx + rx, cy + ry),
                (cx, cy)
            ]

        except Exception:

            return []


    return []


# ============================================================
# GET BOUNDING BOX
# ============================================================

def get_bbox(points):

    if not points:

        return None

    xs = [
        point[0]
        for point in points
    ]

    ys = [
        point[1]
        for point in points
    ]

    return (
        min(xs),
        min(ys),
        max(xs),
        max(ys)
    )


# ============================================================
# CLASS MAPPING
# ============================================================

def get_yolo_class(
    semantic_id
):

    semantic_id = str(
        semantic_id
    )

    # Wall
    if semantic_id in WALL_SEMANTIC_IDS:

        return 0

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # We are NOT going to guess door/window IDs.
    # The first run will print all semantic IDs.
    #
    # Once verified, we will add them here.
    # --------------------------------------------------------

    return None


# ============================================================
# CONVERT SVG
# ============================================================

def convert_svg(
    svg_file
):

    tree = ET.parse(
        svg_file
    )

    root = tree.getroot()

    view_min_x, view_min_y, view_width, view_height = (
        get_viewbox(root)
    )


    # --------------------------------------------------------
    # Group all SVG primitives belonging to the same object.
    #
    # KEY:
    #
    # (semantic-id, instance-id)
    # --------------------------------------------------------

    objects = defaultdict(list)


    # --------------------------------------------------------
    # Track semantic IDs for inspection.
    # --------------------------------------------------------

    semantic_ids = set()


    # --------------------------------------------------------
    # Process SVG primitives.
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

        semantic_id = str(
            semantic_id
        )

        if instance_id is None:

            instance_id = "-1"

        instance_id = str(
            instance_id
        )

        semantic_ids.add(
            semantic_id
        )


        points = get_element_points(
            element
        )

        if not points:

            continue


        key = (
            semantic_id,
            instance_id
        )

        objects[key].extend(
            points
        )


    return objects, semantic_ids, (
        view_min_x,
        view_min_y,
        view_width,
        view_height
    )


# ============================================================
# CREATE YOLO LABELS
# ============================================================

def create_labels(
    objects,
    viewbox
):

    view_min_x, view_min_y, view_width, view_height = viewbox

    labels = []


    for (
        semantic_id,
        instance_id
    ), points in objects.items():

        class_id = get_yolo_class(
            semantic_id
        )

        if class_id is None:

            continue


        # ----------------------------------------------------
        # Calculate ONE box for the entire instance.
        # ----------------------------------------------------

        box = get_bbox(
            points
        )

        if box is None:

            continue


        x1, y1, x2, y2 = box


        # ----------------------------------------------------
        # Translate viewBox origin.
        # ----------------------------------------------------

        x1 -= view_min_x
        x2 -= view_min_x

        y1 -= view_min_y
        y2 -= view_min_y


        # ----------------------------------------------------
        # Clamp coordinates.
        # ----------------------------------------------------

        x1 = max(
            0,
            min(
                view_width,
                x1
            )
        )

        y1 = max(
            0,
            min(
                view_height,
                y1
            )
        )

        x2 = max(
            0,
            min(
                view_width,
                x2
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


        box_width = (
            width / view_width
        )

        box_height = (
            height / view_height
        )


        # ----------------------------------------------------
        # Clamp normalized values.
        # ----------------------------------------------------

        center_x = max(
            0,
            min(
                1,
                center_x
            )
        )

        center_y = max(
            0,
            min(
                1,
                center_y
            )
        )

        box_width = max(
            0.001,
            min(
                1,
                box_width
            )
        )

        box_height = max(
            0.001,
            min(
                1,
                box_height
            )
        )


        labels.append(
            f"{class_id} "
            f"{center_x:.6f} "
            f"{center_y:.6f} "
            f"{box_width:.6f} "
            f"{box_height:.6f}"
        )


    return labels


# ============================================================
# DATA.YAML
# ============================================================

def create_yaml():

    yaml = """path: ../dataset

train: images/train
val: images/val

names:
  0: wall
  1: door
  2: window
"""

    file = (
        DATASET_DIR
        / "data.yaml"
    )

    file.write_text(
        yaml,
        encoding="utf-8"
    )

    print(
        f"Created: {file}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 60
    )

    print(
        "FloorPlanCAD -> YOLO Converter"
    )

    print(
        "=" * 60
    )


    if not SOURCE_DIR.exists():

        print(
            "ERROR: Dataset folder not found:"
        )

        print(
            SOURCE_DIR
        )

        return


    png_files = list(
        SOURCE_DIR.glob(
            "*.png"
        )
    )


    print()

    print(
        f"PNG files found: "
        f"{len(png_files)}"
    )


    if not png_files:

        print(
            "No PNG files found."
        )

        return


    random.seed(
        RANDOM_SEED
    )

    random.shuffle(
        png_files
    )


    if MAX_FILES:

        png_files = png_files[
            :MAX_FILES
        ]


    split = int(
        len(png_files)
        * TRAIN_RATIO
    )


    train_files = set(
        png_files[
            :split
        ]
    )

    val_files = set(
        png_files[
            split:
        ]
    )


    print(
        f"Processing: {len(png_files)}"
    )

    print(
        f"Training:   {len(train_files)}"
    )

    print(
        f"Validation: {len(val_files)}"
    )


    processed = 0
    skipped = 0


    class_counter = {
        "WALL": 0,
        "DOOR": 0,
        "WINDOW": 0
    }


    all_semantic_ids = set()


    # ========================================================
    # PROCESS IMAGES
    # ========================================================

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

            print(
                f"[SKIP] SVG missing: "
                f"{image_file.name}"
            )

            skipped += 1

            continue


        try:

            (
                objects,
                semantic_ids,
                viewbox
            ) = convert_svg(
                svg_file
            )

            all_semantic_ids.update(
                semantic_ids
            )


            labels = create_labels(
                objects,
                viewbox
            )


        except Exception as error:

            print(
                f"[SKIP] SVG error: "
                f"{image_file.name} "
                f"-> {error}"
            )

            skipped += 1

            continue


        if not labels:

            print(
                f"[SKIP] No supported annotations: "
                f"{image_file.name}"
            )

            skipped += 1

            continue


        # ----------------------------------------------------
        # TRAIN / VALIDATION
        # ----------------------------------------------------

        if image_file in train_files:

            image_dir = TRAIN_IMAGES
            label_dir = TRAIN_LABELS

        else:

            image_dir = VAL_IMAGES
            label_dir = VAL_LABELS


        # ----------------------------------------------------
        # Copy image
        # ----------------------------------------------------

        shutil.copy2(
            image_file,
            image_dir
            / image_file.name
        )


        # ----------------------------------------------------
        # Save labels
        # ----------------------------------------------------

        label_file = (
            label_dir
            / f"{image_file.stem}.txt"
        )


        label_file.write_text(
            "\n".join(labels),
            encoding="utf-8"
        )


        processed += 1


        # ----------------------------------------------------
        # Count classes
        # ----------------------------------------------------

        for label in labels:

            class_id = int(
                label.split()[0]
            )

            if class_id == 0:

                class_counter[
                    "WALL"
                ] += 1

            elif class_id == 1:

                class_counter[
                    "DOOR"
                ] += 1

            elif class_id == 2:

                class_counter[
                    "WINDOW"
                ] += 1


        if (
            index % 25 == 0
            or index == 1
        ):

            print(
                f"[{index}/{len(png_files)}] "
                f"{image_file.name}"
            )


    # ========================================================
    # YAML
    # ========================================================

    create_yaml()


    print()

    print(
        "=" * 60
    )

    print(
        "CONVERSION COMPLETE"
    )

    print(
        "=" * 60
    )


    print(
        f"Processed: {processed}"
    )

    print(
        f"Skipped:   {skipped}"
    )


    print()

    print(
        "Annotation counts:"
    )


    print(
        f"Walls:   "
        f"{class_counter['WALL']}"
    )

    print(
        f"Doors:   "
        f"{class_counter['DOOR']}"
    )

    print(
        f"Windows: "
        f"{class_counter['WINDOW']}"
    )


    print()

    print(
        "Semantic IDs found:"
    )

    print(
        sorted(
            all_semantic_ids,
            key=lambda x: int(x)
        )
    )


    print()

    print(
        "Dataset:"
    )

    print(
        DATASET_DIR
    )


if __name__ == "__main__":

    main()