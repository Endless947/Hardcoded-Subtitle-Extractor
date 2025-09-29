import easyocr
import torch

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"[INFO] Using device: {device}")

# initialize EasyOCR reader once
reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())

def ocr_frame_easyocr(frame):
    """
    Detect and recognize text from a frame using EasyOCR.
    Returns cleaned text string.
    """
    h, w = frame.shape[:2]
    # crop bottom quarter (common subtitle region)
    roi = frame[int(h*0.7):h, :]
    results = reader.readtext(roi)

    lines = []
    for (bbox, text, prob) in results:
        if prob > 0.4:
            lines.append(text.strip())

    return " ".join(lines)
