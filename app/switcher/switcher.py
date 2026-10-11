"""Switcher：执行 CameraAction，输出节目（PGM）画面。

AI 导播的最后一步：Director 输出 CameraAction → Switcher 选中对应机位 →
输出该机位画面作为 Program Feed。同时为 Dashboard 提供全部机位预览。
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

import cv2
import numpy as np

from app.schemas import ActionType, CameraAction, ShotType
from app.world.state_manager import StateManager


class Switcher:
    """多机位导播切换器。"""

    def __init__(self, cameras: Dict, state_manager: StateManager,
                 program_size: Tuple[int, int] = (1280, 720)):
        # cameras: dict[id, VirtualCamera]
        self.cameras = cameras
        self.state_manager = state_manager
        self.program_size = program_size

    def apply(self, action: CameraAction, scene_frame: np.ndarray) -> np.ndarray:
        """执行动作，返回节目输出帧。"""
        if action.action == ActionType.SWITCH_CAMERA and action.camera in self.cameras:
            self.state_manager.set_current(action.camera, action.shot)

        cam = self.cameras[self.state_manager.current_camera_id]
        frame = cam.capture(scene_frame, output_size=self.program_size)
        return self._overlay(frame, self.state_manager.current_camera_id,
                             self.state_manager.current_shot)

    def previews(self, scene_frame: np.ndarray,
                 size: Tuple[int, int]) -> Dict[str, np.ndarray]:
        """返回所有机位的预览帧（Dashboard 用）。"""
        return {
            cid: cam.capture(scene_frame, output_size=size)
            for cid, cam in self.cameras.items()
        }

    @staticmethod
    def _overlay(frame: np.ndarray, camera_id: str, shot: ShotType) -> np.ndarray:
        """在节目画面上叠加机位/景别信息。"""
        out = frame.copy()
        h, w = out.shape[:2]
        cv2.rectangle(out, (0, 0), (w - 1, h - 1), (255, 255, 255), 5)
        cv2.rectangle(out, (0, 0), (w, 46), (0, 0, 0), -1)
        cv2.putText(out, "PROGRAM OUTPUT", (16, 32), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (255, 255, 255), 2, cv2.LINE_AA)
        label = f"{camera_id}  |  {shot.value}"
        cv2.putText(out, label, (w - 320, 32), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (120, 220, 255), 2, cv2.LINE_AA)
        return out
