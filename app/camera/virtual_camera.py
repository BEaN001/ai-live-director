"""VirtualCamera：虚拟多机位，通过对合成场景帧裁切实现「切镜」。

Phase 0 的「摄像机」本质是对全场景帧做一次 ROI 裁切 + 缩放：
    CAM1 裁全场景（双人全景）
    CAM2 裁人物 A 区域（中近景）
    CAM3 裁人物 B 区域（中近景）
    CAM4 裁产品区域（产品特写）
这样无需任何硬件即可模拟真实导播的多机位切换。
"""
from __future__ import annotations

from typing import Optional, Tuple

import cv2
import numpy as np

from app.camera.base import CameraController
from app.schemas import ShotType


class VirtualCamera(CameraController):
    """基于 ROI 裁切的虚拟机位。"""

    def __init__(self, camera_id: str, crop_box: Tuple[int, int, int, int],
                 shot: ShotType = ShotType.WIDE,
                 target: Optional[str] = None,
                 position_label: str = "front"):
        super().__init__(camera_id)
        self.crop_box = crop_box  # (x, y, w, h)
        self.shot = shot
        self.target = target
        self.position_label = position_label

    def capture(self, scene_frame: np.ndarray, output_size=None) -> np.ndarray:
        """裁切并缩放到目标分辨率。"""
        x, y, w, h = self.crop_box
        roi = scene_frame[y:y + h, x:x + w]
        if output_size is not None:
            roi = cv2.resize(roi, (output_size[0], output_size[1]))
        return roi
