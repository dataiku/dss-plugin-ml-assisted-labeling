import json
import math


def make_queries(rows, image_paths, folder_paths):
    """Convert DeepHub object detections into the labeling app's query rows."""
    expected = set()
    available = set(folder_paths)
    for path in image_paths:
        if not isinstance(path, str) or not path.strip():
            raise ValueError("Each input image must have a path")
        path = '/' + path.lstrip('/')
        if path in expected:
            raise ValueError("Duplicate input image path: {}".format(path))
        if path not in available:
            raise ValueError("Image path is not in the selected folder: {}".format(path))
        expected.add(path)
    if not expected:
        raise ValueError("Input images dataset is empty")
    queries = []
    seen = set()
    for path, prediction in rows:
        if not isinstance(path, str) or not path.strip():
            raise ValueError("Each prediction must have an image path")
        path = '/' + path.lstrip('/')
        if path in seen:
            raise ValueError("Duplicate image path: {}".format(path))
        seen.add(path)
        if path not in expected:
            raise ValueError("Prediction has no matching input image: {}".format(path))
        try:
            detections = json.loads(prediction)
        except (TypeError, ValueError):
            raise ValueError("Invalid prediction JSON for image: {}".format(path))
        if not isinstance(detections, list):
            raise ValueError("Prediction must be a list of detections for image: {}".format(path))
        confidences = []
        for detection in detections:
            confidence = detection.get('confidence') if isinstance(detection, dict) else None
            if (isinstance(confidence, bool) or not isinstance(confidence, (int, float))
                    or not math.isfinite(confidence) or not 0 <= confidence <= 1):
                raise ValueError("Invalid detection confidence for image: {}".format(path))
            confidences.append(confidence)
        queries.append((path, 1 - max(confidences) if confidences else 1.0))
    missing = expected - seen
    if missing:
        raise ValueError("{} input images have no prediction".format(len(missing)))
    return queries
