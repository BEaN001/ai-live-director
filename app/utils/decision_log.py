"""DecisionLog：记录每一次导演决策（Observation → Decision → Action）。

这是项目的数据飞轮雏形：
    Observation（WorldState）→ Expert/Agent Decision → Camera Action
持续积累后，即可成为未来 VLA 的行为克隆 / SFT 训练数据集。
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from app.schemas import CameraAction, WorldState


class DecisionLog:
    """把每次决策追加写入 JSONL 文件。"""

    def __init__(self, path: str):
        self.path = path
        self.entries: List[Dict[str, Any]] = []
        self._file = open(path, "w", encoding="utf-8")

    def record(self, world_state: WorldState, action: CameraAction) -> Dict[str, Any]:
        """记录一条决策，返回其 dict。"""
        entry = {
            "timestamp": round(world_state.timestamp, 2),
            "observation": {
                "scene": world_state.scene,
                "active_speaker": world_state.active_speaker,
                "interaction": world_state.interaction,
                "product_visible": world_state.product_visible,
            },
            "camera_state": {
                "current": world_state.camera.id if world_state.camera else None,
                "shot": world_state.camera.shot.value if world_state.camera else None,
            },
            "decision": {
                "action": action.action.value,
                "camera": action.camera,
                "shot": action.shot.value if action.shot else None,
                "duration": action.duration,
            },
            "reason": action.reason,
            "confidence": action.confidence,
        }
        self._file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._file.flush()
        self.entries.append(entry)
        return entry

    def close(self) -> None:
        self._file.close()
