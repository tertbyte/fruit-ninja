"""Hand detection wrapper around MediaPipe's Tasks API.

Tracks up to two hands and reports each one's index-fingertip position,
which the rest of the game treats as the tip of a ninja blade.

On first launch the hand-landmarker model is downloaded next to this
file (~7 MB) so the rest of the pipeline can run fully offline.
"""

import os
import time
import urllib.request
from typing import List, Tuple

from mediapipe import Image, ImageFormat
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    RunningMode,
)

_LM_INDEX_TIP = 8

_MODEL_FILENAME = "hand_landmarker.task"
_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
)


def _ensure_model() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, _MODEL_FILENAME)
    if not os.path.exists(path):
        print(f"Downloading {_MODEL_FILENAME} (~7 MB) ...")
        urllib.request.urlretrieve(_MODEL_URL, path)
        print("Model ready.")
    return path


class HandSensor:
    """Returns index-fingertip pixel coordinates for every hand in frame."""

    def __init__(self, max_hands: int = 2, detection_confidence: float = 0.6,
                 tracking_confidence: float = 0.5):
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=_ensure_model()),
            running_mode=RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_hand_presence_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self._detector = HandLandmarker.create_from_options(options)
        # Tasks API requires monotonically increasing timestamps in VIDEO
        # mode -- anchor them at construction.
        self._stream_origin = time.monotonic()

    def read(self, rgb_frame, width: int, height: int) -> List[Tuple[int, int]]:
        mp_image = Image(image_format=ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int((time.monotonic() - self._stream_origin) * 1000)
        result = self._detector.detect_for_video(mp_image, timestamp_ms)

        tips = []
        for landmarks in result.hand_landmarks:
            tip = landmarks[_LM_INDEX_TIP]
            tips.append((int(tip.x * width), int(tip.y * height)))
        return tips

    def close(self) -> None:
        self._detector.close()
