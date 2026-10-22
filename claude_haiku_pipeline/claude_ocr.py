import base64
import io
import json
import os

import anthropic
from PIL import Image, ImageOps

# prompt 與品名資料庫比對沿用 gemini_pipeline，讓兩個模型的評估條件一致
from gemini_pipeline.gemini_ocr import PROMPT, PROMPT_V4, match_product_db  # noqa: F401

_DATE_SCHEMA = {
    "anyOf": [
        {
            "type": "object",
            "description": "無法解析出日期時回傳 null",
            "properties": {
                "year": {"type": "string", "description": "四位數年份，例如 2027"},
                "month": {"type": "string", "description": "兩位數月份，例如 01"},
                "day": {"type": "string", "description": "兩位數日期，例如 13"},
            },
            "required": ["year", "month", "day"],
            "additionalProperties": False,
        },
        {"type": "null"},
    ]
}

# structured outputs 的最外層必須是 object，因此用 {"boxes": [...]} 包住陣列
SCHEMA = {
    "type": "object",
    "properties": {
        "boxes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "manufacturer_date": _DATE_SCHEMA,
                    "expiration_date": _DATE_SCHEMA,
                    "box_2d": {
                        "type": "array",
                        "description": "紙箱邊界框 [ymin, xmin, ymax, xmax]，正規化到 0-1000 整數",
                        "items": {"type": "integer"},
                    },
                },
                "required": [
                    "product_name",
                    "manufacturer_date",
                    "expiration_date",
                    "box_2d",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["boxes"],
    "additionalProperties": False,
}

MODEL = os.getenv("CLAUDE_OCR_MODEL") or "claude-haiku-5-5"
_IS_HAIKU_45 = MODEL.startswith("claude-haiku-4-5")
# Haiku 5.5：adaptive thinking + effort（budget_tokens 會回 400），effort=high 對應 Gemini 的 thinking_level=HIGH。
# Haiku 4.5：不支援 effort / adaptive，改用 budget_tokens。
# 兩者都不設 temperature：Haiku 5.5 只接受 1，Haiku 4.5 開 thinking 時也必須是 1。
THINKING_BUDGET = int(os.getenv("CLAUDE_OCR_THINKING_BUDGET", "8000"))
EFFORT = os.getenv("CLAUDE_OCR_EFFORT", "high")
if _IS_HAIKU_45:
    THINKING_PARAMS = {"thinking": {"type": "enabled", "budget_tokens": THINKING_BUDGET}}
else:
    THINKING_PARAMS = {"thinking": {"type": "adaptive"}, "output_config": {"effort": EFFORT}}
MAX_TOKENS = 16000
# 圖片長邊上限（超過會被伺服器端縮小）：Haiku 5.5 為高解析度 2576px，Haiku 4.5 為 1568px。
# 先在本機縮好以減少上傳量並避開 5MB 限制
MAX_IMAGE_SIDE = 1568 if _IS_HAIKU_45 else 2576

# 品名資料庫比對（同 gemini_pipeline.match_product_db），用 v4 prompt 時設 CLAUDE_OCR_PRODUCT_DB=0 關閉
USE_PRODUCT_DB = os.getenv("CLAUDE_OCR_PRODUCT_DB", "1") == "1"


def get_client():
    # 讀 ANTHROPIC_API_KEY（或 `ant auth login` 的 profile）
    return anthropic.Anthropic()


def _load_image_b64(image_path):
    """讀取圖片並等比縮小到長邊 MAX_IMAGE_SIDE，回傳 (base64, media_type)。
    box_2d 座標為 0-1000 正規化值，與縮放無關。"""
    with Image.open(image_path) as im:
        # 重新編碼會丟掉 EXIF，先依 EXIF 方向轉正
        im = ImageOps.exif_transpose(im).convert("RGB")
        scale = MAX_IMAGE_SIDE / max(im.size)
        if scale < 1:
            im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=90)
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8"), "image/jpeg"


def ocr_image(client, image_path):
    image_b64, media_type = _load_image_b64(image_path)

    output_config = {**THINKING_PARAMS.get("output_config", {}),
                     "format": {"type": "json_schema", "schema": SCHEMA}}
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        thinking=THINKING_PARAMS["thinking"],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": image_b64},
                    },
                    {"type": "text", "text": PROMPT},
                ],
            }
        ],
        output_config=output_config,
    )

    if response.stop_reason != "end_turn":
        raise RuntimeError(f"{image_path}: stop_reason={response.stop_reason} ({response._request_id})")
    text = next(b.text for b in response.content if b.type == "text")
    boxes = json.loads(text)["boxes"]
    return match_product_db(boxes) if USE_PRODUCT_DB else boxes
