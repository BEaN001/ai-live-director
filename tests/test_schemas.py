"""数据结构序列化测试。"""
from app.schemas import (
    ActionType,
    CameraAction,
    CameraState,
    PersonState,
    ShotType,
    WorldState,
)


def test_shot_type_values():
    assert ShotType.MEDIUM_CLOSE_UP.value == "MEDIUM_CLOSE_UP"
    assert ShotType.TWO_SHOT.value == "TWO_SHOT"


def test_world_state_to_dict():
    ws = WorldState(
        timestamp=1.0,
        people=[PersonState("A", (0.3, 0.5), True)],
        active_speaker="A",
        camera=CameraState("CAM2", ShotType.MEDIUM_CLOSE_UP, target="person_A"),
    )
    d = ws.to_dict()
    assert d["active_speaker"] == "A"
    assert d["camera"]["id"] == "CAM2"
    assert d["camera"]["shot"] == "MEDIUM_CLOSE_UP"
    assert d["people"][0]["speaking"] is True


def test_camera_action_to_dict():
    a = CameraAction(
        ActionType.SWITCH_CAMERA, "CAM2", ShotType.MEDIUM_CLOSE_UP,
        4.0, "A 是当前发言人", 0.95,
    )
    d = a.to_dict()
    assert d["action"] == "SWITCH_CAMERA"
    assert d["camera"] == "CAM2"
    assert d["shot"] == "MEDIUM_CLOSE_UP"
    assert d["confidence"] == 0.95
