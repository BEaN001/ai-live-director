"""Shot Quality：机位质量打分（Phase 0 规则版）。

用于「为什么这么拍」的可解释性：
给每个机位一个 0~1 的质量分，衡量它是否对准当前关键事件/人物。
该评测逻辑独立于导演决策逻辑，避免「既当运动员又当裁判」。
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from app.schemas import WorldState


def expected_camera_id(world_state: WorldState) -> str:
    """返回当前事件「理想」应使用的机位（独立评测基准）。"""
    if world_state.product_visible:
        return "CAM4"
    if world_state.interaction:
        return "CAM1"
    if world_state.active_speaker == "A":
        return "CAM2"
    if world_state.active_speaker == "B":
        return "CAM3"
    return "CAM1"


def score_camera(camera_id: str, world_state: WorldState) -> float:
    """单机位质量分：对准关键事件得 1.0，否则 0.4。"""
    return 1.0 if camera_id == expected_camera_id(world_state) else 0.4


def rank_cameras(camera_ids: List[str],
                 world_state: WorldState) -> List[Tuple[str, float]]:
    """按质量分降序排列所有机位。"""
    scored = [(cid, score_camera(cid, world_state)) for cid in camera_ids]
    return sorted(scored, key=lambda x: -x[1])


def quality_map(camera_ids: List[str],
                world_state: WorldState) -> Dict[str, float]:
    """所有机位的质量分字典。"""
    return {cid: score_camera(cid, world_state) for cid in camera_ids}
