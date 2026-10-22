"""
ocr_client.py — GLM-OCR 呼叫封裝（同 service_template/service_api/services/ocr_client.py）
透過 OpenAI 相容 API 呼叫 llama-server。
"""

import base64
import io
import time

from openai import OpenAI
from PIL import Image, ImageEnhance

from glm_ocr_pipeline import config


class GlmOcrClient:
    def __init__(self, base_url: str = config.LLAMA_CPP_URL) -> None:
        self._client = OpenAI(base_url=base_url, api_key="no-key-needed")

    def ocr(self, image: Image.Image) -> tuple[str, float]:
        """對一張 PIL Image 執行 OCR，回傳 (辨識文字, 耗時秒數)。"""
        b64 = self._encode_image(self._preprocess(image))
        t0 = time.time()
        resp = self._client.chat.completions.create(
            model="glm-ocr",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": config.OCR_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }],
            temperature=config.OCR_TEMPERATURE,
            max_tokens=config.OCR_MAX_TOKENS,
        )
        return resp.choices[0].message.content or "", time.time() - t0

    def is_reachable(self) -> bool:
        try:
            self._client.models.list()
            return True
        except Exception:
            return False

    @staticmethod
    def _preprocess(image: Image.Image) -> Image.Image:
        image = image.convert("RGB")
        if config.OCR_MAX_SIDE and max(image.size) > config.OCR_MAX_SIDE:
            scale = config.OCR_MAX_SIDE / max(image.size)
            image = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
        if config.OCR_CONTRAST != 1.0:
            image = ImageEnhance.Contrast(image).enhance(config.OCR_CONTRAST)
        return image

    @staticmethod
    def _encode_image(image: Image.Image, fmt: str = "JPEG") -> str:
        buf = io.BytesIO()
        image.save(buf, format=fmt)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
