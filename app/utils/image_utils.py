import numpy as np
import cv2


def decode_image_rgb(file_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(file_bytes, dtype=np.uint8)
    img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise ValueError("Failed to decode image — unsupported format or corrupted file")
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
