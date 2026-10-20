# AI Live Director —— 决策头蒸馏方案（JEV 方案）设计

> 把 [autotrust/JEV-27B-VL](https://huggingface.co/autotrust/JEV-27B-VL) 的「决策头蒸馏」训练方案，
> 迁移到本项目的 **Director 层**：训练一个能输出「校准的摄影决策分布」的决策模型，替换 `RuleBasedDirector`。
> 本文是 `DESIGN.md` 的后续演进方案，对应 Roadmap 的 Phase 1 → 2。

---

## 1. 背景与目标

本项目的核心是「导演决策」：`WorldState → CameraAction`。当前 Phase 0 用 `RuleBasedDirector`
（`classify_state()` 状态机 + 查表）。JEV 方案的目标是把它升级成一个**学习出来的决策模型**：

- 输入 `WorldState`（Observation），输出**每个候选机位/景别的校准概率**；
- 决策头只在文本上训练，图像 zero-shot 泛化（复用 JEV-27B-VL 的机制）；
- 保持 `Director` 接口不变，`RuleBasedDirector` 平滑替换。

---

## 2. 核心映射（JEV → 本项目）

| JEV 方案 | 本项目 |
|---|---|
| `state`（决策依赖的事实） | `WorldState`（序列化 JSON） |
| `options`（2~256 个命名选项） | 离散化的 `CameraAction`（见 §4） |
| 决策头（24 槽 choice） | Director 决策头（5 槽 choice） |
| 教师 TypeSafe Jev 1.13 | 规则导演 bootstrap → 强 VLM → 人工（见 §5） |
| backbone 冻结 + LoRA + 决策头 | 同一个 Blocks of Experts 配方 |
| 校准概率（bias + 温度） | 同上，概率直接当 `confidence` |

**关键澄清**：Phase 0 的 `WorldState` 已经是结构化抽象（speaker / interaction / product），不是像素。
所以 Director 是**文本决策**（JSON → 动作分布），**不需要看图**；「看图」是 Perception 层（YOLO + 说话人 + VLM）
的职责，与 Director 解耦。因此 Phase 1 用 JEV-27B（文本版）的思路，Phase 2 再上 JEV-27B-VL 的多模态 zero-shot。

---

## 3. 决策任务定义（把 Director 变成一个 choice 决策）

现在 `classify_state()` 输出 5 个离散状态 `IDLE/FOCUS_A/FOCUS_B/TWO_SHOT/PRODUCT`，再查表映射到
(camera, shot)。把它改造成 JEV 的 choice 决策：

```python
state    = json.dumps(world_state.to_dict())
question = "当前应该切到哪个机位和景别？"
options  = [
    "全景 CAM1",        # IDLE
    "A 中近景 CAM2",    # FOCUS_A
    "B 中近景 CAM3",    # FOCUS_B
    "双人镜头 CAM1",    # TWO_SHOT
    "产品特写 CAM4",    # PRODUCT
]
probs = decide("choice", state, question, options)   # → 5 个校准概率
```

prompt 落成 JEV 裸模板（`jev27-bare-v1`）：

```
[kind] choice
[state] {"active_speaker":"A","interaction":false,"product_visible":false,"people":[{"id":"A","speaking":true}...]}
[question] 当前应该切到哪个机位和景别？
[options]
A) 全景 CAM1
B) A 中近景 CAM2
C) B 中近景 CAM3
D) 双人镜头 CAM1
E) 产品特写 CAM4
[decision]:
```

### 关键设计：HOLD / 最短时长留在模型外

模型只输出「**此刻最优状态是什么**」，而「该不该真的切」（受 `min_shot_duration` 约束）是**后处理**：

```
模型分布 → argmax 得最优状态 → 映射到 (camera, shot)
                                    ↓
              复用 RuleBasedDirector 的最短时长逻辑 → SWITCH 或 HOLD
```

这样切镜节奏仍由确定性约束保证，模型只负责「怎么拍最好」，避免「抽风切镜」。

---

## 4. 动作空间离散化

`CameraAction` 有 6 个字段，Phase 1 建议**单级 choice over 5 个状态**：

| 字段 | 处理 |
|---|---|
| (action, camera, shot) | 5 个选项**联合编码**（选项文本带机位+景别） |
| duration | 后处理，沿用 config 的 `default_shot_duration` |
| confidence | **直接用模型概率**（JEV 白送） |
| reason | 从选中状态模板生成（复用 `director.yaml` 的 reason） |

> Phase 2/3 想加 ZOOM/TRACK/多景别，选项从 5 扩到 16+ 即可，JEV 的 choice 原生支持 2~256 个选项，训练框架不变。

---

## 5. 教师信号（JEV 有闭源教师，这里要自己造）

JEV 的 loss 是 `KL(teacher ‖ student)`，需要教师输出**概率分布**。本项目教师分三阶段：

### 阶段 A：规则导演 bootstrap（最快验证闭环）

- `SyntheticWorldStateGenerator`：随机采样时间线（发言人切换/互动/产品），批量生成 WorldState。
- 对每个跑 `classify_state()` 得硬标签（5 选 1），**软化成分布**作蒸馏目标：
  - 简单版：label smoothing（正确项 0.9，其余均分 0.1）。
  - 更好版：按优先级层次构造软分布（A 说话时 `P(FOCUS_A)=0.85, P(TWO_SHOT)=0.08, P(IDLE)=0.07`）。

> 目的：跑通「合成数据 → 蒸馏 → 部署替换」全链路，教师质量可不高。

### 阶段 B：强 VLM 蒸馏（对齐 JEV 原版）

- 强模型（GPT/Claude/Gemini 或 base Qwen3.8 配好 prompt）当「专家导演」。
- 喂 WorldState + 摄影原则 + 5 选项，**采样 N 次得频率分布**或直接输出每选项概率。
- 收集 (WorldState → VLM 分布) → KL 蒸馏进小模型。

> 教师 VLM 的分布有字母先验/未校准问题，但学生的决策头（lm_head 行初始化 + 训练 + bias/温度拟合）会修掉，
> JEV 卡片证明该流程能「青出于蓝」。

### 阶段 C：真实现场 + 人工标注（长期）

Phase 2 接真实视频后，用人工导播决策（多标注者 → 一致度分布）做 gold 教师，配合 `DecisionLog` 数据飞轮。

---

## 6. 模型与训练（照搬 Blocks of Experts）

```
backbone：Qwen3.8-27B 文本塔（或 Qwen3.5-9B 起步，更快更省）
  ├─ 冻结，bit-identical
  └─ System 1 块：
       backbone LoRA（q/k/v/o/gate/up/down_proj, r=16~32）
     + 决策头（5 槽 fp32，从 lm_head 的 5 个 verbalizer 行初始化）
```

| 项 | 取值 |
|---|---|
| loss | `KL(teacher_distribution ‖ student)` |
| 数据增强 | 30% 选项排列增强（读机位内容、不读 A/B/C/D 位置） |
| 调度 | cosine ~5000 step，冻结 backbone |
| 参数规模 | 只训 LoRA + 决策头（<1% backbone） |
| 决策头初始化 | 从 lm_head 行拷贝 → 第 0 步即「基座零样本导演」 |

---

## 7. 数据流水线

- 生成器：`app/datasets/synthetic_world_state.py` —— 随机时间线 → WorldState 批量。
- 标签器：`app/datasets/label_by_rule.py` / `label_by_vlm.py` —— 产出 `(prompt → 教师分布)`，格式对齐 `jev-distill-corpus-v3`。
- 已有资产复用：`DecisionLog` 的 `Observation → Decision → Action` 即数据雏形；`datasets/` 目录已预留。

---

## 8. 部署：保持 `Director` 接口不变

```python
# app/director/decision_model_director.py（新）
class DecisionModelDirector(Director):
    def decide(self, world_state) -> CameraAction:
        dist = client.decide("choice", json.dumps(world_state.to_dict()), QUESTION, OPTIONS)
        state = OPTION_TO_STATE[max(dist, key=dist.get)]
        return build_action(state, confidence=dist[state], reason=...)
        # 最短时长约束复用 RuleBasedDirector 逻辑
```

- `Director` 抽象接口（`base.py`）不动，`RuleBasedDirector` 平滑替换。
- 推理接 `decision_server.py` 的 `/v1/decide` 或本地 transformers。
- `confidence` 用模型概率，比规则导演手写 0.95 更可信。

---

## 9. 分阶段 Roadmap

| 阶段 | 教师 | 输入 | 决策模型 | 交付 |
|---|---|---|---|---|
| 1a | 规则 bootstrap | WorldState JSON | 文本决策头蒸馏 | 跑通「合成→蒸馏→替换」闭环 |
| 1b | 强 VLM 蒸馏 | WorldState JSON | 同上 | 决策质量对齐 JEV 原版 |
| 2 | VLM + 真实视频 | WorldState + 关键帧 | 多模态决策头（图像 zero-shot） | 真实输入 |
| 3 | 人工 + 飞轮 | 端到端 Observation | VLA policy | 生产 |

---

## 10. JEV 方案 vs VLA 方案

这是两条不同的演进路线，核心区别是「**输出离散决策分布**」还是「**直接输出连续动作**」。

| 维度 | JEV 方案（决策头蒸馏） | VLA 方案（Vision-Language-Action） |
|---|---|---|
| 输出 | 有限选项上的**校准概率分布** | 直接输出**动作**（连续值 / 动作 token 序列） |
| 动作空间 | 离散、预定义、可枚举（2~256 个命名选项） | 连续（pan/tilt/zoom 值）或大离散动作 token |
| 推理 | 单次前向 + 读 logits，**无自回归生成** | 通常自回归生成动作 token 或回归连续值 |
| 训练 | 知识蒸馏（KL 拟合教师分布） | 行为克隆（BC/SFT 模仿专家轨迹）+ RL 微调 |
| 校准 | 天然输出校准概率（可设阈值 / 升级 System 2） | 通常无校准置信度 |
| 架构 | 冻结 backbone + LoRA + 决策头（复用 lm_head） | 完整模型（视觉塔 + LLM + 动作解码头） |
| 速度 | ~0.1s / 决策 | 一般更慢（多步生成 / 回归） |
| 对应本项目动作层级 | **Level 1 语义动作 / Level 2 摄影动作** | **Level 3 连续控制 / 端到端** |

### 映射到 DESIGN.md 的三级动作空间

```
Level 1 语义动作   TRACK(A) / FOCUS(B) / SHOW_PRODUCT      ← JEV 方案
Level 2 摄影动作   SHOT(MEDIUM) / SHOT(CLOSE_UP) / PUSH_IN ← JEV 方案
Level 3 连续控制   pan=0.25  tilt=-0.12  zoom=1.15         ← VLA 方案
```

- **JEV 方案** = 在「拍谁、什么景别、切哪个机位」这类**离散、可枚举**的问题上做决策，输出「有多确定」。
- **VLA 方案** = 端到端从像素直接输出**连续控制量**（PTZ 的 pan/tilt/zoom），是「动作生成」而非「选择」。

### 什么时候用哪个

| | JEV 方案 | VLA 方案 |
|---|---|---|
| 动作空间 | 有限、离散、可枚举 | 连续 / 大离散 |
| 需求 | 校准概率做阈值/升级、要快、要可解释 | 精细连续运动控制 |
| 典型 | 选机位、选景别、预置位路由 | 平滑运镜、精确对焦跟踪 |

### 混合形态（本项目的自然演进）

「**JEV 做高层离散决策（选机位/景别）+ 传统 PTZ 控制器做连续执行**」是 JEV 方案的天然落地形态，
也正是 `DESIGN.md` 已经主张的原则——「大模型只输出高层动作，绝不直接控制电机」。VLA 是后续
Phase 3 把连续控制层也「学习化」的终极形态，两者可渐进叠加：

```
JEV 决策头（选机位/景别，校准概率）──▶ Shot Planner ──▶ 连续控制器（PTZ）
        ↑                                              ↑
    Phase 1/2（本方案）                           Phase 3 可换 VLA
```

---

## 11. 风险与开放问题

1. **教师分布质量是天花板**——规则 bootstrap 太「规则化」、VLM 教师有先验偏差，都可能被学生继承
   （JEV 也承认「fidelity extends to the teacher's mistakes」）。缓解：bias+温度在 held-out 上重拟合，且 Phase 1b 用强教师。
2. **动作空间会涨**：Phase 2 加 ZOOM/TRACK/多景别后 5 槽 → 16+ 槽，需重训决策头（框架不变）。
3. **置信度与最短时长的耦合**：模型输出「最优状态」，切镜节奏靠后处理；若以后想让模型决定「要不要现在切」，
   把 HOLD 也变成显式选项（choice 5→6，把「保持当前」当选项）。
4. **文本 vs 多模态的边界**：Phase 1 决策是文本（WorldState JSON），Phase 2 引入图像后，需要确认
   「图像 zero-shot 泛化」在本项目场景下的质量（JEV 证明了对通用视觉判断有效，但「导播」这种专业判断需自测）。
