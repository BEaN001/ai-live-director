"""导出效果截图：在关键时间点保存节目帧为 PNG（README 展示用）。

用法：
    python scripts/export_frames.py
产出：
    docs/images/cam2_speaking_A.png  ... 等 4 张关键帧
"""
from __future__ import annotations

import sys
from pathlib import Path

# 保证直接 `python scripts/export_frames.py` 运行时能导入 app 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2

from app.engine import DirectorEngine, PROJECT_ROOT

IMAGES_DIR = PROJECT_ROOT / "docs" / "images"

# (时间点秒, 输出文件名) —— 对应四个事件段的代表性帧
TARGETS = [
    (2.5, "cam2_speaking_A.png"),
    (7.5, "cam3_speaking_B.png"),
    (12.5, "cam1_interaction.png"),
    (17.5, "cam4_product.png"),
]


def run() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    engine = DirectorEngine()
    ticks = {int(t * engine.fps): name for t, name in TARGETS}

    for tick in range(engine.total_ticks):
        result = engine.step(tick)
        if tick in ticks:
            path = IMAGES_DIR / ticks[tick]
            cv2.imwrite(str(path), result.program_frame)
            print(f"已导出 {path}")

    print("截图导出完成。")


if __name__ == "__main__":
    run()
