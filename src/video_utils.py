import cv2

def extract_frames(video_path, interval_ms=500):
    """
    Extract frames every interval_ms milliseconds.
    Returns list of (timestamp_sec, frame)
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    frames = []
    frame_time_ms = 0
    while True:
        cap.set(cv2.CAP_PROP_POS_MSEC, frame_time_ms)
        ret, frame = cap.read()
        if not ret:
            break
        timestamp_sec = frame_time_ms / 1000.0
        frames.append((timestamp_sec, frame))
        frame_time_ms += interval_ms

    cap.release()
    return frames
