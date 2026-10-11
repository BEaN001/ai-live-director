"""VLM 感知适配器（占位）。

设计原则：VLM 只负责「理解现场」，绝不直接控制摄像机。

Phase 1 计划接入 Qwen2.5-VL 等开源 VLM，把多帧视频理解成：
    scene / people / interaction / product_visible / event
然后由 Director 依据这些语义做摄影决策。

本文件仅保留接口与使用示例，v0.1（Phase 0）不实现，避免引入模型依赖。
"""
from __future__ import annotations

from typing import List

from app.schemas import WorldState


class VLMAdapter:
    """把视频帧/音频语义化，输出结构化现场信息（Phase 1 实现）。"""

    def __init__(self, model_name: str = "Qwen/Qwen2.5-VL-7B-Instruct"):
        self.model_name = model_name
        raise NotImplementedError(
            "VLMAdapter 为 Phase 1 预留接口，v0.1 不实现。"
            "当前请使用 MockPerception（app.perception.mock）。"
        )

    def observe(self, frames: List, timestamp: float) -> WorldState:
        """输入：多帧画面（可选音频）；输出：结构化 WorldState。"""
        raise NotImplementedError
