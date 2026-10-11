"""DirectorEngine：驱动「Perception → WorldState → Director → CameraAction → Program」闭环。

这是整个项目的核心装配点，把各层串起来按 tick 推进：
    1. Perception.observe(t)      → WorldState（现场发生了什么）
    2. StateManager.merge(...)    → 补上当前机位状态
    3. Director.decide(...)       → CameraAction（应该怎么拍）
    4. Switcher.apply(...)        → 节目输出帧（实际切到哪个机位）

CLI（app.main）与 Dashboard（app.server）都复用同一个引擎，保证行为一致。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import yaml

from app.camera.simulator import SceneSimulator
from app.camera.virtual_camera import VirtualCamera
from app.director.rule_based import RuleBasedDirector
from app.perception.mock import MockPerception
from app.schemas import CameraAction, ShotType, WorldState
from app.switcher.switcher import Switcher
from app.world.state_manager import StateManager

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CAMERAS_CONFIG = PROJECT_ROOT / "configs" / "cameras.yaml"
DIRECTOR_CONFIG = PROJECT_ROOT / "configs" / "director.yaml"


@dataclass
class StepResult:
    """单个时间步的运行结果。"""

    world_state: WorldState            # 决策前的世界状态（含当前机位）
    action: CameraAction               # 导演动作
    scene_frame: np.ndarray            # 合成全场景帧
    program_frame: np.ndarray          # 节目输出帧
    previews: Dict[str, np.ndarray]    # 各机位预览帧
    current_camera_id: str             # 执行后的当前机位
    current_shot: ShotType             # 执行后的当前景别


class DirectorEngine:
    """AI 导播引擎。"""

    def __init__(self,
                 cameras_config: Optional[Path] = None,
                 director_config: Optional[Path] = None):
        cam_path = cameras_config or CAMERAS_CONFIG
        dir_path = director_config or DIRECTOR_CONFIG

        self.cam_cfg = yaml.safe_load(cam_path.read_text(encoding="utf-8"))
        self.dir_cfg = yaml.safe_load(dir_path.read_text(encoding="utf-8"))

        self.fps: float = float(self.cam_cfg.get("fps", 10))
        self.duration: float = float(self.cam_cfg.get("duration", 25.0))
        scene = self.cam_cfg.get("scene", {})
        out = self.cam_cfg.get("output", {})
        self.program_size: Tuple[int, int] = tuple(out.get("program", [1280, 720]))
        self.preview_size: Tuple[int, int] = tuple(out.get("preview", [320, 180]))

        # 各层组件
        self.simulator = SceneSimulator(scene.get("width", 1280), scene.get("height", 720))
        self.perception = MockPerception(total_duration=self.duration)
        self.state_manager = StateManager(self.cam_cfg.get("cameras", []))
        self.director = RuleBasedDirector(self.dir_cfg)
        self.switcher = self._build_switcher()

    def _build_switcher(self) -> Switcher:
        cameras: Dict[str, VirtualCamera] = {}
        for c in self.cam_cfg.get("cameras", []):
            cameras[c["id"]] = VirtualCamera(
                camera_id=c["id"],
                crop_box=tuple(c.get("crop", [0, 0, 1280, 720])),
                shot=ShotType(c.get("shot", "WIDE")),
                target=c.get("target"),
                position_label=c.get("position_label", "front"),
            )
        return Switcher(cameras, self.state_manager, program_size=self.program_size)

    @property
    def total_ticks(self) -> int:
        return int(self.duration * self.fps)

    def reset(self) -> None:
        """复位到初始状态（用于 Dashboard 循环播放）。"""
        self.state_manager.reset()
        self.director.reset()

    def step(self, tick: int) -> StepResult:
        """推进一个时间步，返回该步结果。"""
        timestamp = tick / self.fps

        # 1. 感知 → 2. 合并当前机位状态
        perceived = self.perception.observe(timestamp)
        world_state = self.state_manager.merge(perceived)

        # 3. 导演决策
        action = self.director.decide(world_state)

        # 4. 渲染全场景 → 执行动作 → 输出节目帧 + 机位预览
        scene_frame = self.simulator.render(world_state)
        program_frame = self.switcher.apply(action, scene_frame)
        previews = self.switcher.previews(scene_frame, size=self.preview_size)

        return StepResult(
            world_state=world_state,
            action=action,
            scene_frame=scene_frame,
            program_frame=program_frame,
            previews=previews,
            current_camera_id=self.state_manager.current_camera_id,
            current_shot=self.state_manager.current_shot,
        )
