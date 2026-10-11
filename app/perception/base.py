"""感知层抽象接口。"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import WorldState


class Perception(ABC):
    """现场感知：把视频/音频理解成结构化 WorldState。

    v0.1（Phase 0）只提供 MockPerception（脚本化时间线）；
    Phase 1 会替换为「YOLO 人物检测 + 说话人检测 + VLM 语义理解」，
    Phase 3 再把「Perception + Director」整体升级为端到端 VLA。
    """

    @abstractmethod
    def observe(self, timestamp: float) -> WorldState:
        """返回当前时刻的感知结果（不含 camera 字段，由 StateManager 填充）。"""
        raise NotImplementedError
