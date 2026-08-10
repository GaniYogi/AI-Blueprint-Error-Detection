import os
from typing import Dict, Any, List, Tuple

# OpenCV
HAS_CV2 = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    pass


# EasyOCR
HAS_EASYOCR = False

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    pass


# YOLO
HAS_YOLO = False

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    pass


class BlueprintAnalysisEngine:

    def __init__(
        self,
        upload_dir: str,
        models_dir: str
    ):
        self.upload_dir = upload_dir
        self.models_dir = models_dir

        self.reader = None
        self.yolo_model = None

        # -------------------------------------------------
        # Load EasyOCR
        # -------------------------------------------------

        if HAS_EASYOCR:

            try:
                print("Loading EasyOCR...")

                self.reader = easyocr.Reader(
                    ['en'],
                    gpu=False
                )

                print("EasyOCR loaded successfully.")

            except Exception as e:

                print(
                    f"EasyOCR initialization failed: {e}"
                )

                self.reader = None

        else:

            print(
                "EasyOCR is not installed."
            )

        # -------------------------------------------------
        # Load YOLO
        # -------------------------------------------------

        if HAS_YOLO:

            try:

                weights_path = os.path.join(
                    models_dir,
                    "best.pt"
                )

                if os.path.exists(weights_path):

                    print(
                        f"Loading YOLO model: {weights_path}"
                    )

                    self.yolo_model = YOLO(
                        weights_path
                    )

                    print(
                        "YOLO model loaded successfully."
                    )

                    print(
                        f"YOLO classes: {self.yolo_model.names}"
                    )

                else:

                    print(
                        f"YOLO weights not found: {weights_path}"
                    )

            except Exception as e:

                print(
                    f"YOLO model initialization failed: {e}"
                )

        else:

            print(
                "Ultralytics YOLO is not installed."
            )


    # =====================================================
    # MAIN ANALYSIS
    # =====================================================

    def run_analysis(
        self,
        file_path: str,
        rules: Dict[str, float]
    ) -> Dict[str, Any]:

        """
        Run complete blueprint analysis.

        Pipeline:

        Blueprint
             ↓
        Image metadata
             ↓
        YOLO object detection
             ↓
        EasyOCR text detection
             ↓
        Error analysis
             ↓
        Compliance analysis
             ↓
        Final result
        """

        # -------------------------------------------------
        # Check file
        # -------------------------------------------------

        if not os.path.exists(file_path):

            raise FileNotFoundError(
                f"Blueprint file not found: {file_path}"
            )


        # -------------------------------------------------
        # Image dimensions
        # -------------------------------------------------

        width = 1200
        height = 800

        if HAS_CV2:

            try:

                image = cv2.imread(
                    file_path
                )

                if image is not None:

                    height, width = image.shape[:2]

            except Exception as e:

                print(
                    f"Failed to read image: {e}"
                )


        filename = os.path.basename(
            file_path
        )


        # -------------------------------------------------
        # 1. YOLO OBJECT DETECTION (+ OpenCV fallback)
        # -------------------------------------------------

        detected_objects = self._detect_objects(
            file_path,
            width,
            height
        )


        # -------------------------------------------------
        # 2. OCR
        # -------------------------------------------------

        ocr_results = self._run_ocr(
            file_path,
            width,
            height
        )


        # -------------------------------------------------
        # 2.5  OCR-based room enrichment
        #      When YOLO/OpenCV found ≤1 object, use the
        #      room-name text detected by EasyOCR to create
        #      accurate per-room bounding boxes.
        # -------------------------------------------------

        if len(detected_objects) <= 1 and ocr_results:
            ocr_rooms = self._detect_rooms_from_ocr(
                ocr_results, width, height
            )
            if len(ocr_rooms) > len(detected_objects):
                # Keep OpenCV walls but replace the single-blob room
                ocr_walls = self._detect_walls_opencv(
                    file_path, width, height
                )
                detected_objects = ocr_rooms + ocr_walls
                print(
                    f"OCR enrichment: {len(ocr_rooms)} rooms, "
                    f"{len(ocr_walls)} walls."
                )


        # -------------------------------------------------
        # 3. ERROR DETECTION
        # -------------------------------------------------

        errors = self._detect_errors(
            detected_objects,
            ocr_results,
            width,
            height
        )


        # -------------------------------------------------
        # 4. COMPLIANCE
        # -------------------------------------------------

        (
            compliance_checks,
            compliance_score,
            violation_count
        ) = self._check_compliance(

            detected_objects,
            ocr_results,
            errors,
            rules
        )


        # -------------------------------------------------
        # 5. FINAL RESULT
        # -------------------------------------------------

        results = {

            "image_metadata": {

                "width": width,

                "height": height,

                "filename": filename

            },

            "detected_objects":
                detected_objects,

            "ocr_results":
                ocr_results,

            "errors":
                errors,

            "compliance_checks":
                compliance_checks,

            "compliance_score":
                round(
                    compliance_score,
                    1
                ),

            "total_violations":
                violation_count,

            "total_errors":
                len(errors),

            "risk_assessment":
                self._evaluate_risk(
                    compliance_score,
                    len(errors)
                ),

            "recommendations":
                self._generate_recommendations(
                    errors,
                    compliance_checks
                )

        }

        return results


    # =====================================================
    # YOLO OBJECT DETECTION
    # =====================================================

    def _detect_objects(
        self,
        file_path: str,
        width: int,
        height: int
    ) -> List[Dict[str, Any]]:
        """
        Detect blueprint elements using YOLO.
        Falls back to OpenCV contour-based detection when YOLO
        returns no results (e.g. model not trained on this style).
        """

        detected = []

        # --------------------------------------------------
        # Try YOLO first
        # --------------------------------------------------

        if self.yolo_model is not None:
            try:
                results = self.yolo_model.predict(
                    source=file_path,
                    conf=0.25,
                    verbose=False
                )

                for result in results:
                    if result.boxes is None:
                        continue
                    for box in result.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        label = self.yolo_model.names[cls]

                        detected.append({
                            "id": f"obj_{len(detected) + 1}",
                            "label": str(label),
                            "bbox": [
                                float(x1),
                                float(y1),
                                float(x2 - x1),
                                float(y2 - y1)
                            ],
                            "confidence": round(conf, 2)
                        })

            except Exception as e:
                print(f"YOLO inference failed: {e}")

        print(f"YOLO detected {len(detected)} objects.")

        # --------------------------------------------------
        # Fallback: OpenCV contour-based detection
        # --------------------------------------------------

        if len(detected) == 0 and HAS_CV2:
            print("YOLO found nothing — running OpenCV contour fallback.")
            detected = self._detect_objects_opencv(file_path, width, height)

        return detected


    def _detect_objects_opencv(
        self,
        file_path: str,
        width: int,
        height: int
    ) -> List[Dict[str, Any]]:
        """
        OpenCV-based fallback detector.

        Key insight: floor plan rooms share door openings, so a plain
        flood-fill can't separate them.  We first DILATE the walls
        heavily to seal door gaps, THEN flood-fill from corners to
        remove the exterior, leaving individual room blobs.
        """

        import cv2
        import numpy as np

        detected = []

        try:
            img = cv2.imread(file_path)
            if img is None:
                return detected

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape

            # --------------------------------------------------
            # 1. ROOM DETECTION  (dilation-seal + flood-fill)
            # --------------------------------------------------

            # Threshold: walls → 255, open space → 0
            _, wall_mask = cv2.threshold(
                gray, 180, 255, cv2.THRESH_BINARY_INV
            )

            # Dilate walls heavily to seal door/opening gaps.
            # gap_size ≈ 3–4 % of image; adjust down if rooms merge.
            gap_size = max(20, int(min(w, h) * 0.035))
            kernel_gap = np.ones((gap_size, gap_size), np.uint8)
            sealed = cv2.dilate(wall_mask, kernel_gap, iterations=1)

            # Invert: now open-space pixels are white
            inv = cv2.bitwise_not(sealed)

            # Flood-fill from all four corners to mark exterior
            flooded = inv.copy()
            fill_mask = np.zeros((h + 2, w + 2), np.uint8)
            for pt in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
                if flooded[pt[1], pt[0]] == 255:
                    cv2.floodFill(flooded, fill_mask, pt, 0)

            # What remains = interior rooms
            room_mask = flooded

            # Small close to remove noise
            k_small = np.ones((5, 5), np.uint8)
            room_mask = cv2.morphologyEx(
                room_mask, cv2.MORPH_CLOSE, k_small
            )

            contours, _ = cv2.findContours(
                room_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            img_area = w * h
            room_count = 0

            for contour in sorted(
                contours, key=cv2.contourArea, reverse=True
            ):
                area = cv2.contourArea(contour)
                # Must be between 0.3 % and 60 % of image
                if area < img_area * 0.003 or area > img_area * 0.60:
                    continue

                x, y, bw, bh = cv2.boundingRect(contour)
                rect_area = bw * bh
                if rect_area == 0:
                    continue

                fill_ratio = area / rect_area
                aspect    = max(bw, bh) / max(min(bw, bh), 1)

                if fill_ratio < 0.25 or aspect > 10:
                    continue

                room_count += 1
                detected.append({
                    'id':         f'room_{room_count}',
                    'label':      'room',
                    'name':       f'Space {room_count}',
                    'bbox':       [float(x), float(y),
                                   float(bw), float(bh)],
                    'confidence': round(
                        min(0.5 + fill_ratio * 0.4, 0.95), 2
                    ),
                })

            print(f'OpenCV seal+flood found {room_count} rooms.')

            # --------------------------------------------------
            # 2. WALL SEGMENTS  (Hough lines)
            # --------------------------------------------------

            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            edges   = cv2.Canny(blurred, 30, 120)

            lines = cv2.HoughLinesP(
                edges,
                rho=1,
                theta=np.pi / 180,
                threshold=60,
                minLineLength=int(min(w, h) * 0.04),
                maxLineGap=10,
            )

            wall_count = 0
            if lines is not None:
                merged: List[Tuple] = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    length = ((x2-x1)**2 + (y2-y1)**2) ** 0.5
                    if length < min(w, h) * 0.03:
                        continue
                    is_dup = any(
                        abs(x1-mx1)+abs(y1-my1) < 25 and
                        abs(x2-mx2)+abs(y2-my2) < 25
                        for mx1, my1, mx2, my2 in merged
                    )
                    if not is_dup:
                        merged.append((x1, y1, x2, y2))

                for x1, y1, x2, y2 in merged[:35]:
                    bx  = float(min(x1, x2))
                    by  = float(min(y1, y2))
                    bw2 = float(max(abs(x2-x1), 5))
                    bh2 = float(max(abs(y2-y1), 5))
                    wall_count += 1
                    detected.append({
                        'id':         f'wall_{wall_count}',
                        'label':      'wall',
                        'bbox':       [bx, by, bw2, bh2],
                        'confidence': 0.78,
                    })

            print(f'OpenCV Hough found {wall_count} wall segments.')

        except Exception as e:
            print(f'OpenCV fallback detection failed: {e}')

        return detected



    # =====================================================
    # OCR-BASED ROOM DETECTION
    # =====================================================

    def _detect_rooms_from_ocr(
        self,
        ocr_results: List[Dict[str, Any]],
        width: int,
        height: int
    ) -> List[Dict[str, Any]]:
        """
        Build room detections from EasyOCR text results.
        Finds text entries that match room-name keywords,
        then estimates each room's bounding box from the
        text position and any dimension string in the text.
        """

        import re

        ROOM_KEYWORDS = [
            'bedroom', 'kitchen', 'living', 'dining',
            'toilet', 'bathroom', 'bath', 'verandah',
            'staircase', 'garage', 'utility', 'pantry',
            'hall', 'corridor', 'lobby', 'study', 'office',
            'store', 'laundry', 'porch', 'balcony', 'room',
        ]

        rooms = []
        used_positions: List[Tuple] = []

        for ocr in ocr_results:
            text_raw = ocr.get('text', '')
            text_low = text_raw.lower().strip()
            bbox = ocr.get('bbox')          # [x, y, w, h]

            if not bbox or not text_low:
                continue

            # Must contain a room keyword
            if not any(kw in text_low for kw in ROOM_KEYWORDS):
                continue

            x, y, w, h = [float(v) for v in bbox]
            cx, cy = x + w / 2, y + h / 2

            # Deduplicate: skip if too close to an existing room
            is_dup = False
            for ux, uy in used_positions:
                if abs(cx - ux) < 80 and abs(cy - uy) < 80:
                    is_dup = True
                    break
            if is_dup:
                continue
            used_positions.append((cx, cy))

            # Try to extract dimensions, e.g. "12'0 X 10'0" or "3.6 x 3.0"
            rw, rh = w + 60, h + 60   # default: expand text box a little

            dim_match = re.search(
                r"(\d+)['\u2019]?\s*(?:\d+\"?)?\s*[xX\u00d7]\s*(\d+)",
                text_raw
            )
            if dim_match:
                try:
                    ft_w = int(dim_match.group(1))
                    ft_h = int(dim_match.group(2))
                    # Rough scale: assume total interior ~30 ft wide
                    scale = (width * 0.75) / 30.0
                    rw = min(ft_w * scale, width * 0.45)
                    rh = min(ft_h * scale, height * 0.45)
                except Exception:
                    pass

            rx = max(0.0, cx - rw / 2)
            ry = max(0.0, cy - rh / 2)
            rw = min(rw, width - rx)
            rh = min(rh, height - ry)

            # Clean up room name (take first meaningful words)
            name_parts = text_raw.strip().split()
            name = ' '.join(name_parts[:4])

            rooms.append({
                'id': f'room_{len(rooms) + 1}',
                'label': 'room',
                'name': name,
                'bbox': [rx, ry, rw, rh],
                'confidence': round(float(ocr.get('confidence', 0.85)), 2),
            })

        print(f"OCR room detection found {len(rooms)} rooms.")
        return rooms


    def _detect_walls_opencv(
        self,
        file_path: str,
        width: int,
        height: int
    ) -> List[Dict[str, Any]]:
        """
        Detect wall line segments using Hough transform only.
        Used as a standalone complement to OCR-based room detection.
        """

        if not HAS_CV2:
            return []

        import cv2
        import numpy as np

        walls: List[Dict[str, Any]] = []

        try:
            img = cv2.imread(file_path)
            if img is None:
                return walls

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape

            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            edges = cv2.Canny(blurred, 30, 120)

            lines = cv2.HoughLinesP(
                edges,
                rho=1,
                theta=np.pi / 180,
                threshold=60,
                minLineLength=int(min(w, h) * 0.04),
                maxLineGap=10
            )

            if lines is None:
                return walls

            merged: List[Tuple] = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                if length < min(w, h) * 0.03:
                    continue
                is_dup = any(
                    abs(x1 - mx1) + abs(y1 - my1) < 25 and
                    abs(x2 - mx2) + abs(y2 - my2) < 25
                    for mx1, my1, mx2, my2 in merged
                )
                if not is_dup:
                    merged.append((x1, y1, x2, y2))

            for idx, (x1, y1, x2, y2) in enumerate(merged[:35]):
                bx = float(min(x1, x2))
                by = float(min(y1, y2))
                bw = float(max(abs(x2 - x1), 5))
                bh = float(max(abs(y2 - y1), 5))
                walls.append({
                    'id': f'wall_{idx + 1}',
                    'label': 'wall',
                    'bbox': [bx, by, bw, bh],
                    'confidence': 0.78,
                })

            print(f"_detect_walls_opencv found {len(walls)} walls.")

        except Exception as e:
            print(f"_detect_walls_opencv failed: {e}")

        return walls


    # =====================================================
    # OCR
    # =====================================================

    def _run_ocr(
        self,
        file_path: str,
        width: int,
        height: int
    ) -> List[Dict[str, Any]]:

        """
        Extract text from blueprint using EasyOCR.

        IMPORTANT:
        If OCR fails, an empty list is returned.

        No fake/simulated OCR data is generated.
        """

        if self.reader is None:

            print(
                "EasyOCR is not available."
            )

            return []


        try:

            results = self.reader.readtext(
                file_path
            )

            ocr_texts = []


            for idx, result in enumerate(
                results
            ):

                # EasyOCR normally returns:
                #
                # [bbox, text, confidence]

                if len(result) != 3:

                    continue


                bbox, text, conf = result


                xs = [

                    point[0]

                    for point in bbox

                ]

                ys = [

                    point[1]

                    for point in bbox

                ]


                x = min(xs)

                y = min(ys)

                w = max(xs) - x

                h = max(ys) - y


                ocr_texts.append({

                    "id":
                        f"ocr_{idx + 1}",

                    "text":
                        str(text),

                    "bbox": [

                        int(x),

                        int(y),

                        int(w),

                        int(h)

                    ],

                    "confidence":
                        round(
                            float(conf),
                            2
                        )

                })


            print(
                f"OCR detected {len(ocr_texts)} text items."
            )


            return ocr_texts


        except Exception as e:

            print(
                f"EasyOCR inference failed: {e}"
            )

            return []


    # =====================================================
    # ERROR DETECTION
    # =====================================================

    def _detect_errors(
        self,
        detected_objects: List[Dict[str, Any]],
        ocr_results: List[Dict[str, Any]],
        width: int,
        height: int
    ) -> List[Dict[str, Any]]:
        """
        Detect blueprint problems from YOLO or OpenCV detection results.
        """

        errors = []

        # Separate detected classes (handles both YOLO and OpenCV labels)
        walls   = [o for o in detected_objects if o["label"].lower() in ("wall",)]
        doors   = [o for o in detected_objects if o["label"].lower() in ("door",)]
        windows = [o for o in detected_objects if o["label"].lower() in ("window",)]
        rooms   = [o for o in detected_objects if o["label"].lower() in ("room",)]

        # Low-confidence detections
        for obj in detected_objects:
            confidence = float(obj.get("confidence", 0))
            if confidence < 0.35:
                errors.append({
                    "id": f"err_{len(errors) + 1}",
                    "type": "low_confidence_detection",
                    "description": (
                        f"Low-confidence {obj['label']} detection "
                        f"({confidence:.2f})."
                    ),
                    "bbox": obj["bbox"],
                    "severity": "Low",
                    "suggestion": (
                        "Review this area manually or upload a higher-resolution blueprint."
                    )
                })

        # No structural elements detected at all
        if len(walls) == 0 and len(rooms) == 0:
            errors.append({
                "id": "err_no_walls",
                "type": "missing_wall_detection",
                "description": (
                    "No wall or room elements were detected in the blueprint."
                ),
                "bbox": None,
                "severity": "High",
                "suggestion": (
                    "Verify whether walls are clearly visible. Upload a cleaner, "
                    "higher-contrast version of the blueprint."
                )
            })

        # No doors detected (only flag if YOLO was available and found nothing)
        if len(doors) == 0 and len(rooms) > 0:
            errors.append({
                "id": "err_no_doors",
                "type": "missing_door_detection",
                "description": (
                    "No door elements were identified. "
                    "Doors may be present but not detected by the model."
                ),
                "bbox": None,
                "severity": "Medium",
                "suggestion": (
                    "Verify door locations manually. "
                    "The detection model may need additional training data."
                )
            })

        # No windows detected
        if len(windows) == 0 and len(rooms) > 0:
            errors.append({
                "id": "err_no_windows",
                "type": "missing_window_detection",
                "description": (
                    "No window elements were identified. "
                    "Ensure windows are marked clearly on the plan."
                ),
                "bbox": None,
                "severity": "Medium",
                "suggestion": "Verify window locations manually."
            })

        # Too few rooms for a residential layout
        if len(rooms) > 0 and len(rooms) < 2:
            errors.append({
                "id": "err_too_few_rooms",
                "type": "insufficient_habitable_spaces",
                "description": (
                    f"Only {len(rooms)} habitable space(s) detected. "
                    "A minimum residential layout requires at least 2 distinct rooms."
                ),
                "bbox": rooms[0]["bbox"] if rooms else None,
                "severity": "High",
                "suggestion": (
                    "Ensure all rooms are clearly enclosed with solid walls."
                )
            })

        # Overlapping room bounding boxes (potential drafting error)
        for i, r1 in enumerate(rooms):
            for j, r2 in enumerate(rooms):
                if i >= j:
                    continue
                x1, y1, w1, h1 = r1["bbox"]
                x2, y2, w2, h2 = r2["bbox"]
                ox = max(0, min(x1+w1, x2+w2) - max(x1, x2))
                oy = max(0, min(y1+h1, y2+h2) - max(y1, y2))
                overlap = ox * oy
                area1 = w1 * h1
                if area1 > 0 and overlap / area1 > 0.4:
                    errors.append({
                        "id": f"err_overlap_{i}_{j}",
                        "type": "overlapping_room_boundaries",
                        "description": (
                            f"Space {i+1} and Space {j+1} significantly overlap — "
                            "possible drafting error or unclear wall boundary."
                        ),
                        "bbox": r1["bbox"],
                        "severity": "Medium",
                        "suggestion": (
                            "Review the boundary between these two spaces. "
                            "Ensure wall lines are complete and non-overlapping."
                        )
                    })

        return errors



    # =====================================================
    # COMPLIANCE
    # =====================================================

    def _check_compliance(
        self,
        detected_objects: List[Dict[str, Any]],
        ocr_results: List[Dict[str, Any]],
        errors: List[Dict[str, Any]],
        rules: Dict[str, float]
    ) -> Tuple[
        List[Dict[str, Any]],
        float,
        int
    ]:

        """
        Generate compliance checks from actual
        detection results.

        No hard-coded bedroom/door dimensions
        are used.
        """

        checks = []


        # -------------------------------------------------
        # Count objects
        # -------------------------------------------------

        walls = sum(
            1 for obj in detected_objects
            if obj["label"].lower() in ("wall",)
        )

        doors = sum(
            1 for obj in detected_objects
            if obj["label"].lower() in ("door",)
        )

        windows = sum(
            1 for obj in detected_objects
            if obj["label"].lower() in ("window",)
        )

        rooms = sum(
            1 for obj in detected_objects
            if obj["label"].lower() in ("room",)
        )

        # Treat detected rooms as having walls present
        structural_ok = walls > 0 or rooms > 0

        # -------------------------------------------------
        # Wall check
        # -------------------------------------------------

        wall_status = "PASS" if structural_ok else "REVIEW"

        checks.append({
            "rule_key": "wall_detection",
            "name": "Wall Detection",
            "category": "structure",
            "description": "Check whether wall/room elements were detected.",
            "threshold": "At least 1 wall or room",
            "actual": f"{walls} walls, {rooms} rooms detected",
            "status": wall_status,
            "severity": "High",
            "suggestion": (
                "Verify wall elements manually if they were not detected."
            )
        })


        # -------------------------------------------------
        # Door check
        # -------------------------------------------------

        door_status = (
            "PASS"
            if doors > 0
            else "REVIEW"
        )


        checks.append({

            "rule_key":
                "door_detection",

            "name":
                "Door Detection",

            "category":
                "accessibility",

            "description":
                "Check whether door elements were detected.",

            "threshold":
                "At least 1 door",

            "actual":
                f"{doors} doors detected",

            "status":
                door_status,

            "severity":
                "Medium",

            "suggestion":
                (
                    "Verify door locations manually."
                )

        })


        # -------------------------------------------------
        # Window check
        # -------------------------------------------------

        window_status = (
            "PASS"
            if windows > 0
            else "REVIEW"
        )


        checks.append({

            "rule_key":
                "window_detection",

            "name":
                "Window Detection",

            "category":
                "ventilation",

            "description":
                "Check whether window elements were detected.",

            "threshold":
                "At least 1 window",

            "actual":
                f"{windows} windows detected",

            "status":
                window_status,

            "severity":
                "Medium",

            "suggestion":
                (
                    "Verify window locations manually."
                )

        })


        # -------------------------------------------------
        # OCR check
        # -------------------------------------------------

        checks.append({

            "rule_key":
                "ocr_detection",

            "name":
                "Blueprint Text Detection",

            "category":
                "documentation",

            "description":
                "Check whether text annotations were detected.",

            "threshold":
                "Text detection available",

            "actual":
                f"{len(ocr_results)} text items detected",

            "status":
                (
                    "PASS"
                    if len(ocr_results) > 0
                    else "REVIEW"
                ),

            "severity":
                "Low",

            "suggestion":
                (
                    "Verify dimensions and room labels "
                    "manually if OCR does not detect them."
                )

        })


        # -------------------------------------------------
        # Calculate score
        # -------------------------------------------------

        score = 100.0


        for error in errors:

            severity = error.get(
                "severity",
                "Low"
            )


            if severity == "Critical":

                score -= 25.0


            elif severity == "High":

                score -= 15.0


            elif severity == "Medium":

                score -= 10.0


            else:

                score -= 5.0


        score = max(
            0.0,
            score
        )


        # Only actual errors count as violations
        violations = sum(

            1

            for error in errors

            if error.get("severity")
            in [
                "Critical",
                "High",
                "Medium"
            ]

        )


        return (
            checks,
            score,
            violations
        )


    # =====================================================
    # RISK ASSESSMENT
    # =====================================================

    def _evaluate_risk(
        self,
        compliance_score: float,
        error_count: int
    ) -> str:

        if (
            compliance_score >= 90.0
            and error_count <= 1
        ):

            return "Low Risk"


        elif (
            compliance_score >= 75.0
            and error_count <= 3
        ):

            return "Medium Risk"


        elif (
            compliance_score >= 50.0
            or error_count <= 6
        ):

            return "High Risk"


        else:

            return "Critical Risk"


    # =====================================================
    # RECOMMENDATIONS
    # =====================================================

    def _generate_recommendations(
        self,
        errors: List[Dict[str, Any]],
        compliance_checks: List[Dict[str, Any]]
    ) -> List[str]:

        recommendations = []


        # -------------------------------------------------
        # Error recommendations
        # -------------------------------------------------

        for error in errors:

            suggestion = error.get(
                "suggestion"
            )

            if suggestion:

                recommendations.append(
                    suggestion
                )


        # -------------------------------------------------
        # Compliance recommendations
        # -------------------------------------------------

        for check in compliance_checks:

            if check.get("status") == "REVIEW":

                suggestion = check.get(
                    "suggestion"
                )

                if suggestion:

                    recommendations.append(
                        suggestion
                    )


        # -------------------------------------------------
        # No issues
        # -------------------------------------------------

        if not recommendations:

            recommendations.append(

                "No automatic issues were detected. "
                "Review the blueprint manually before "
                "construction approval."

            )


        # Remove duplicates

        recommendations = list(
            dict.fromkeys(
                recommendations
            )
        )


        return recommendations