"""摄像机控制抽象接口。"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import ShotType


class CameraController(ABC):
    """摄像机控制接口：高层摄影动作 → 底层控制。

    v0.1 使用 VirtualCamera（对合成帧裁切）；Phase 2 将替换为
    RealPTZController（VISCA / ONVIF / SDK）。二者实现同一接口，
    上层 Director 无需改动。
    """

    def __init__(self, camera_id: str):
        self.camera_id = camera_id

    @abstractmethod
    def capture(self, scene_frame, output_size=None):
        """返回该机位当前输出的画面帧。"""
        raise NotImplementedError

    # ---- Phase 2 预留的 PTZ 控制接口 ----
    def switch_camera(self, camera_id: str) -> None:  # pragma: no cover
        raise NotImplementedError

    def pan(self, value: float) -> None:  # pragma: no cover
        raise NotImplementedError

    def tilt(self, value: float) -> None:  # pragma: no cover
        raise NotImplementedError

    def zoom(self, value: float) -> None:  # pragma: no cover
        raise NotImplementedError

    def goto_preset(self, preset: str) -> None:  # pragma: no cover
        raise NotImplementedError
