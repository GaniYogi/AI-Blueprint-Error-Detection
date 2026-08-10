import xml.etree.ElementTree as ET
from pathlib import Path
import cv2
import numpy as np
from svgpathtools import parse_path


SVG_FILE = Path(
    r"C:\Users\ganiy\OneDrive\Desktop\train-00\0000-0002.svg"
)

OUTPUT_FILE = Path(
    r"C:\Users\ganiy\OneDrive\Desktop\semantic_debug.png"
)


# Different colors for different semantic IDs
COLORS = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (255, 0, 255),
    (0, 255, 255),
    (128, 0, 255),
    (255, 128, 0),
    (128, 255, 0),
    (0, 128, 255),
]


def main():

    tree = ET.parse(SVG_FILE)
    root = tree.getroot()

    canvas = np.zeros(
        (1000, 1000, 3),
        dtype=np.uint8
    )

    semantic_ids = sorted(
        {
            e.attrib.get("semantic-id")
            for e in root.iter()
            if e.attrib.get("semantic-id")
        },
        key=int
    )

    color_map = {}

    for index, semantic_id in enumerate(
        semantic_ids
    ):
        color_map[semantic_id] = COLORS[
            index % len(COLORS)
        ]

    for element in root.iter():

        semantic_id = element.attrib.get(
            "semantic-id"
        )

        if semantic_id is None:
            continue

        color = color_map[
            semantic_id
        ]

        tag = element.tag.split(
            "}"
        )[-1].lower()

        points = []

        try:

            if tag == "path":

                path = parse_path(
                    element.attrib.get("d", "")
                )

                points = [
                    path.point(0),
                    path.point(0.5),
                    path.point(1)
                ]

            elif tag == "circle":

                cx = float(
                    element.attrib["cx"]
                )

                cy = float(
                    element.attrib["cy"]
                )

                r = float(
                    element.attrib["r"]
                )

                points = [
                    complex(cx - r, cy - r),
                    complex(cx + r, cy + r)
                ]

            elif tag == "ellipse":

                cx = float(
                    element.attrib["cx"]
                )

                cy = float(
                    element.attrib["cy"]
                )

                rx = float(
                    element.attrib["rx"]
                )

                ry = float(
                    element.attrib["ry"]
                )

                points = [
                    complex(cx - rx, cy - ry),
                    complex(cx + rx, cy + ry)
                ]

        except Exception:
            continue

        for point in points:

            x = int(point.real * 10)
            y = int(point.imag * 10)

            if (
                0 <= x < 1000
                and 0 <= y < 1000
            ):

                cv2.circle(
                    canvas,
                    (x, y),
                    3,
                    color,
                    -1
                )

    # Add semantic ID legend
    y = 25

    for semantic_id in semantic_ids:

        color = color_map[
            semantic_id
        ]

        cv2.putText(
            canvas,
            f"ID {semantic_id}",
            (10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )

        y += 25

    cv2.imwrite(
        str(OUTPUT_FILE),
        canvas
    )

    print(
        "Created:"
    )

    print(
        OUTPUT_FILE
    )

    print()

    print(
        "Semantic IDs:"
    )

    print(
        semantic_ids
    )


if __name__ == "__main__":
    main()