import base64
import json
import mimetypes
import os

from openai import OpenAI

PROMPT = """你是專業的商品紙箱文字辨識與空間定位專家。分析圖片中所有紙箱，每個紙箱各自獨立為清單中一個物件，並遵循以下規則：

1. 日期：有「有效期/到期/EXP」直接取為 expiration_date；同時有「製造日期」+「保存期限」（如10個月）則相加算出 expiration_date；只有一串日期數字、無前綴說明時視為 expiration_date；查無日期則 manufacturer_date/expiration_date 填 "未知"。統一格式 YYYY-MM-DD。

2. product_name：必須是箱面實際印刷文字的連續子字串，不可改寫/翻譯/增字/調換順序，逐字核對確保與原文一致（含形近字如「菲」非「非」）。
   - 取「公司/品牌名稱＋商品類別或品名」的組合，長度以完整表達商品類型為原則，不因求簡短而截斷語意（如需保留「紙湯杯」不可只留「環保」）；不加「袋裝」「箱」等未直接相連的字。
   - 有口味/風味/規格等細分資訊（如「牛肉蔬菜風味」）必須完整包含，不可只取品牌/大類而省略。
   - 箱面若印有公司/品牌 Logo（如橢圓色塊搭配簡短文字，例：「華元」），即使 Logo 與品名文字位置分開，product_name 仍須以該 Logo 文字為前綴（例：「華元 真魷味 紅燒口味」）；【絕對不可省略】品牌文字是 product_name 的必要組成，不可因加速輸出而簡化省略。
   - 【書法/藝術字體品牌】：若品牌文字採用書法/毛筆/藝術字體印刷（筆畫較粗、連筆、非標準印刷字形），或紙箱拍攝角度傾斜/旋轉導致文字非水平，仍須耐心逐筆辨識，不可因字體特殊或角度傾斜而略過、猜測形似字、或直接省略；可留意品牌文字旁常伴隨的®/™小圓圈符號來確認該處為品牌標示。
   - 若印有品名/口味表格：(a) 某欄位有記號（打勾/圓點/圈選/螢光標示）標示實際內容物，則取「品牌＋該欄品名」（例：MOS BURGER 表格「蕃茄燉雞肉」欄有記號，則為「MOS BURGER 蕃茄燉雞肉」）；(b) 表格字跡模糊無法逐字確認，但有清楚可辨識的共通關鍵字（如各列都以「冰塊」結尾），則取「品牌＋該關鍵字」，模糊到無法確定的修飾字（如「袋裝/鋼製」）絕不可自行猜測，寧可精簡。

3. 紙箱偵測：只框輪廓完整清晰可見者，被遮擋大半或只露極小一角則忽略；同一實體紙箱僅一筆資料，不因文字分散於多面而拆成多筆；裝飾圖案/警示圖示/條碼不可單獨當作紙箱。

4. box_2d：[ymin, xmin, ymax, xmax]，正規化到 0-1000 整數，(0,0)為左上角、(1000,1000)為右下角，須貼齊紙箱可見輪廓。

輸出所有紙箱的結構化物件陣列。"""

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

MODEL = "gpt-5.6"


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
