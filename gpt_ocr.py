import base64
import json
import mimetypes
import os

from openai import OpenAI

PROMPT = """你是一個專業的商品紙箱文字辨識與空間定位專家。請分析圖片中所有的紙箱，並將每一個紙箱分別獨立為清單中的一個物件。

請嚴格遵循以下解析規則：

1. 日期與保存期限推理邏輯：
   - 【直接提取】：若印有「有效日期 / 到期日 / EXP」，直接提取該日期作為 expiration_date。
   - 【公式計算】：若同時印有「製造日期」與「保存期限」（例如：保存期限 10 個月），請自動將製造日期加上保存期限，計算出最終的有效日期作為 expiration_date。
   - 【預設規則】：若僅看到一串日期數字且沒有任何前綴說明（如未標明製造或有效），一律直接視為 expiration_date。
   - 【無資訊處理】：若無法獲知製造日期或有效日期，對應欄位請回傳 null。所有日期格式請統一轉換為 YYYY-MM-DD。

2. 空間定位規範：
   - 請框出每個紙箱完整外觀的邊界框 box_2d，格式為 [ymin, xmin, ymax, xmax]。
   - 座標數值須正規化到 0-1000 的整數範圍，(0, 0) 代表圖片左上角，(1000, 1000) 代表圖片右下角。
   - 邊界框必須盡量貼齊該紙箱可見的完整輪廓邊緣。

請依據上述規則，輸出包含所有紙箱資訊的結構化物件陣列。"""

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

MODEL = "gpt-5.4"


def get_client():
    api_key = os.environ["OPENAI_API_KEY"]
    return OpenAI(api_key=api_key)


def ocr_image(client, image_path):
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = client.responses.create(
        model=MODEL,
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
