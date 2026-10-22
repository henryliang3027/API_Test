"""
pipeline.py — GLM-OCR + 日期字串解析 + 品名 json 資料庫
=========================================================
參考 service_template/service_api/pipeline.py，但不使用 YOLO 紙箱分割：
整張圖片視為一個 box 直接送 GLM-OCR。

流程：
  圖片 → (1) GLM-OCR 辨識文字
       → (2) 品名比對（box_name.json 關鍵字；未命中 → 未知品項 product=None）
       → (3) 日期解析（date_extractor：有效日期、製造日期）
       → (4) 組合回應（格式同 service_template 的 /api/v1/detect）

用法：
    from glm_ocr_pipeline.pipeline import GlmOcrPipeline
    result = GlmOcrPipeline().run("eval_dataset/20260920_v3/t1.jpg")
"""

from pathlib import Path

from PIL import Image

from glm_ocr_pipeline import date_extractor
from glm_ocr_pipeline.ocr_client import GlmOcrClient
from glm_ocr_pipeline.product_db import ProductDatabase


class GlmOcrPipeline:
    def __init__(self) -> None:
        self.ocr = GlmOcrClient()
        self.product_db = ProductDatabase()

    def run(self, image_path: str) -> dict:
        image = Image.open(image_path)
        ocr_text, ocr_elapsed = self.ocr.ocr(image)

        matched = self.product_db.match(ocr_text)
        dates = date_extractor.extract_dates(ocr_text)

        box = {
            "box_id": 1,
            "product": {"brand": matched["brand"], "name": matched["name"]} if matched else None,
            "expiry_date": dates.get("expiry"),
            "manufacture_date": dates.get("manufacture"),
        }
        return {
            "filename": Path(image_path).name,
            "total_boxes": 1,
            "boxes": [box],
            "ocr_text": ocr_text,
            "ocr_elapsed": round(ocr_elapsed, 3),
        }
