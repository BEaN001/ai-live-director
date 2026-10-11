"""LLM 导演（占位）。

Phase 1 计划把 RuleBasedDirector 替换为 LLM 导演：
输入 WorldState + 用户指令 + 历史动作，输出结构化 CameraAction。

系统提示词（设计草案）：
    你是一名专业直播导演。根据当前直播状态选择最合适的摄影机和镜头。
    摄影原则：
    1. 当前讲话人优先。
    2. 单人讲话使用 Medium Close Up。
    3. 两人互动使用 Two Shot。
    4. 产品展示使用 Product Close Up。
    5. 避免频繁切镜，单个镜头至少保持 3 秒。
    6. 只能输出定义好的 CameraAction。

v0.1（Phase 0）不实现，避免引入模型/API 依赖。
"""
from __future__ import annotations

from app.director.base import Director
from app.schemas import CameraAction, WorldState


class LLMDirector(Director):
    """基于 LLM + 结构化输出的导演（Phase 1 实现）。"""

    def __init__(self, model_name: str = "qwen2.5-72b-instruct"):
        self.model_name = model_name
        raise NotImplementedError(
            "LLMDirector 为 Phase 1 预留接口，v0.1 不实现。"
            "当前请使用 RuleBasedDirector（app.director.rule_based）。"
        )

    def decide(self, world_state: WorldState) -> CameraAction:
        raise NotImplementedError
