# 架构与数据流

## 1. 模块划分

```text
ai-live-director/
├── app/
│   ├── schemas.py            # 核心数据结构（WorldState / CameraAction / ShotType ...）
│   ├── engine.py             # DirectorEngine：装配各层，按 tick 驱动闭环
│   ├── main.py               # CLI 离线入口（输出 program.mp4 + director_log.jsonl）
│   ├── server.py             # FastAPI + WebSocket 实时 Dashboard
│   ├── perception/           # 感知层（mock.py 脚本化时间线；vlm_adapter.py 占位）
│   ├── world/                # state_manager.py：汇总感知 + 机位状态 → WorldState
│   ├── director/             # rule_based.py + state_machine.py；llm_director.py 占位
│   ├── camera/               # simulator.py 合成场景；virtual_camera.py 虚拟机位；ptz_adapter.py 占位
│   ├── switcher/             # switcher.py：执行 CameraAction → 节目输出
│   ├── evaluation/           # shot_quality.py + director_metrics.py 评测
│   └── utils/                # decision_log.py + video_writer.py
├── configs/                  # cameras.yaml（机位/裁剪）+ director.yaml（导演参数）
├── tests/                    # 单元测试 + 引擎冒烟测试
└── docs/                     # 本文档 + DESIGN.md
```

## 2. 单步数据流（一个 tick）

```text
tick → timestamp = tick / fps
         │
         ▼
┌─────────────────────┐
│ Perception.observe  │   MockPerception 按时间线返回 WorldState（无 camera）
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ StateManager.merge  │   填入当前输出机位状态 → 完整 WorldState（Observation）
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  Director.decide    │   RuleBasedDirector：状态机 + 最小镜头时长 → CameraAction
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  Simulator.render   │   用 OpenCV 合成全场景帧（两人 + 说话指示 + 产品）
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   Switcher.apply    │   执行 SWITCH_CAMERA / HOLD，裁切当前机位 → 节目帧
└──────────┬──────────┘
           ▼
    program_frame + previews（写入视频 / 推给 Dashboard）
           │
           ▼
┌─────────────────────┐
│  DecisionLog.record │   记录 Observation → Decision → Action（JSONL）
└─────────────────────┘
```

## 3. 时间线（MockPerception，25s）

| 时间 | 事件 | 目标机位 / 景别 |
|---|---|---|
| 0–5s | A 讲话 | CAM2 / MCU |
| 5–10s | B 讲话 | CAM3 / MCU |
| 10–15s | 双方互动 | CAM1 / Two Shot |
| 15–20s | 产品展示 | CAM4 / Product CU |
| 20–25s | A 再讲话 | CAM2 / MCU |

## 4. 替换点（未来演进）

- `MockPerception` → `RealPerception`（YOLO + ByteTrack + 说话人检测）
- `RuleBasedDirector` → `LLMDirector`（结构化输出）→ `VLADirector`（端到端）
- `VirtualCamera` → `RealPTZController`（VISCA / ONVIF / SDK）

三处替换均不改 `WorldState` / `CameraAction` 接口。
