"""导演状态机：把现场事件映射为离散的「导演状态」。

状态机保证了切镜的稳定语义，避免让 LLM 每一秒自由发挥导致「抽风式切镜」：
    IDLE → FOCUS_A → FOCUS_B → TWO_SHOT → PRODUCT
事件优先级：产品展示 > 双方互动 > 单人讲话 > 无事件。
"""
from __future__ import annotations

from enum import Enum

from app.schemas import WorldState


class DirectorState(str, Enum):
    """导演状态。"""

    IDLE = "IDLE"         # 无事件，全景
    FOCUS_A = "FOCUS_A"   # A 讲话，A 中近景
    FOCUS_B = "FOCUS_B"   # B 讲话，B 中近景
    TWO_SHOT = "TWO_SHOT" # 双方互动，双人镜头
    PRODUCT = "PRODUCT"   # 产品展示，产品特写


def classify_state(world_state: WorldState) -> DirectorState:
    """根据世界状态判定当前导演状态（事件优先级从高到低）。"""
    if world_state.product_visible:
        return DirectorState.PRODUCT
    if world_state.interaction:
        return DirectorState.TWO_SHOT
    if world_state.active_speaker == "A":
        return DirectorState.FOCUS_A
    if world_state.active_speaker == "B":
        return DirectorState.FOCUS_B
    return DirectorState.IDLE
