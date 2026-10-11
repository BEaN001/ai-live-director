"""核心数据结构：WorldState / CameraState / CameraAction。

这些接口是整个项目的「共同契约」：
- Perception 层输出 WorldState（Observation）；
- Director 层输出 CameraAction（Action）；
- Camera / Switcher 层消费 CameraAction 完成执行。

这样把「人物 / 说话人 / 互动事件」与「摄像机动作」解耦：
未来把 RuleBasedDirector 替换成 LLM / VLM / VLA 时，只需换 Director 实现，
上下层接口保持不变。这也正是未来 VLA 的 Observation / Action 雏形。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ActionType(str, Enum):
    """高层摄影动作词汇表（Camera Action Token）。"""

    SWITCH_CAMERA = "SWITCH_CAMERA"   # 切换机位
    SHOT = "SHOT"                     # 指定景别
    ZOOM_IN = "ZOOM_IN"               # 推近
    ZOOM_OUT = "ZOOM_OUT"             # 拉远
    TRACK_PERSON = "TRACK_PERSON"     # 跟踪人物
    HOLD = "HOLD"                     # 保持当前镜头
    GOTO_PRESET = "GOTO_PRESET"       # 去往预置位


class ShotType(str, Enum):
    """景别（摄影语言）。"""

    WIDE = "WIDE"                       # 全景
    MEDIUM = "MEDIUM"                   # 中景
    MEDIUM_CLOSE_UP = "MEDIUM_CLOSE_UP" # 中近景
    CLOSE_UP = "CLOSE_UP"               # 特写
    TWO_SHOT = "TWO_SHOT"               # 双人镜头
    PRODUCT_CU = "PRODUCT_CU"           # 产品特写


@dataclass
class PersonState:
    """单个人物的结构化状态。"""

    id: str
    position: Tuple[float, float]  # 归一化坐标 (x, y)，范围 0~1
    speaking: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "position": [round(self.position[0], 3), round(self.position[1], 3)],
            "speaking": self.speaking,
        }


@dataclass
class CameraState:
    """单个机位的结构化状态。"""

    id: str
    shot: ShotType = ShotType.WIDE
    target: Optional[str] = None       # 当前对准目标（人物 id / "product" / "both"）
    position_label: str = "front"      # 机位位置描述

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "shot": self.shot.value,
            "target": self.target,
            "position_label": self.position_label,
        }


@dataclass
class WorldState:
    """统一的世界状态：感知层输出，也是未来 VLA 的 Observation。"""

    timestamp: float
    scene: str = "interview"
    people: List[PersonState] = field(default_factory=list)
    active_speaker: Optional[str] = None
    interaction: bool = False
    product_visible: bool = False
    camera: Optional[CameraState] = None  # 当前输出机位（由 StateManager 填充）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": round(self.timestamp, 2),
            "scene": self.scene,
            "people": [p.to_dict() for p in self.people],
            "active_speaker": self.active_speaker,
            "interaction": self.interaction,
            "product_visible": self.product_visible,
            "camera": self.camera.to_dict() if self.camera else None,
        }


@dataclass
class CameraAction:
    """导演输出动作：高层摄影决策，与底层硬件解耦。"""

    action: ActionType
    camera: Optional[str] = None
    shot: Optional[ShotType] = None
    duration: float = 4.0
    reason: str = ""
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value,
            "camera": self.camera,
            "shot": self.shot.value if self.shot else None,
            "duration": self.duration,
            "reason": self.reason,
            "confidence": self.confidence,
        }
