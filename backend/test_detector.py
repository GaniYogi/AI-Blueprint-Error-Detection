from ai.detector import detect_objects

image_path = "uploads/test.png"

results = detect_objects(image_path)

print("\nDetected Objects\n")

for obj in results:
    print(obj)