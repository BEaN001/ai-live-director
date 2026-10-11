"""PTZ 摄像机适配器（占位）。

Phase 2 计划把 VirtualCamera 替换为真实 PTZ 摄像机控制：
    CameraAction → RealPTZController → VISCA / ONVIF / SDK → 物理云台

与 VirtualCamera 实现同一 CameraController 接口，上层 Director 无需改动。
本文件仅保留接口说明，v0.1（Phase 0）不实现，避免引入硬件依赖。
"""
from __future__ import annotations

from app.camera.base import CameraController


class RealPTZController(CameraController):
    """真实 PTZ 摄像机控制（Phase 2 实现）。"""

    def __init__(self, camera_id: str, protocol: str = "VISCA", address: str = ""):
        super().__init__(camera_id)
        self.protocol = protocol
        self.address = address
        raise NotImplementedError(
            "RealPTZController 为 Phase 2 预留接口，v0.1 不实现。"
            "当前请使用 VirtualCamera（app.camera.virtual_camera）。"
        )

    def capture(self, scene_frame, output_size=None):
        raise NotImplementedError
