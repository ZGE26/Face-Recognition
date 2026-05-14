import numpy as np
import face_recognition


def extract_single_embedding(image_rgb: np.ndarray) -> np.ndarray | None:
    """Returns encoding only when exactly one face is detected (used for register)."""
    locations = face_recognition.face_locations(image_rgb, number_of_times_to_upsample=2)
    if len(locations) != 1:
        return None
    encodings = face_recognition.face_encodings(image_rgb, known_face_locations=locations)
    return encodings[0] if encodings else None


def extract_best_embedding(image_rgb: np.ndarray) -> np.ndarray | None:
    """Returns encoding of the largest detected face (used for scan)."""
    locations = face_recognition.face_locations(image_rgb, number_of_times_to_upsample=2)
    if not locations:
        return None
    encodings = face_recognition.face_encodings(image_rgb, known_face_locations=locations)
    return encodings[0] if encodings else None


def find_best_match(
    probe: np.ndarray,
    candidates: list[tuple[int, np.ndarray]],
    tolerance: float,
) -> tuple[int, float] | None:
    """
    Compares probe against all candidates using Euclidean distance.
    Returns (user_id, confidence) of the best match below tolerance, or None.
    Confidence = 1.0 - distance (higher = more certain).
    """
    if not candidates:
        return None

    known_encodings = [enc for _, enc in candidates]
    user_ids = [uid for uid, _ in candidates]

    distances = face_recognition.face_distance(known_encodings, probe)
    best_idx = int(np.argmin(distances))
    best_distance = float(distances[best_idx])

    if best_distance <= tolerance:
        confidence = round(1.0 - best_distance, 4)
        return user_ids[best_idx], confidence

    return None
