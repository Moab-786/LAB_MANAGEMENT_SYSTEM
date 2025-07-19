import os
import sys
import argparse
import json
import cv2
from collections import Counter
from ultralytics import YOLO

label_normalization = {
    "Scientific SM7023 3¾DMM": "Scientific SM7023 3.75 DMM"
}

def detect_objects_in_image(model, image_path, min_conf=0.8):
    results = model(image_path, verbose=False)
    detections = results[0].boxes
    names = model.names
    detected_labels = []

    for det in detections:
        conf = float(det.conf.item())
        if conf < min_conf:
            continue
        label = names[int(det.cls.item())]
        clean_label = label_normalization.get(label, label)
        detected_labels.append(clean_label)

    return dict(Counter(detected_labels))


def detect_objects_in_video(model, video_path, min_conf=0.8, resolution=(640, 480), max_frames=300):
    if not os.path.exists(video_path):
        print("❌ Video source not found.")
        return {}

    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

    max_counts = Counter()
    frame_num = 0

    while cap.isOpened() and frame_num < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, verbose=False)
        frame_counts = Counter()

        for det in results[0].boxes:
            conf = float(det.conf.item())
            if conf < min_conf:
                continue
            label = model.names[int(det.cls.item())]
            clean_label = label_normalization.get(label, label)
            frame_counts[clean_label] += 1

        for label, count in frame_counts.items():
            if count > max_counts[label]:
                max_counts[label] = count

        frame_num += 1

    cap.release()
    return dict(max_counts)

def live_detection(model_path, source, min_conf=0.8, resolution=(640, 480), display=False, frame_limit=100):
    if not os.path.exists(model_path):
        print("YOLO model not found.")
        return {}

    model = YOLO(model_path)
    cap = cv2.VideoCapture(int(source) if source.isdigit() else source)

    if not cap.isOpened():
        print("Failed to open video source.")
        return {}

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

    max_counts = Counter()
    frame_count = 0

    while cap.isOpened() and frame_count < frame_limit:
        ret, frame = cap.read()
        if not ret:
            break


        # Resize frame to the desired resolution
        frame = cv2.resize(frame, resolution)

        results = model(frame, verbose=False)
        detected_labels = []
        for det in results[0].boxes:
            conf = float(det.conf.item())
            if conf < min_conf:
                continue
            cls = int(det.cls.item())
            label = model.names[cls]
            clean_label = label_normalization.get(label, label)
            detected_labels.append(clean_label)

        frame_counts = Counter(detected_labels)
        for label, count in frame_counts.items():
            if count > max_counts[label]:
                max_counts[label] = count

        if display:
            for det in results[0].boxes:
                if float(det.conf.item()) < min_conf:
                    continue
                x1, y1, x2, y2 = map(int, det.xyxy[0].tolist())
                label = model.names[int(det.cls.item())]
                clean_label = label_normalization.get(label, label)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{clean_label}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.imshow("Live Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        frame_count += 1

    cap.release()
    if display:
        cv2.destroyAllWindows()

    return dict(max_counts)

def detect_objects(model_path, source_path, min_conf=0.8, resolution=(640, 480)):
    if not os.path.exists(model_path):
        print("❌ Model not found.")
        return {}

    if not os.path.exists(source_path):
        print("❌ Source not found.")
        return {}

    model = YOLO(model_path)
    ext = os.path.splitext(source_path)[1].lower()

    if ext in ['.mp4', '.avi', '.mov', '.mkv']:
        return detect_objects_in_video(model, source_path, min_conf, resolution)
    else:
        return detect_objects_in_image(model, source_path, min_conf)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to YOLO model")
    parser.add_argument("--source", required=True, help="Image/video file path or camera index")
    parser.add_argument("--thresh", default=0.8, type=float, help="Confidence threshold")
    parser.add_argument("--live", action="store_true", help="Enable live webcam detection")
    parser.add_argument("--resolution", default="640x480", help="e.g. 1280x720")

    args = parser.parse_args()
    width, height = map(int, args.resolution.lower().split('x'))
    resolution = (width, height)

    if args.live:
        live_detection(args.model, args.source, args.thresh, resolution)
    else:
        result = detect_objects(args.model, args.source, args.thresh, resolution)
        print(json.dumps(result))
