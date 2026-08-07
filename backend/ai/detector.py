from ultralytics import YOLO

# Load the pretrained YOLO model
model = YOLO("yolov8n.pt")


def detect_objects(image_path: str):
    """
    Detect objects in an image using YOLO.
    """

    results = model.predict(
        source=image_path,
        conf=0.25,
        save=True
    )

    detections = []

    for result in results:
        for box in result.boxes:
            detections.append({
                "class": model.names[int(box.cls)],
                "confidence": round(float(box.conf), 2),
                "bbox": box.xyxy.tolist()[0]
            })

    return detections