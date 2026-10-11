"""SceneSimulator：用 OpenCV 合成「两人访谈」演播室场景画面。

Phase 0 不读取任何真实视频，直接绘制一个可被虚拟多机位裁切的场景：
    - 演播室背景 + 地面
    - 人物 A（左）、人物 B（右）
    - 说话人指示（光圈 + 声波条）
    - 产品（中心下方，product_visible 时显示）

人物锚点与 configs/cameras.yaml 中的 crop 区域一一对应。
"""
from __future__ import annotations

import cv2
import numpy as np

from app.schemas import WorldState


class SceneSimulator:
    """合成场景渲染器。"""

    # 人物与产品的固定锚点（像素坐标，基于 1280×720）
    PERSON_A_ANCHOR = (330, 330)
    PERSON_B_ANCHOR = (950, 330)
    PRODUCT_ANCHOR = (640, 560)

    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height

    def render(self, world_state: WorldState) -> np.ndarray:
        """根据世界状态渲染一帧合成场景。"""
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self._draw_background(img)

        a_speaking = any(p.id == "A" and p.speaking for p in world_state.people)
        b_speaking = any(p.id == "B" and p.speaking for p in world_state.people)
        self._draw_person(img, self.PERSON_A_ANCHOR, "A", a_speaking)
        self._draw_person(img, self.PERSON_B_ANCHOR, "B", b_speaking)

        if world_state.product_visible:
            self._draw_product(img)

        self._draw_hud(img, world_state)
        return img

    # ---- 绘制辅助 ----

    def _draw_background(self, img: np.ndarray) -> None:
        """渐变演播室背景 + 地面。"""
        top = (36, 38, 62)
        bottom = (22, 24, 40)
        for y in range(self.height):
            t = y / self.height
            color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
            img[y, :] = color
        # 地面分隔线
        cv2.line(img, (0, 620), (self.width, 620), (70, 74, 100), 2)

    def _draw_person(self, img: np.ndarray, anchor, label: str, speaking: bool) -> None:
        x, y = anchor
        # 身体（圆角矩形近似）
        cv2.rectangle(img, (x - 62, y + 30), (x + 62, y + 210), (64, 70, 96), -1)
        # 头部
        cv2.circle(img, (x, y), 52, (196, 168, 148), -1)
        # 标签
        cv2.putText(img, label, (x - 12, y - 70), cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (220, 220, 220), 2, cv2.LINE_AA)
        if speaking:
            # 说话人光圈
            cv2.circle(img, (x, y), 62, (80, 220, 120), 3)
            self._draw_speech_bars(img, x + 72, y - 40)

    def _draw_speech_bars(self, img: np.ndarray, x: int, y: int) -> None:
        """说话声波条（固定高度，保证输出可复现）。"""
        heights = [12, 26, 18, 30]
        for i, h in enumerate(heights):
            cv2.rectangle(img, (x + i * 12, y - h), (x + i * 12 + 6, y),
                          (80, 220, 120), -1)

    def _draw_product(self, img: np.ndarray) -> None:
        """产品（手机）特写区域绘制。"""
        x, y = self.PRODUCT_ANCHOR
        # 手机机身
        cv2.rectangle(img, (x - 70, y - 100), (x + 70, y + 120), (40, 42, 58), -1)
        # 屏幕
        cv2.rectangle(img, (x - 60, y - 90), (x + 60, y + 100), (120, 200, 240), -1)
        cv2.putText(img, "PRODUCT", (x - 58, y + 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (20, 30, 40), 2, cv2.LINE_AA)
        # 高亮边框
        cv2.rectangle(img, (x - 76, y - 106), (x + 76, y + 126), (90, 200, 255), 3)

    def _draw_hud(self, img: np.ndarray, world_state: WorldState) -> None:
        """左上角信息：时间戳 + 场景。"""
        text = f"STUDIO  |  t={world_state.timestamp:05.1f}s  |  {world_state.scene}"
        cv2.putText(img, text, (20, 36), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (200, 200, 200), 2, cv2.LINE_AA)
