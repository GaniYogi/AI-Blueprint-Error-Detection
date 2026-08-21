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

                candidate_paths = [
                    os.path.join(models_dir, "best.pt"),
                    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models", "best.pt"),
                    os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "best.pt"),
                ]

                weights_path = None
                for path in candidate_paths:
                    if os.path.exists(path):
                        weights_path = path
                        break

                if weights_path:
                    print(f"Loading YOLO model: {weights_path}")
                    self.yolo_model = YOLO(weights_path)
                    print("YOLO model loaded successfully.")
                    print(f"YOLO classes: {self.yolo_model.names}")
                else:
                    print(f"YOLO weights not found in candidates: {candidate_paths}")

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
                    pts = line[0] if (hasattr(line[0], '__len__') and len(line[0]) == 4) else line
                    x1, y1, x2, y2 = pts
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
                pts = line[0] if (hasattr(line[0], '__len__') and len(line[0]) == 4) else line
                x1, y1, x2, y2 = pts
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
            if HAS_CV2 and os.path.exists(file_path):
                img_gray = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
                target_input = img_gray if img_gray is not None else file_path
            else:
                target_input = file_path

            results = self.reader.readtext(target_input)

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

                # --- Filter 1: confidence threshold ---
                confidence = float(conf)
                if confidence < 0.50:
                    continue

                # --- Filter 2: strip and skip empty text ---
                text = str(text).strip()
                if not text:
                    continue


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
                        text,

                    "bbox": [

                        int(x),

                        int(y),

                        int(w),

                        int(h)

                    ],

                    "confidence":
                        round(
                            confidence,
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
    # SPATIAL HELPER
    # =====================================================

    @staticmethod
    def _is_near_wall(
        obj_bbox: List,
        wall_bboxes: List[List],
        tolerance: float
    ) -> bool:
        """
        Return True if obj_bbox is within `tolerance` pixels of ANY
        wall bbox, or overlaps one.

        Geometry (all bboxes are [x, y, w, h]):

          Rect A: (ox, oy) → (ox+ow, oy+oh)
          Rect B: (wx, wy) → (wx+ww, wy+wh)

          Horizontal gap:
            gap_x = max(0, max(ox, wx) − min(ox+ow, wx+ww))
          Vertical gap:
            gap_y = max(0, max(oy, wy) − min(oy+oh, wy+wh))

          When the rects overlap, gap_x == 0 AND gap_y == 0.
          Euclidean min-boundary-distance = sqrt(gap_x² + gap_y²).

        A door/window is considered "near" a wall if this distance
        is ≤ tolerance for at least one wall segment.
        """
        ox, oy, ow, oh = [
            float(v) for v in obj_bbox
        ]

        for wb in wall_bboxes:
            wx, wy, ww, wh = [float(v) for v in wb]

            # Horizontal gap between the two axis-aligned rects
            gap_x = max(
                0.0,
                max(ox, wx) - min(ox + ow, wx + ww)
            )

            # Vertical gap between the two axis-aligned rects
            gap_y = max(
                0.0,
                max(oy, wy) - min(oy + oh, wy + wh)
            )

            # Euclidean min-distance between rect boundaries
            dist = (gap_x ** 2 + gap_y ** 2) ** 0.5

            if dist <= tolerance:
                return True

        return False


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

        # -------------------------------------------------
        # Floating door / window detection
        #
        # A door or window is considered "floating" when it
        # is clearly far from every detected wall segment.
        # This check only runs when YOLO has produced actual
        # wall bboxes; if no walls were found (OpenCV room-
        # only fallback) there is nothing to compare against.
        #
        # Tolerance = 1.5 × the object's own larger dimension.
        # This gives generous room for:
        #   • doors that sit in a wall opening (gap up to door-
        #     width away from each flanking wall segment)
        #   • slight bbox registration errors between YOLO
        #     detections of adjacent elements
        # Only clearly isolated elements (distance >> their
        # own size) are flagged.
        # -------------------------------------------------

        if walls:

            wall_bboxes = [w["bbox"] for w in walls]

            # -- Floating doors --
            for door in doors:
                d_bbox = door["bbox"]

                # Tolerance proportional to door size
                tol = max(
                    float(d_bbox[2]),
                    float(d_bbox[3])
                ) * 1.5

                if not self._is_near_wall(d_bbox, wall_bboxes, tol):
                    errors.append({
                        "id": f"err_floating_{door['id']}",
                        "type": "floating_door",
                        "description": (
                            f"Door '{door['id']}' appears to be far from "
                            "all detected wall segments and may be "
                            "misplaced or a false positive."
                        ),
                        "bbox": d_bbox,
                        "severity": "Medium",
                        "suggestion": (
                            "Verify this door is positioned at a wall "
                            "opening. If correct, the wall detection may "
                            "be incomplete — try a higher-resolution image."
                        )
                    })

            # -- Floating windows --
            for window in windows:
                w_bbox = window["bbox"]

                # Tolerance proportional to window size
                tol = max(
                    float(w_bbox[2]),
                    float(w_bbox[3])
                ) * 1.5

                if not self._is_near_wall(w_bbox, wall_bboxes, tol):
                    errors.append({
                        "id": f"err_floating_{window['id']}",
                        "type": "floating_window",
                        "description": (
                            f"Window '{window['id']}' appears to be far "
                            "from all detected wall segments and may be "
                            "misplaced or a false positive."
                        ),
                        "bbox": w_bbox,
                        "severity": "Medium",
                        "suggestion": (
                            "Verify this window is positioned within a "
                            "wall. If correct, the wall detection may be "
                            "incomplete — try a higher-resolution image."
                        )
                    })

        # -------------------------------------------------
        # Room-label OCR validation
        #
        # Only runs when the detection pipeline found at
        # least one room (YOLO or OCR enrichment).  If rooms
        # exist but no recognisable room-label keyword appears
        # in the (already confidence-filtered) OCR results,
        # we raise a REVIEW-level warning.
        #
        # Matching strategy:
        #   1. Normalise each OCR text to lowercase and strip
        #      punctuation/extra whitespace.
        #   2. Tokenise on whitespace so that single-word
        #      labels ("hall", "kitchen") are only matched
        #      against whole tokens — avoids matching "store"
        #      inside "restore" etc.
        #   3. For multi-word labels ("living room",
        #      "master bedroom"), check that the normalised
        #      text CONTAINS the full phrase as a substring
        #      of the joined token string.
        #
        # Rule: skip entirely when no rooms detected
        #       (insufficient evidence to flag anything).
        # -------------------------------------------------

        if rooms:

            # Vocabulary: recognisable room-label phrases.
            # Order matters for multi-word entries: put them
            # before their component words so the phrase
            # match fires first (no overlap issues with the
            # single-word fallback tokens).
            ROOM_LABEL_VOCAB = [
                "master bedroom",
                "living room",
                "dining room",
                "bed room",
                "bedroom",
                "kitchen",
                "dining",
                "bathroom",
                "toilet",
                "washroom",
                "hall",
                "office",
                "store",
                "garage",
            ]

            import re as _re

            def _normalise(raw: str) -> str:
                """
                Lowercase, collapse whitespace, strip leading/
                trailing punctuation so OCR noise is reduced.
                e.g. "LIVING ROOM." -> "living room"
                     "BED- ROOM"   -> "bed room"
                """
                text = raw.lower()
                # Replace hyphens/dashes used as word-joiners
                # with a space so "BED-ROOM" -> "bed room"
                text = text.replace("-", " ")
                # Remove non-alpha-space characters
                text = _re.sub(r"[^a-z ]", " ", text)
                # Collapse multiple spaces
                text = _re.sub(r"\s+", " ", text).strip()
                return text

            def _ocr_contains_room_label(
                ocr_list: List[Dict[str, Any]],
                vocab: List[str]
            ) -> bool:
                """
                Return True if any single OCR result, after
                normalisation, contains one of the vocabulary
                phrases (whole-word for single-token labels,
                substring for multi-token phrases).
                """
                for entry in ocr_list:
                    norm = _normalise(entry.get("text", ""))
                    if not norm:
                        continue
                    tokens = norm.split()
                    token_set = set(tokens)
                    for label in vocab:
                        label_tokens = label.split()
                        if len(label_tokens) == 1:
                            # Single-word: must be an exact token
                            if label_tokens[0] in token_set:
                                return True
                        else:
                            # Multi-word: substring of joined tokens
                            if label in norm:
                                return True
                return False

            has_room_label = _ocr_contains_room_label(
                ocr_results,
                ROOM_LABEL_VOCAB
            )

            if not has_room_label:
                errors.append({
                    "id": "err_missing_room_labels",
                    "type": "missing_room_labels",
                    "description": (
                        f"{len(rooms)} room(s) detected but no "
                        "recognisable room-label text was found in the "
                        "OCR output. Room names (e.g. BEDROOM, KITCHEN, "
                        "LIVING ROOM) may be absent or illegible."
                    ),
                    "bbox": None,
                    "severity": "Low",
                    "suggestion": (
                        "Ensure each room is clearly labelled on the "
                        "blueprint. Labels should be printed in a "
                        "readable font at sufficient size for OCR to "
                        "detect them reliably."
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
        # window_ventilation_ratio  (from rules_dict)
        #
        # On a 2D plan at uniform scale, the ratio of
        # pixel areas equals the ratio of real-world areas,
        # so this check is scale-invariant and does not
        # require a pixel-to-foot conversion.
        #
        # Rules that CANNOT be evaluated with current data:
        #   min_bedroom_area   — no pixel-to-ft scale
        #   min_door_width     — no pixel-to-ft scale
        #   min_corridor_width — no corridor class + no scale
        #   accessibility_compliance — requires bathroom
        #                         detection & door-swing data
        # -------------------------------------------------

        ventilation_threshold = float(
            rules.get("window_ventilation_ratio", 8.0)
        )

        window_objs = [
            o for o in detected_objects
            if o["label"].lower() == "window"
        ]

        room_objs = [
            o for o in detected_objects
            if o["label"].lower() == "room"
        ]

        if window_objs and room_objs:

            total_window_px = sum(
                float(o["bbox"][2]) * float(o["bbox"][3])
                for o in window_objs
            )

            total_room_px = sum(
                float(o["bbox"][2]) * float(o["bbox"][3])
                for o in room_objs
            )

            if total_room_px > 0:

                actual_ratio = (total_window_px / total_room_px) * 100.0

                ventilation_status = (
                    "PASS"
                    if actual_ratio >= ventilation_threshold
                    else "FAIL"
                )

                checks.append({
                    "rule_key": "window_ventilation_ratio",
                    "name": "Window Ventilation Ratio",
                    "category": "ventilation",
                    "description": (
                        "Total window bbox area as a percentage of "
                        "total room bbox area. Pixel ratio is "
                        "scale-invariant on a 2D floor plan."
                    ),
                    "threshold": (
                        f">= {ventilation_threshold:.1f}%"
                    ),
                    "actual": (
                        f"{actual_ratio:.1f}% "
                        f"({len(window_objs)} window(s), "
                        f"{len(room_objs)} room(s))"
                    ),
                    "status": ventilation_status,
                    "severity": "Medium",
                    "suggestion": (
                        "Add or enlarge windows to improve natural "
                        "light and ventilation if ratio is below "
                        f"{ventilation_threshold:.1f}%."
                    )
                })

            else:

                checks.append({
                    "rule_key": "window_ventilation_ratio",
                    "name": "Window Ventilation Ratio",
                    "category": "ventilation",
                    "description": (
                        "Could not compute ratio: room area is zero."
                    ),
                    "threshold": (
                        f">= {ventilation_threshold:.1f}%"
                    ),
                    "actual": "Room area is zero — cannot compute ratio.",
                    "status": "REVIEW",
                    "severity": "Medium",
                    "suggestion": (
                        "Verify room detection results manually."
                    )
                })

        else:

            missing = []
            if not window_objs:
                missing.append("windows")
            if not room_objs:
                missing.append("rooms")

            checks.append({
                "rule_key": "window_ventilation_ratio",
                "name": "Window Ventilation Ratio",
                "category": "ventilation",
                "description": (
                    "Could not compute ventilation ratio: "
                    f"{' and '.join(missing)} not detected."
                ),
                "threshold": (
                    f">= {ventilation_threshold:.1f}%"
                ),
                "actual": (
                    f"Insufficient data "
                    f"({len(window_objs)} window(s), "
                    f"{len(room_objs)} room(s) detected)"
                ),
                "status": "REVIEW",
                "severity": "Medium",
                "suggestion": (
                    "Ensure windows and rooms are clearly visible "
                    "in the blueprint for an accurate ratio check."
                )
            })


        # -------------------------------------------------
        # Calculate score
        #
        # Step 1 — error deductions (unchanged):
        #   Critical → -25   High → -15
        #   Medium   → -10   Low  → -5
        #
        # Step 2 — compliance-check deductions:
        #   REVIEW → -3   FAIL → -7   PASS → 0
        #
        #   To avoid double-penalising, checks whose
        #   underlying issue is ALREADY represented by an
        #   error in the errors list are skipped in Step 2.
        #
        #   Mapping of check rule_key → error type it overlaps:
        #     wall_detection     → missing_wall_detection
        #     door_detection     → missing_door_detection
        #     window_detection   → missing_window_detection
        #   (ocr_detection and window_ventilation_ratio have
        #    no matching error type, so they are always scored)
        # -------------------------------------------------

        score = 100.0

        # ------ Step 1: error deductions ------

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

        # ------ Step 2: compliance-check deductions ------
        #
        # Only checks NOT already penalised via an error
        # receive an additional small deduction.

        _COVERED_BY_ERROR = {
            "wall_detection":   "missing_wall_detection",
            "door_detection":   "missing_door_detection",
            "window_detection": "missing_window_detection",
        }

        _error_types_present = {
            e.get("type") for e in errors
        }

        for check in checks:

            status   = check.get("status", "PASS")
            rule_key = check.get("rule_key", "")

            # Skip PASS checks — no deduction
            if status == "PASS":
                continue

            # Skip if this check's issue is already in errors
            overlapping_error = _COVERED_BY_ERROR.get(rule_key)
            if (
                overlapping_error
                and overlapping_error in _error_types_present
            ):
                continue

            # Apply deduction
            if status == "FAIL":
                score -= 7.0

            elif status == "REVIEW":
                score -= 3.0

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