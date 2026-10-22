import io
import json
import os
import mimetypes

from google import genai
from google.genai import types
from PIL import Image

PROMPT = """你是專業的貨架商品盤點與空間定位專家。分析圖片中貨架上「排面看得到」的商品，遵循以下規則：

1. 偵測範圍：只計算排面（貨架最前排、鏡頭可直接看到商品正面/側面）陳列的獨立商品單品，每一件商品各自獨立為清單中一個物件。
   - 同一層貨架上並排、堆疊或前後交錯但仍可辨識出個別商品輪廓者，每件都要各自框選計數。
   - 若商品因排列緊密而僅露出極小一角、被前方商品完全遮擋、或只看到瓶蓋/罐頂而無法判斷為獨立一件，則忽略不計。
   - 紙箱/包裝箱（尚未拆封陳列成排面商品者）不計入商品數量，但仍可視為一個物件，product_name 使用箱面文字，type 標示為 "box"。
   - 商品標籤牌卡、價格標籤、裝飾圖案不算商品。

2. product_name：盡可能辨識商品包裝上實際印刷文字（品牌＋品名/口味），逐字核對，不可改寫、翻譯、猜測；若因角度、遮擋、字體過小而無法辨識文字，可用商品外觀特徵簡述（如「藍色罐裝奶粉」）代替，不可留空。

3. type：商品陳列型態，須為以下其中之一："can"（罐裝）、"bottle"（瓶裝）、"box"（紙箱/箱裝）、"other"（其他）。

4. box_2d：[ymin, xmin, ymax, xmax]，正規化到 0-1000 整數，(0,0)為左上角、(1000,1000)為右下角，須貼齊商品可見輪廓。

5. total_count：排面可見商品的總件數，須與商品清單（items）陣列長度一致。

輸出商品總數與所有偵測到商品的結構化物件陣列。"""

LARGE_DIMENSION_THRESHOLD = 4000

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "total_count": {
            "type": "INTEGER",
            "description": "排面可見商品的總件數，須與 items 陣列長度一致",
        },
        "items": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "product_name": {"type": "STRING"},
                    "type": {
                        "type": "STRING",
                        "enum": ["can", "bottle", "box", "other"],
                    },
                    "box_2d": {
                        "type": "ARRAY",
                        "description": "商品邊界框 [ymin, xmin, ymax, xmax]，正規化到 0-1000 整數",
                        "items": {"type": "INTEGER"},
                    },
                },
                "required": ["product_name", "type", "box_2d"],
            },
        },
    },
    "required": ["total_count", "items"],
}

MODEL = "gemini-3.5-flash-lite"


def get_client():
    api_key = os.environ["GEMINI_API_KEY"]
    return genai.Client(api_key=api_key)


def _load_image_bytes(image_path):
    """讀取圖片；若寬或高達到 LARGE_DIMENSION_THRESHOLD，等比縮小為一半以加速推論。
    box_2d 座標為 0-1000 正規化值，與縮放無關，因此縮圖不影響座標判讀。"""
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    with Image.open(io.BytesIO(image_bytes)) as im:
        width, height = im.size
        if max(width, height) < LARGE_DIMENSION_THRESHOLD:
            return image_bytes, mimetypes.guess_type(image_path)[0] or "image/jpeg"

        resized = im.convert("RGB").resize(
            (max(1, width // 2), max(1, height // 2)), Image.LANCZOS
        )
        buf = io.BytesIO()
        resized.save(buf, format="JPEG", quality=90)
        return buf.getvalue(), "image/jpeg"


def count_shelf_products(client, image_path):
    image_bytes, mime_type = _load_image_bytes(image_path)

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            PROMPT,
        ],
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.MEDIUM),
            temperature=0,
            response_mime_type="application/json",
            response_schema=SCHEMA,
        ),
    )

    return json.loads(response.text)
