"""FastAPI + WebSocket 入口：实时 Dashboard。

用法：
    python -m app.server            # 或 uvicorn app.server:app
    # 浏览器打开 http://127.0.0.1:8000

每个连接独立驱动一个引擎实例，按压缩后的「直播节奏」循环播放仿真，
通过 WebSocket 把节目画面、机位预览、世界状态、导演决策实时推给前端。
"""
from __future__ import annotations

import asyncio
import base64
from pathlib import Path

import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.engine import DirectorEngine

STATIC_DIR = Path(__file__).resolve().parent / "web" / "static"

app = FastAPI(title="AI Live Director v0.1")

# 仪表盘推流节奏（秒/步）：25s 仿真压缩到约 12s 播完
TICK_DELAY = 0.05
PROGRAM_MAX_WIDTH = 960


def _encode(frame, max_width: int = None) -> str:
    """把帧编码为 JPEG base64 字符串。"""
    if max_width is not None and frame.shape[1] > max_width:
        scale = max_width / frame.shape[1]
        frame = cv2.resize(frame, (max_width, int(frame.shape[0] * scale)))
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
    return base64.b64encode(buf.tobytes()).decode("ascii")


@app.get("/")
async def index() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    engine = DirectorEngine()
    try:
        while True:
            engine.reset()
            for tick in range(engine.total_ticks):
                result = engine.step(tick)
                await ws.send_json({
                    "type": "step",
                    "world_state": result.world_state.to_dict(),
                    "action": result.action.to_dict(),
                    "current_camera": result.current_camera_id,
                    "program": _encode(result.program_frame, PROGRAM_MAX_WIDTH),
                    "previews": {cid: _encode(f) for cid, f in result.previews.items()},
                })
                await asyncio.sleep(TICK_DELAY)
            await ws.send_json({"type": "done"})
            await asyncio.sleep(1.2)
    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
