"""VideoWriter：把节目帧写入 mp4 视频文件。"""
from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np


class VideoWriter:
    """基于 OpenCV VideoWriter 的 mp4 输出封装。"""

    def __init__(self, path: str, fps: float, size: Tuple[int, int]):
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._writer = cv2.VideoWriter(path, fourcc, fps, size)

    def write(self, frame: np.ndarray) -> None:
        self._writer.write(frame)

    def close(self) -> None:
        self._writer.release()
