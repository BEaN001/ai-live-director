"""MockPerception：脚本化时间线，模拟「两人访谈」现场感知。

Phase 0 不读取任何真实视频/模型，直接用一段预定义时间线驱动：
    A 讲话 → B 讲话 → 两人互动 → 产品展示 → A 再讲话
每个时刻返回对应的 WorldState（人物、说话人、事件、产品是否可见）。
"""
from __future__ import annotations

from typing import List, Tuple

from app.perception.base import Perception
from app.schemas import PersonState, WorldState

# 人物在画面中的归一化位置（左右各一）
_PERSON_A_POS = (0.30, 0.50)
_PERSON_B_POS = (0.70, 0.50)


class MockPerception(Perception):
    """根据预定义时间线生成现场状态。"""

    def __init__(self, total_duration: float = 25.0):
        self.total_duration = total_duration
        # 时间线：(起始秒, 结束秒, 事件类型)
        self.timeline: List[Tuple[float, float, str]] = [
            (0.0, 5.0, "A_speaking"),
            (5.0, 10.0, "B_speaking"),
            (10.0, 15.0, "interaction"),
            (15.0, 20.0, "product"),
            (20.0, 25.0, "A_speaking"),
        ]

    def _event_at(self, timestamp: float) -> str:
        """根据时间戳查表得到当前事件。"""
        for start, end, event in self.timeline:
            if start <= timestamp < end:
                return event
        # 越界兜底：回到最后一段
        return self.timeline[-1][2]

    def observe(self, timestamp: float) -> WorldState:
        event = self._event_at(timestamp)

        a_speaking = event in ("A_speaking", "interaction")
        b_speaking = event in ("B_speaking", "interaction")
        interaction = event == "interaction"
        product_visible = event == "product"

        if event == "A_speaking":
            active_speaker = "A"
        elif event == "B_speaking":
            active_speaker = "B"
        elif event == "interaction":
            active_speaker = None  # 两人同时说，视为互动
        else:
            active_speaker = None

        people = [
            PersonState(id="A", position=_PERSON_A_POS, speaking=a_speaking),
            PersonState(id="B", position=_PERSON_B_POS, speaking=b_speaking),
        ]

        return WorldState(
            timestamp=timestamp,
            scene="interview",
            people=people,
            active_speaker=active_speaker,
            interaction=interaction,
            product_visible=product_visible,
        )
