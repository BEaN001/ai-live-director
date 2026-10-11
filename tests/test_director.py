"""规则导演决策逻辑测试。"""
from pathlib import Path

import yaml

from app.director.rule_based import RuleBasedDirector
from app.director.state_machine import DirectorState, classify_state
from app.schemas import ActionType, PersonState, WorldState

_DIRECTOR_CONFIG = Path(__file__).resolve().parent.parent / "configs" / "director.yaml"


def _load_config():
    return yaml.safe_load(_DIRECTOR_CONFIG.read_text(encoding="utf-8"))


def _make_ws(t, speaker=None, interaction=False, product=False):
    people = [
        PersonState("A", (0.3, 0.5), speaking=(speaker == "A" or interaction)),
        PersonState("B", (0.7, 0.5), speaking=(speaker == "B" or interaction)),
    ]
    return WorldState(
        timestamp=t, people=people, active_speaker=speaker,
        interaction=interaction, product_visible=product,
    )


def test_a_speaking_switches_to_cam2():
    d = RuleBasedDirector(_load_config())
    a = d.decide(_make_ws(0.0, speaker="A"))
    assert a.action == ActionType.SWITCH_CAMERA
    assert a.camera == "CAM2"


def test_min_shot_duration_holds():
    d = RuleBasedDirector(_load_config())
    d.decide(_make_ws(0.0, speaker="A"))
    a = d.decide(_make_ws(1.0, speaker="A"))
    assert a.action == ActionType.HOLD
    assert a.camera is None


def test_b_speaking_switches_to_cam3_after_duration():
    d = RuleBasedDirector(_load_config())
    d.decide(_make_ws(0.0, speaker="A"))
    a = d.decide(_make_ws(4.0, speaker="B"))
    assert a.action == ActionType.SWITCH_CAMERA
    assert a.camera == "CAM3"


def test_interaction_switches_to_cam1():
    d = RuleBasedDirector(_load_config())
    d.decide(_make_ws(0.0, speaker="A"))
    a = d.decide(_make_ws(5.0, interaction=True))
    assert a.action == ActionType.SWITCH_CAMERA
    assert a.camera == "CAM1"


def test_product_switches_to_cam4():
    d = RuleBasedDirector(_load_config())
    d.decide(_make_ws(0.0, speaker="A"))
    a = d.decide(_make_ws(5.0, product=True))
    assert a.action == ActionType.SWITCH_CAMERA
    assert a.camera == "CAM4"


def test_classify_state_priority():
    assert classify_state(_make_ws(0, product=True)) == DirectorState.PRODUCT
    assert classify_state(_make_ws(0, interaction=True)) == DirectorState.TWO_SHOT
    assert classify_state(_make_ws(0, speaker="A")) == DirectorState.FOCUS_A
    assert classify_state(_make_ws(0, speaker="B")) == DirectorState.FOCUS_B
    assert classify_state(_make_ws(0)) == DirectorState.IDLE
