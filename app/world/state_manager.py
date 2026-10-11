"""StateManager：维护摄像机状态，并把感知结果合并成统一 WorldState。

它是「感知（现场发生了什么）」与「导演（应该怎么拍）」之间的关键中间层：
Director 看到的不是一堆像素，而是一个结构化的 WorldState。
"""
from __future__ import annotations

from typing import Dict, Optional

from app.schemas import CameraState, ShotType, WorldState


class StateManager:
    """持有全部机位状态与当前输出机位。"""

    def __init__(self, camera_defs):
        # camera_defs: list[dict]，来自 configs/cameras.yaml 的 cameras 段
        self.cameras: Dict[str, CameraState] = {}
        for c in camera_defs:
            self.cameras[c["id"]] = CameraState(
                id=c["id"],
                shot=ShotType(c.get("shot", "WIDE")),
                target=c.get("target"),
                position_label=c.get("position_label", "front"),
            )
        # 初始输出机位（第一个机位）
        self.current_camera_id: str = camera_defs[0]["id"]
        self.current_shot: ShotType = self.cameras[self.current_camera_id].shot

    def reset(self) -> None:
        """复位到初始机位（用于循环播放演示）。"""
        first = next(iter(self.cameras))
        self.current_camera_id = first
        self.current_shot = self.cameras[first].shot

    def set_current(self, camera_id: str, shot: Optional[ShotType]) -> None:
        """更新当前输出机位与景别。"""
        if camera_id in self.cameras:
            self.current_camera_id = camera_id
            self.current_shot = shot or self.cameras[camera_id].shot

    def get_camera_states(self) -> Dict[str, CameraState]:
        """返回所有机位的状态快照。"""
        return dict(self.cameras)

    def merge(self, perceived: WorldState) -> WorldState:
        """把感知结果与当前机位状态合并为完整 WorldState。"""
        perceived.camera = CameraState(
            id=self.current_camera_id,
            shot=self.current_shot,
            target=self.cameras[self.current_camera_id].target,
            position_label=self.cameras[self.current_camera_id].position_label,
        )
        return perceived
