"""
pipeline.py — PP-OCRv6 + 日期字串解析 + 品名 json 資料庫
=========================================================
與 glm_ocr_pipeline/pipeline.py 相同流程，只把 OCR 換成 PP-OCRv6：
  圖片 → (1) PP-OCRv6 辨識文字
       → (2) 品名比對（glm_ocr_pipeline/box_name.json；未命中 → product=None）
       → (3) 日期解析（glm_ocr_pipeline/date_extractor）
       → (4) 組合回應（格式同 service_template 的 /api/v1/detect）

用法：
    from paddleocrv6_pipeline.pipeline import PaddleOcrV6Pipeline
    result = PaddleOcrV6Pipeline().run("eval_dataset/20260920_v3/t1.jpg")
"""

from pathlib import Path

from paddleocrv6_pipeline import config
from paddleocrv6_pipeline.ocr_client import PaddleOcrV6Client
from glm_ocr_pipeline import date_extractor
from glm_ocr_pipeline.product_db import ProductDatabase


class PaddleOcrV6Pipeline:
    def __init__(self) -> None:
        self.ocr = PaddleOcrV6Client()
        self.product_db = ProductDatabase(config.BOX_NAME_JSON)

    def run(self, image_path: str) -> dict:
        ocr_text, ocr_elapsed = self.ocr.ocr(image_path)

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
