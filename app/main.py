"""CLI 入口：离线跑通完整闭环，输出节目视频 + 决策日志 + 指标摘要。

用法：
    python -m app.main

产出：
    outputs/program.mp4         节目输出（AI 自动导播的最终成片）
    outputs/director_log.jsonl  每一次导演决策（未来 VLA 数据集雏形）
"""
from __future__ import annotations

from pathlib import Path

from app.engine import DirectorEngine, PROJECT_ROOT
from app.evaluation.director_metrics import compute_metrics
from app.evaluation.shot_quality import expected_camera_id
from app.utils.decision_log import DecisionLog
from app.utils.video_writer import VideoWriter

OUTPUT_DIR = PROJECT_ROOT / "outputs"


def run() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    program_path = OUTPUT_DIR / "program.mp4"
    log_path = OUTPUT_DIR / "director_log.jsonl"

    engine = DirectorEngine()
    writer = VideoWriter(str(program_path), fps=engine.fps, size=engine.program_size)
    log = DecisionLog(str(log_path))

    # 覆盖率统计：执行后的机位是否对准当前关键事件
    matched = 0

    print("=" * 72)
    print("AI LIVE DIRECTOR v0.1 —— 离线仿真开始")
    print(f"场景：两人访谈（{engine.duration:.0f}s @ {engine.fps:.0f}fps）")
    print("=" * 72)

    for tick in range(engine.total_ticks):
        result = engine.step(tick)
        ws = result.world_state

        # 写节目帧 + 记录决策
        writer.write(result.program_frame)
        log.record(ws, result.action)

        # 覆盖率：执行后的当前机位是否等于理想机位
        if result.current_camera_id == expected_camera_id(ws):
            matched += 1

        # 控制台输出（仅切镜与关键动作时打印，避免刷屏）
        if result.action.action.value == "SWITCH_CAMERA":
            print(f"[{ws.timestamp:6.1f}s] speaker={ws.active_speaker} "
                  f"interaction={ws.interaction} product={ws.product_visible}")
            print(f"   => {result.action.action.value} {result.action.camera}"
                  f" | {result.action.reason}")

    writer.close()
    log.close()

    metrics = compute_metrics(log.entries, min_shot_duration=engine.director.min_shot_duration)
    coverage = matched / engine.total_ticks if engine.total_ticks else 0.0

    print("=" * 72)
    print("仿真结束，产出：")
    print(f"  节目视频  -> {program_path}")
    print(f"  决策日志  -> {log_path}")
    print("-" * 72)
    print("导演指标：")
    print(f"  切镜次数        : {metrics['switch_count']}")
    print(f"  平均镜头时长    : {metrics['avg_shot_duration']}s")
    print(f"  最短镜头时长    : {metrics['min_shot_duration']}s")
    print(f"  不合理切镜数    : {metrics['bad_cut_count']}"
          f"（Bad Cut Rate = {metrics['bad_cut_rate']}）")
    print(f"  事件覆盖率      : {coverage * 100:.1f}%")
    print("=" * 72)


if __name__ == "__main__":
    run()
