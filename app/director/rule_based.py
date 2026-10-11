"""RuleBasedDirector：规则导演（Phase 0）。

规则逻辑（对应 configs/director.yaml）：
    1. 用状态机把现场事件映射为目标机位 + 景别；
    2. 受「最小镜头时长」约束，避免频繁切镜；
    3. 每个动作附带 reason / confidence，便于解释「为什么这么拍」。

这是「Perception → Decision → Action」闭环最朴素、最可控的实现，
后续把决策逻辑替换为 LLM / VLM / VLA 即可渐进升级。
"""
from __future__ import annotations

import math
from typing import Dict, Optional

from app.director.base import Director
from app.director.state_machine import DirectorState, classify_state
from app.schemas import ActionType, CameraAction, ShotType, WorldState


class RuleBasedDirector(Director):
    """基于规则 + 状态机的导演。"""

    def __init__(self, config: Optional[Dict] = None):
        config = config or {}
        self.min_shot_duration: float = config.get("min_shot_duration", 3.0)
        self.default_shot_duration: float = config.get("default_shot_duration", 4.0)
        # 状态 → {camera, shot, reason, confidence}
        self.state_map: Dict[str, Dict] = config.get("states", {})

        self.current_camera: Optional[str] = None
        self.last_switch_time: float = -math.inf

    def reset(self) -> None:
        self.current_camera = None
        self.last_switch_time = -math.inf

    def _target(self, state: DirectorState) -> Dict:
        """返回状态对应的目标机位/景别/理由/置信度。"""
        entry = self.state_map.get(state.value, {})
        return {
            "camera": entry.get("camera", "CAM1"),
            "shot": ShotType(entry.get("shot", "WIDE")),
            "reason": entry.get("reason", "保持当前镜头"),
            "confidence": entry.get("confidence", 0.9),
        }

    def decide(self, world_state: WorldState) -> CameraAction:
        state = classify_state(world_state)
        target = self._target(state)
        desired_camera = target["camera"]
        desired_shot = target["shot"]
        now = world_state.timestamp
        elapsed = now - self.last_switch_time

        # 首次决策：直接切到目标机位
        if self.current_camera is None:
            return self._switch(desired_camera, desired_shot, now,
                                reason=target["reason"],
                                confidence=target["confidence"])

        # 已在该机位：保持，但若仍在最短时长内则说明原因
        if desired_camera == self.current_camera:
            if elapsed < self.min_shot_duration:
                return CameraAction(
                    action=ActionType.HOLD,
                    duration=self.default_shot_duration,
                    reason=f"最短镜头时长未到（{self.min_shot_duration:.0f}s）",
                    confidence=target["confidence"],
                )
            return CameraAction(
                action=ActionType.HOLD,
                duration=self.default_shot_duration,
                reason=f"已是最优机位 {self.current_camera}，保持",
                confidence=target["confidence"],
            )

        # 需要切镜，但受最短时长约束
        if elapsed < self.min_shot_duration:
            return CameraAction(
                action=ActionType.HOLD,
                duration=self.default_shot_duration,
                reason=f"最短镜头时长未到（{self.min_shot_duration:.0f}s）",
                confidence=target["confidence"],
            )

        return self._switch(desired_camera, desired_shot, now,
                            reason=target["reason"],
                            confidence=target["confidence"])

    def _switch(self, camera: str, shot: ShotType, now: float,
                reason: str, confidence: float) -> CameraAction:
        self.current_camera = camera
        self.last_switch_time = now
        return CameraAction(
            action=ActionType.SWITCH_CAMERA,
            camera=camera,
            shot=shot,
            duration=self.default_shot_duration,
            reason=reason,
            confidence=confidence,
        )
