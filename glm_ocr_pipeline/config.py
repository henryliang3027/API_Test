"""
config.py — GLM-OCR + 日期字串解析 + 品名 json 資料庫 的設定集中管理
================================================================
參考 service_template/service_api/config.py，移除 YOLO（不做紙箱分割，整張圖直接送 OCR）。
所有設定都可透過環境變數覆蓋。
"""

import os
from pathlib import Path

# glm_ocr_pipeline/ 的上一層為專案根目錄
ROOT_DIR: Path = Path(__file__).resolve().parent.parent
PKG_DIR: Path = Path(__file__).resolve().parent

# ── llama.cpp runtime（llama-server）────────────────────────────────────────
LLAMA_DIR: str = os.getenv("LLAMA_DIR", str(ROOT_DIR / "llama-b1287"))
LLAMA_SERVER_BIN: str = os.getenv("LLAMA_SERVER_BIN", str(Path(LLAMA_DIR) / "llama-server"))
GLM_OCR_MODEL: str = os.getenv("GLM_OCR_MODEL", str(ROOT_DIR / "models/glm-ocr/GLM-OCR-f16.gguf"))
GLM_OCR_MMPROJ: str = os.getenv("GLM_OCR_MMPROJ", str(ROOT_DIR / "models/glm-ocr/mmproj-GLM-OCR-Q8_0.gguf"))
LLAMA_HOST: str = os.getenv("LLAMA_HOST", "0.0.0.0")
LLAMA_PORT: int = int(os.getenv("LLAMA_PORT", "8010"))
N_GPU_LAYERS: str = os.getenv("N_GPU_LAYERS", "99")
CTX_SIZE: str = os.getenv("CTX_SIZE", "8192")

# ── GLM-OCR（llama-server OpenAI 相容 API）──────────────────────────────────
LLAMA_CPP_URL: str = os.getenv("LLAMA_CPP_URL", f"http://localhost:{LLAMA_PORT}/v1")
OCR_PROMPT: str = os.getenv("OCR_PROMPT", "Text Recognition:")
OCR_MAX_TOKENS: int = 2048
OCR_TEMPERATURE: float = 0.0
# 圖片最長邊超過此值時等比縮小再送 OCR（0 = 不縮放）
OCR_MAX_SIDE: int = int(os.getenv("OCR_MAX_SIDE", "0"))
# OCR 前提高對比度的倍數（同 service_template 的 enhance_contrast_pillow，1.0 = 不處理）
OCR_CONTRAST: float = float(os.getenv("OCR_CONTRAST", "2.0"))

# ── 品名資料庫 ──────────────────────────────────────────────────────────────
BOX_NAME_JSON: str = os.getenv("BOX_NAME_JSON", str(PKG_DIR / "box_name.json"))
