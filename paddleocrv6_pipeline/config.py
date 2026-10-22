"""
config.py — PP-OCRv6 + 日期字串解析 + 品名 json 資料庫 的設定集中管理
=====================================================================
日期解析與品名資料庫沿用 glm_ocr_pipeline，只把 OCR 換成 PP-OCRv6，方便與 GLM-OCR 比較。
所有設定都可透過環境變數覆蓋。
"""

import os
from pathlib import Path

# paddleocrv6_pipeline/ 的上一層為專案根目錄
ROOT_DIR: Path = Path(__file__).resolve().parent.parent

# ── PP-OCRv6 模型（從 ~/.paddlex/official_models 複製到 models/paddleocrv6）───
MODEL_DIR: Path = Path(os.getenv("PPOCRV6_MODEL_DIR", str(ROOT_DIR / "models/paddleocrv6")))
DET_MODEL_NAME: str = "PP-OCRv6_medium_det"
REC_MODEL_NAME: str = "PP-OCRv6_medium_rec"
# 推論裝置：預設用 GPU（Radeon RX 9070 XT，透過 PyTorch ROCm 跑 transformers 引擎）；
# 設 PPOCRV6_DEVICE=cpu 改用 Paddle Inference（paddlepaddle 是 CPU 版，不支援 AMD GPU）
DEVICE: str = os.getenv("PPOCRV6_DEVICE", "gpu:0")
USE_GPU: bool = DEVICE.startswith("gpu")
ENGINE: str = "transformers" if USE_GPU else "paddle"
# transformers 引擎讀 safetensors 權重，paddle 引擎讀 inference.pdiparams
_SUFFIX = "_safetensors" if USE_GPU else ""
DET_MODEL_DIR: str = str(MODEL_DIR / f"{DET_MODEL_NAME}{_SUFFIX}")
REC_MODEL_DIR: str = str(MODEL_DIR / f"{REC_MODEL_NAME}{_SUFFIX}")
# Paddle 3.3 CPU + oneDNN 跑 PIR 模型會報 ConvertPirAttribute2RuntimeAttribute 錯誤，預設關閉
ENABLE_MKLDNN: bool = os.getenv("ENABLE_MKLDNN", "0") == "1"
# ROCm：MIOpen 預設的卷積演算法搜尋會要求 5GB 以上的 workspace，VRAM 被 llama-server 占用時會 OOM；
# FAST 模式峰值約 1GB。必須在 import torch 之前設定。
MIOPEN_FIND_MODE: str = os.getenv("MIOPEN_FIND_MODE", "FAST")

# ── PaddleOCR 參數（同原 PaddleVL/paddleocr_v6.py）────────────────────────────
TEXT_DET_THRESH: float = float(os.getenv("TEXT_DET_THRESH", "0.1"))
TEXT_DET_BOX_THRESH: float = float(os.getenv("TEXT_DET_BOX_THRESH", "0.3"))
TEXT_REC_SCORE_THRESH: float = float(os.getenv("TEXT_REC_SCORE_THRESH", "0.0"))

# ── 品名資料庫（與 GLM-OCR 共用）────────────────────────────────────────────
BOX_NAME_JSON: str = os.getenv("BOX_NAME_JSON", str(ROOT_DIR / "glm_ocr_pipeline/box_name.json"))
