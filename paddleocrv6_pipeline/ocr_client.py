"""
ocr_client.py — PP-OCRv6 呼叫封裝（原 PaddleVL/paddleocr_v6.py，已刪除）
本機直接載入 PaddleOCR，不經 server。
GPU：engine="transformers"（PyTorch ROCm）；CPU：engine="paddle"（Paddle Inference）。
"""

import os
import time

from paddleocrv6_pipeline import config

os.environ.setdefault("MIOPEN_FIND_MODE", config.MIOPEN_FIND_MODE)

from paddleocr import PaddleOCR  # noqa: E402


class PaddleOcrV6Client:
    def __init__(self) -> None:
        self._ocr = PaddleOCR(
            text_detection_model_name=config.DET_MODEL_NAME,
            text_detection_model_dir=config.DET_MODEL_DIR,
            text_recognition_model_name=config.REC_MODEL_NAME,
            text_recognition_model_dir=config.REC_MODEL_DIR,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            text_det_thresh=config.TEXT_DET_THRESH,
            text_det_box_thresh=config.TEXT_DET_BOX_THRESH,
            text_rec_score_thresh=config.TEXT_REC_SCORE_THRESH,
            device=config.DEVICE,
            engine=config.ENGINE,
            **({} if config.USE_GPU else {"enable_mkldnn": config.ENABLE_MKLDNN}),
        )

    def ocr(self, image_path: str) -> tuple[str, float]:
        """對一張圖片執行 OCR，回傳 (辨識文字（每行一段）, 耗時秒數)。"""
        t0 = time.time()
        texts: list[str] = []
        for page in self._ocr.predict(image_path):
            texts.extend(page.get("rec_texts", []))
        return "\n".join(texts), time.time() - t0
