"""引擎端到端冒烟测试。"""
from app.engine import DirectorEngine


def test_engine_first_tick_switches_to_cam2():
    engine = DirectorEngine()
    result = engine.step(0)  # t=0，A 讲话
    assert result.action.camera == "CAM2"
    assert result.current_camera_id == "CAM2"
    assert result.program_frame is not None
    assert result.previews is not None


def test_engine_full_run():
    engine = DirectorEngine()
    cameras_seen = set()
    for tick in range(engine.total_ticks):
        result = engine.step(tick)
        cameras_seen.add(result.current_camera_id)
    # 完整时间线应覆盖 CAM2(A) / CAM3(B) / CAM1(互动) / CAM4(产品)
    assert {"CAM1", "CAM2", "CAM3", "CAM4"} <= cameras_seen


def test_engine_reset_restarts_from_cam1():
    engine = DirectorEngine()
    engine.step(0)
    engine.reset()
    result = engine.step(0)
    assert result.current_camera_id == "CAM2"  # 复位后首个决策仍切到 CAM2
