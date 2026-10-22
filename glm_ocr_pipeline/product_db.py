"""
product_db.py — 品名 json 資料庫（同 service_template/service_api/services/product_db.py）
比對邏輯：計算 OCR 文字中命中的 keywords 數量，取最高分的產品；0 分回傳 None（未知品項）。
"""

import json
from pathlib import Path
from typing import Optional

from glm_ocr_pipeline import config


class ProductDatabase:
    def __init__(self, path: str = config.BOX_NAME_JSON) -> None:
        self.path = path
        self._products: list[dict] = []
        self.reload()

    def reload(self) -> int:
        with open(Path(self.path), encoding="utf-8") as f:
            self._products = json.load(f)["products"]
        return len(self._products)

    def match(self, ocr_text: str) -> Optional[dict]:
        best_product: Optional[dict] = None
        best_score = 0
        for product in self._products:
            score = sum(1 for kw in product["keywords"] if kw in ocr_text)
            if score > best_score:
                best_product, best_score = product, score
        return best_product if best_score > 0 else None

    @property
    def count(self) -> int:
        return len(self._products)
