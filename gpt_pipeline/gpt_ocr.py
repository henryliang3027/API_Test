import base64
import json
import os

from openai import OpenAI

# prompt 與大圖縮小沿用 gemini_pipeline，讓兩個模型的評估條件一致
from gemini_pipeline.gemini_ocr import PROMPT, PROMPT_V4, _load_image_bytes  # noqa: F401

_DATE_SCHEMA = {
    "type": ["object", "null"],
    "description": "無法解析出日期時回傳 null",
    "properties": {
        "year": {"type": "string", "description": "四位數年份，例如 2027"},
        "month": {"type": "string", "description": "兩位數月份，例如 01"},
        "day": {"type": "string", "description": "兩位數日期，例如 13"},
    },
    "required": ["year", "month", "day"],
    "additionalProperties": False,
}

# OpenAI strict json_schema 的最外層必須是 object，因此用 {"boxes": [...]} 包住陣列
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

MODEL = os.getenv("GPT_MODEL", "gpt-5.6-sol")
# 推理模型不支援 temperature；對應 Gemini 的 thinking_level=HIGH
REASONING_EFFORT = os.getenv("GPT_REASONING_EFFORT", "high")


def get_client():
    api_key = os.environ["OPENAI_API_KEY"]
    return OpenAI(api_key=api_key)


def ocr_image(client, image_path):
    image_bytes, mime_type = _load_image_bytes(image_path)
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = client.responses.create(
        model=MODEL,
        reasoning={"effort": REASONING_EFFORT},
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": PROMPT},
                    {
                        "type": "input_image",
                        "image_url": f"data:{mime_type};base64,{b64_image}",
                    },
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "box_result",
                "schema": SCHEMA,
                "strict": True,
            }
        },
    )

    return json.loads(response.output_text)["boxes"]
