"""便捷脚本：启动实时 Dashboard（等价于 python -m app.server）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn

from app.server import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
