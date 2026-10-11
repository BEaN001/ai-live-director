"""DirectorMetrics：从决策日志统计导演行为指标。

回答面试官常问的「你怎么证明 AI 拍得好？」：
    - 切镜总次数 / 平均镜头时长（避免 1 秒一切）
    - 不合理切镜率（Bad Cut Rate，两次切镜间隔 < 最短时长）
"""
from __future__ import annotations

from typing import Any, Dict, List


def compute_metrics(entries: List[Dict[str, Any]],
                    min_shot_duration: float = 3.0) -> Dict[str, Any]:
    """根据决策日志条目计算导演指标。

    entries: DecisionLog.entries 的列表（每条含 timestamp / decision.action / decision.camera）
    """
    switches = [
        (e["timestamp"], e["decision"]["camera"])
        for e in entries
        if e["decision"]["action"] == "SWITCH_CAMERA"
    ]
    holds = [e for e in entries if e["decision"]["action"] == "HOLD"]

    # 每个机位的持续时长 = 下次切镜时间 - 本次切镜时间（最后一次用日志末尾时间）
    end_time = entries[-1]["timestamp"] if entries else 0.0
    durations: List[float] = []
    bad_cuts = 0
    for i, (t, _cam) in enumerate(switches):
        next_t = switches[i + 1][0] if i + 1 < len(switches) else end_time
        dur = next_t - t
        durations.append(dur)
        if i > 0 and (t - switches[i - 1][0]) < min_shot_duration:
            bad_cuts += 1

    avg_duration = (sum(durations) / len(durations)) if durations else 0.0

    return {
        "total_ticks": len(entries),
        "switch_count": len(switches),
        "hold_count": len(holds),
        "avg_shot_duration": round(avg_duration, 2),
        "min_shot_duration": round(min(durations), 2) if durations else 0.0,
        "max_shot_duration": round(max(durations), 2) if durations else 0.0,
        "bad_cut_count": bad_cuts,
        "bad_cut_rate": round(bad_cuts / len(switches), 4) if switches else 0.0,
    }
