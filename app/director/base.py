"""导演抽象接口。"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import CameraAction, WorldState


class Director(ABC):
    """AI 导演：输入 WorldState，输出 CameraAction。

    v0.1 使用 RuleBasedDirector；Phase 1 可替换为 LLM Director，
    Phase 3 替换为 VLA Policy。输出接口（CameraAction）保持不变。
    """

    @abstractmethod
    def decide(self, world_state: WorldState) -> CameraAction:
        """根据当前世界状态决定下一个摄影动作。"""
        raise NotImplementedError

    def reset(self) -> None:
        """复位导演内部状态（当前机位、上次切镜时间等）。"""
        pass
