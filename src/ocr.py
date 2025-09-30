import easyocr
import torch
from rapidfuzz import fuzz

# Choose device
device = 'cpu'
print(f"[INFO] Using device: {device}")

# Initialize EasyOCR reader once
reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())

# List of phrases to ignore (case-insensitive, partial matches)
ignored_phrases = [
    "activate windows",
    "go to settings to activate windows",
    "press ctrl+alt+del",
    "windows",
    "go to"
]

# Keep track of last subtitle to prevent consecutive duplicates
last_subtitle = None


def is_valid_subtitle(text):
    """
    Check if the text is valid and not a system/overlay message.
    """
    text = text.strip()
    if not text:
        return False

    text_lower = text.lower()
    # Use fuzzy partial ratio to catch partial matches
    for phrase in ignored_phrases:
        if fuzz.partial_ratio(text_lower, phrase.lower()) > 80:
            return False
    return True


def ocr_frame_easyocr(frame):
    """
    Detect and recognize text from a (pre-cropped) frame using EasyOCR.
    Returns cleaned text string, ignoring unwanted lines and consecutive duplicates.
    """
    global last_subtitle

    results = reader.readtext(frame)

    lines = []
    for (_, text, prob) in results:
        if prob < 0.4:
            continue  # skip low-confidence results

        text = text.strip()
        if not text:
            continue

        # skip system overlays or unwanted text
        if not is_valid_subtitle(text):
            continue

        # prevent consecutive duplicates with fuzzy matching
        if last_subtitle and fuzz.ratio(text.lower(), last_subtitle.lower()) > 90:
            continue

        lines.append(text)
        last_subtitle = text

    return " ".join(lines)
