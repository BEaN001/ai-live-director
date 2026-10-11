# AI Live Director —— 技术方案总结（v0.1）

> 本文是从「VLA + World Model AI 摄影师 / AI 导播」相关讨论中提炼的技术方案总结，
> 也是本仓库设计与后续演进（Phase 0 → 1 → 2 → 3）的纲领性文档。

---

## 1. 背景与定位

传统「AI 摄像机」主要解决一个 CV 问题：

> **「人在哪里，我怎么跟着他？」**（检测 → 跟踪 → 保持人在画面中央）

本项目的目标更进一层，解决的是摄影/导播决策问题：

> **「现场发生了什么？现在应该拍谁？用什么景别？哪个机位最好？摄像机该怎么动？什么时候切镜？」**

一句话定位：

> **让摄像机从「被动记录设备」，升级为「具备感知、决策与执行能力的 AI 摄影师 / AI 导播 Agent」。**

这是从「AI 跟拍」到「AI 摄影师」再到「AI 导播」的产品跃迁。

---

## 2. 竞品与差异化

| 公司/方向 | AI 跟拍 | 自动构图 | PTZ | 多机位 | AI 导播 | VLA | World Model |
|---|---:|---:|---:|---:|---:|---:|---:|
| OBSBOT 寻影 | ★★★★★ | ★★★★★ | ★★★★★ | ★★★ | ★★★ | ★ | ★ |
| Huddly | ★★★★ | ★★★★ | ★★★ | ★★★★★ | ★★★★ | ★ | ★ |
| Visor | ★ | ★★ | ★ | ★★★★★ | ★★★★★ | ★★ | ★ |
| TrackGoX | ★★★★★ | ★★★ | ★★★★ | ★ | ★★ | ★★ | ★ |
| **本项目方向** | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ |

**差异化定位：VLA-native AI Director**

现有方案大多还是「规则系统 + PTZ 控制器」：

```text
if person_left:   pan_left()
if face_too_small: zoom_in()
if speaker_changed: switch_camera()
```

而目标架构是「理解节目 → 理解镜头语言 → 理解空间 → 自主控制摄像机与导播台」，
把摄影决策（Cinematography Policy）从「目标跟踪」（Tracking Policy）中分离出来。

---

## 3. 三层产品定义

- **Level 1 · AI Cameraman**：一台摄像机自己会拍（检测、跟踪、构图、变焦、运镜）。
- **Level 2 · AI Cinematographer**：理解「该怎么拍」——`场景理解 → 镜头规划 → 摄影动作`。
- **Level 3 · AI Live Director**：把多台摄像机、摄影师、导播台统一为一个 Agent。

```text
                 AI Director
                      │
          ┌───────────┴───────────┐
          ↓                       ↓
   AI Cinematographer        AI Switcher
          │                       │
     Camera Planning         Camera Selection
          │                       │
     ┌────┼────┐             ┌────┼────┐
     ↓    ↓    ↓             ↓    ↓    ↓
    PTZ  Zoom Focus         CAM1 CAM2 CAM3
          │                       │
          └──────────┬────────────┘
                     ↓
                Program Feed ──→ Live
```

---

## 4. 总体技术架构

核心闭环（也是简历中描述的架构）：

```text
Video Perception → World State → Director → Camera Action → Program Output
```

分层展开：

```text
┌─────────────── User Intent ───────────────┐
│ "帮我拍一场两人访谈，重点拍讲话的人"       │
└────────────────────┬─────────────────────┘
                     ↓
┌──────────── Multimodal Perception ────────┐
│ Video / Audio / Person / Face / Object / Event │
└────────────────────┬─────────────────────┘
                     ↓
┌────────────── World State ────────────────┐
│ 人物 / 物体 / 空间 / 摄像机 / 事件 / 时间   │
└────────────────────┬─────────────────────┘
                     ↓
┌──────────── World Model（可选）────────────┐
│ 3D Scene / Camera Pose / Depth / Future View │
└────────────────────┬─────────────────────┘
                     ↓
┌────────── VLA / AI Director ──────────────┐
│ Understand → Reason → Plan → Action        │
└────────────────────┬─────────────────────┘
                     ↓
┌──────────── Camera Planner ───────────────┐
│ Shot / Camera / Motion / Zoom / Duration   │
└────────────────────┬─────────────────────┘
                     ↓
┌──────────── Camera Controller ────────────┐
│ VISCA / ONVIF / NDI / SDK / PTZ            │
└────────────────────┬─────────────────────┘
                     ↓
               Physical Cameras → Live
```

---

## 5. 核心数据结构

### WorldState（Observation，未来 VLA 的输入）

```json
{
  "timestamp": 123.5,
  "scene": "interview",
  "people": [
    {"id": "A", "position": [0.31, 0.47], "speaking": true},
    {"id": "B", "position": [0.68, 0.46], "speaking": false}
  ],
  "active_speaker": "A",
  "interaction": false,
  "product_visible": true,
  "camera": {"id": "CAM2", "shot": "MEDIUM_CLOSE_UP", "target": "person_A"}
}
```

### CameraAction（Action，与底层硬件解耦）

```json
{
  "action": "SWITCH_CAMERA",
  "camera": "CAM2",
  "shot": "MEDIUM_CLOSE_UP",
  "duration": 4.0,
  "reason": "A 是当前发言人",
  "confidence": 0.95
}
```

这两个接口把「人物 / 说话人 / 互动事件」与「摄像机动作」解耦，
因此规则策略、LLM、VLM、VLA 之间可以**渐进替换而不改上下层**。

---

## 6. Camera Action Space

定义三层动作，**大模型只输出高层动作，绝不直接控制电机**：

```text
Level 1 语义动作    TRACK(A)  /  FOCUS(B)  /  SHOW_PRODUCT  /  SWITCH_TO_CAMERA_2
Level 2 摄影动作    SHOT(MEDIUM)  SHOT(CLOSE_UP)  SHOT(TWO_SHOT)  PUSH_IN  PAN_LEFT  TILT_UP
Level 3 连续控制    pan=0.25  tilt=-0.12  zoom=1.15  duration=2.5s
```

分层关系：

```text
VLA → Semantic Action → Shot Planner → Continuous Controller → PTZ
```

配合「摄影语言」：景别（WS/MS/MCU/CU/Two Shot/OTS）、构图（三分法/头留白/视线留白）、
运镜（推/拉/摇/移/跟）、节奏（快切/慢推/静止）。

---

## 7. 导演状态机与规则

用离散状态机保证切镜语义稳定，避免「CAM1→CAM2→CAM1」式抽风：

```text
IDLE ──A讲话──→ FOCUS_A ──B讲话──→ FOCUS_B ──互动──→ TWO_SHOT ──产品──→ PRODUCT
```

事件优先级：**产品展示 > 双方互动 > 单人讲话 > 无事件**。

并引入 **最小镜头时长（min_shot_duration = 3s）**，防止频繁切镜。
每个动作附带 `reason` / `confidence`，用于回答「为什么这么拍」。

---

## 8. 演进路线（Roadmap）

| 阶段 | 决策层 | 感知层 | 执行层 |
|---|---|---|---|
| **Phase 0（本仓库）** | 规则导演 + 状态机 | MockPerception（脚本化时间线） | 虚拟多机位（crop） |
| Phase 1 | LLM / VLM 导演 | YOLO + 说话人检测 + VLM | 虚拟多机位 + 真实视频 |
| Phase 2 | 同上 | 同上 | 真实 PTZ（VISCA / ONVIF） |
| Phase 3 | VLA Policy | 端到端 Observation | Camera Agent |

数据飞轮：`DecisionLog（Observation → Action）` 持续积累，
即未来 VLA 行为克隆 / SFT 训练数据集的雏形。

---

## 9. 关键设计原则

1. **VLM 只负责理解现场，不直接控制摄像机**——架构上强制「感知」与「决策」分离。
2. **Action Space 与硬件解耦**——换硬件不重做决策层。
3. **规则优先，AI 渐进替换**——先用规则跑通闭环，再逐步替换 LLM/VLM/VLA。
4. **可解释、可评测**——每个决策有 reason/confidence，并有切镜频率、镜头时长、覆盖率等指标。
5. **Decision Log 即数据资产**——每一次决策都是未来训练数据的一条样本。
