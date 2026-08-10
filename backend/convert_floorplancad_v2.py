import re
import shutil
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict


# ============================================================
# CONFIGURATION
# ============================================================

SOURCE_DIR = Path(
    r"C:\Users\ganiy\OneDrive\Desktop\train-00"
)

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = PROJECT_DIR / "dataset_v3"

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
# NUMBER EXTRACTION
# ============================================================

def get_numbers(text):

    if not text:
        return []

    pattern = (
        r"[-+]?(?:"
        r"\d*\.\d+"
        r"|"
        r"\d+\.?"
        r")(?:[eE][-+]?\d+)?"
    )

    return [
        float(value)
        for value in re.findall(
            pattern,
            text
        )
    ]


# ============================================================
# SVG PATH POINT EXTRACTION
# ============================================================

def extract_path_points(path_data):

    if not path_data:
        return []

    tokens = re.findall(
        r"[MmLlHhVvCcSsQqTtAaZz]"
        r"|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?",
        path_data
    )

    points = []

    x = 0.0
    y = 0.0

    start_x = 0.0
    start_y = 0.0

    command = None

    i = 0

    while i < len(tokens):

        token = tokens[i]

        # ----------------------------------------------------
        # SVG command
        # ----------------------------------------------------

        if re.fullmatch(
            r"[A-Za-z]",
            token
        ):

            command = token

            if command.upper() == "Z":

                x = start_x
                y = start_y

            i += 1

            continue

        if command is None:

            i += 1

            continue

        # ----------------------------------------------------
        # MOVE
        # ----------------------------------------------------

        if command in ("M", "m"):

            if i + 1 >= len(tokens):
                break

            nx = float(tokens[i])
            ny = float(tokens[i + 1])

            if command == "M":

                x = nx
                y = ny

            else:

                x += nx
                y += ny

            start_x = x
            start_y = y

            points.append((x, y))

            i += 2

            command = (
                "L" if command == "M"
                else "l"
            )

            continue

        # ----------------------------------------------------
        # LINE
        # ----------------------------------------------------

        if command in ("L", "l"):

            if i + 1 >= len(tokens):
                break

            nx = float(tokens[i])
            ny = float(tokens[i + 1])

            if command == "L":

                x = nx
                y = ny

            else:

                x += nx
                y += ny

            points.append((x, y))

            i += 2

            continue

        # ----------------------------------------------------
        # HORIZONTAL
        # ----------------------------------------------------

        if command == "H":

            x = float(tokens[i])

            points.append((x, y))

            i += 1

            continue

        if command == "h":

            x += float(tokens[i])

            points.append((x, y))

            i += 1

            continue

        # ----------------------------------------------------
        # VERTICAL
        # ----------------------------------------------------

        if command == "V":

            y = float(tokens[i])

            points.append((x, y))

            i += 1

            continue

        if command == "v":

            y += float(tokens[i])

            points.append((x, y))

            i += 1

            continue

        # ----------------------------------------------------
        # CUBIC / QUADRATIC CURVES
        # ----------------------------------------------------

        if command.upper() in (
            "C",
            "S",
            "Q",
            "T",
        ):

            counts = {
                "C": 6,
                "c": 6,
                "S": 4,
                "s": 4,
                "Q": 4,
                "q": 4,
                "T": 2,
                "t": 2,
            }

            count = counts[command]

            values = []

            for _ in range(count):

                if i >= len(tokens):
                    break

                if re.fullmatch(
                    r"[A-Za-z]",
                    tokens[i]
                ):
                    break

                values.append(
                    float(tokens[i])
                )

                i += 1

            # Add all coordinate pairs to bbox.
            for j in range(
                0,
                len(values) - 1,
                2
            ):

                px = values[j]
                py = values[j + 1]

                if command.islower():

                    px += x
                    py += y

                points.append(
                    (px, py)
                )

            if len(values) >= 2:

                if command.islower():

                    x += values[-2]
                    y += values[-1]

                else:

                    x = values[-2]
                    y = values[-1]

                points.append((x, y))

            continue

        # ----------------------------------------------------
        # ARC
        # ----------------------------------------------------

        if command.upper() == "A":

            values = []

            for _ in range(7):

                if i >= len(tokens):
                    break

                if re.fullmatch(
                    r"[A-Za-z]",
                    tokens[i]
                ):
                    break

                values.append(
                    float(tokens[i])
                )

                i += 1

            if len(values) == 7:

                nx = values[5]
                ny = values[6]

                if command.islower():

                    x += nx
                    y += ny

                else:

                    x = nx
                    y = ny

                points.append(
                    (x, y)
                )

            continue

        i += 1

    return points


# ============================================================
# BOUNDING BOX
# ============================================================

def bbox(points):

    if not points:
        return None

    xs = [
        p[0]
        for p in points
    ]

    ys = [
        p[1]
        for p in points
    ]

    return (
        min(xs),
        min(ys),
        max(xs),
        max(ys),
    )


# ============================================================
# LAYER DETECTION
# ============================================================

def detect_layer(element):

    element_id = element.attrib.get(
        "id",
        ""
    ).upper()

    label = element.attrib.get(
        "{http://www.inkscape.org/namespaces/inkscape}label",
        ""
    ).upper()

    text = (
        element_id
        + " "
        + label
    )

    if "WALL" in text:
        return "WALL"

    if "WINDOW" in text:
        return "WINDOW"

    if "DOOR" in text:
        return "DOOR"

    return None


# ============================================================
# SEMANTIC ID
# ============================================================

def semantic_class(element, layer):

    semantic_id = element.attrib.get(
        "semantic-id"
    )

    if semantic_id:

        semantic_id = semantic_id.strip()

        if semantic_id == "1":
            return "WALL"

        if semantic_id in ("2",):
            return "DOOR"

        if semantic_id in ("3", "4"):
            return "WINDOW"

    return layer


# ============================================================
# INSTANCE ID
# ============================================================

def get_instance_id(element):

    return element.attrib.get(
        "instance-id",
        "-1"
    )


# ============================================================
# CONVERT SVG
# ============================================================

def convert_svg(svg_file):

    tree = ET.parse(svg_file)

    root = tree.getroot()

    view_box = root.attrib.get(
        "viewBox"
    )

    values = get_numbers(
        view_box
    )

    if len(values) != 4:

        raise ValueError(
            "Invalid SVG viewBox"
        )

    min_x = values[0]
    min_y = values[1]

    svg_width = values[2]
    svg_height = values[3]

    # --------------------------------------------------------
    # Group geometry by:
    #
    # semantic class + instance ID
    # --------------------------------------------------------

    objects = defaultdict(list)

    current_layer = None

    def walk(
        element,
        inherited_layer=None
    ):

        nonlocal current_layer

        layer = inherited_layer

        tag = element.tag.split(
            "}"
        )[-1].lower()

        # ----------------------------------------------------
        # Detect layer
        # ----------------------------------------------------

        if tag == "g":

            detected = detect_layer(
                element
            )

            if detected:

                layer = detected

        # ----------------------------------------------------
        # Process path
        # ----------------------------------------------------

        if (
            tag == "path"
            and layer in CLASS_NAMES
        ):

            path_data = element.attrib.get(
                "d"
            )

            points = extract_path_points(
                path_data
            )

            if points:

                object_class = semantic_class(
                    element,
                    layer
                )

                instance_id = get_instance_id(
                    element
                )

                # Ignore unknown classes.
                if object_class in CLASS_NAMES:

                    key = (
                        object_class,
                        instance_id
                    )

                    objects[key].extend(
                        points
                    )

        # ----------------------------------------------------
        # Children
        # ----------------------------------------------------

        for child in element:

            walk(
                child,
                layer
            )

    walk(root)

    annotations = []

    # --------------------------------------------------------
    # Convert each INSTANCE into one bbox
    # --------------------------------------------------------

    for (
        object_class,
        instance_id
    ), points in objects.items():

        # Ignore unassigned geometry.
        #
        # -1 can represent generic geometry that isn't
        # associated with an object instance.
        #
        # We still keep walls if they use -1 because
        # walls may be represented as line geometry.

        if (
            instance_id == "-1"
            and object_class != "WALL"
        ):
            continue

        box = bbox(points)

        if not box:
            continue

        x1, y1, x2, y2 = box

        # Convert from viewBox coordinates.
        x1 -= min_x
        x2 -= min_x

        y1 -= min_y
        y2 -= min_y

        # Clamp.
        x1 = max(
            0,
            min(svg_width, x1)
        )

        y1 = max(
            0,
            min(svg_height, y1)
        )

        x2 = max(
            0,
            min(svg_width, x2)
        )

        y2 = max(
            0,
            min(svg_height, y2)
        )

        width = x2 - x1
        height = y2 - y1

        if width <= 0 or height <= 0:
            continue

        center_x = (
            (x1 + x2) / 2
        ) / svg_width

        center_y = (
            (y1 + y2) / 2
        ) / svg_height

        norm_width = (
            width / svg_width
        )

        norm_height = (
            height / svg_height
        )

        class_id = CLASS_NAMES[
            object_class
        ]

        annotations.append(
            f"{class_id} "
            f"{center_x:.6f} "
            f"{center_y:.6f} "
            f"{norm_width:.6f} "
            f"{norm_height:.6f}"
        )

    return annotations


# ============================================================
# DATA YAML
# ============================================================

def create_yaml():

    content = """path: ../dataset_v3

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
        content,
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
    print("FloorPlanCAD -> YOLO V3")
    print("INSTANCE-BASED CONVERTER")
    print("=" * 60)

    png_files = list(
        SOURCE_DIR.glob("*.png")
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

    if MAX_FILES:

        png_files = png_files[
            :MAX_FILES
        ]

    split = int(
        len(png_files)
        * TRAIN_RATIO
    )

    train_files = set(
        png_files[:split]
    )

    processed = 0
    skipped = 0

    counters = {
        "WALL": 0,
        "DOOR": 0,
        "WINDOW": 0,
    }

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

        for label in labels:

            class_id = int(
                label.split()[0]
            )

            if class_id == 0:

                counters["WALL"] += 1

            elif class_id == 1:

                counters["DOOR"] += 1

            elif class_id == 2:

                counters["WINDOW"] += 1

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
    print("V3 CONVERSION COMPLETE")
    print("=" * 60)

    print(
        f"Processed: {processed}"
    )

    print(
        f"Skipped:   {skipped}"
    )

    print()
    print(
        f"Walls:   {counters['WALL']}"
    )

    print(
        f"Doors:   {counters['DOOR']}"
    )

    print(
        f"Windows: {counters['WINDOW']}"
    )


if __name__ == "__main__":
    main()