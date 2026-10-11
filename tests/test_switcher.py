"""导播切换器测试。"""
import numpy as np

from app.camera.virtual_camera import VirtualCamera
from app.schemas import ActionType, CameraAction, ShotType
from app.switcher.switcher import Switcher
from app.world.state_manager import StateManager


def _make_switcher():
    defs = [
        {"id": "CAM1", "crop": [0, 0, 640, 360], "shot": "TWO_SHOT", "target": "both"},
        {"id": "CAM2", "crop": [0, 0, 320, 360], "shot": "MEDIUM_CLOSE_UP", "target": "person_A"},
    ]
    sm = StateManager(defs)
    cams = {
        c["id"]: VirtualCamera(c["id"], tuple(c["crop"]), ShotType(c["shot"]), c["target"])
        for c in defs
    }
    return Switcher(cams, sm, program_size=(640, 360))


def _frame():
    return np.zeros((360, 640, 3), dtype=np.uint8)


def test_switch_changes_current_camera():
    sw = _make_switcher()
    out = sw.apply(CameraAction(ActionType.SWITCH_CAMERA, "CAM2", ShotType.MEDIUM_CLOSE_UP), _frame())
    assert sw.state_manager.current_camera_id == "CAM2"
    assert out.shape == (360, 640, 3)


def test_hold_keeps_current():
    sw = _make_switcher()
    sw.apply(CameraAction(ActionType.HOLD), _frame())
    assert sw.state_manager.current_camera_id == "CAM1"


def test_unknown_camera_ignored():
    sw = _make_switcher()
    sw.apply(CameraAction(ActionType.SWITCH_CAMERA, "CAM99", ShotType.WIDE), _frame())
    assert sw.state_manager.current_camera_id == "CAM1"


def test_previews_return_all_cameras():
    sw = _make_switcher()
    previews = sw.previews(_frame(), size=(160, 90))
    assert set(previews.keys()) == {"CAM1", "CAM2"}
    assert all(v.shape == (90, 160, 3) for v in previews.values())
