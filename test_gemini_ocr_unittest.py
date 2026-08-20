import os

import pytest
from dotenv import load_dotenv

from draw_utils import draw_result
from gemini_ocr import get_client, ocr_image
from ground_truth import GROUND_TRUTH

load_dotenv()

IMAGE_DIRS = ["test_images/v1", "test_images/v2"]
RESULT_DIR = "result"
os.makedirs(RESULT_DIR, exist_ok=True)


def find_image_path(image_name):
    for image_dir in IMAGE_DIRS:
        candidate = os.path.join(image_dir, image_name)
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(f"{image_name} 在 {IMAGE_DIRS} 中都找不到")


TRADEMARK_SYMBOLS = ("™", "®", "©")


def normalize_text(text):
    text = (text or "").replace(" ", "")
    for symbol in TRADEMARK_SYMBOLS:
        text = text.replace(symbol, "")
    return text


def contains_any(actual_text, expected):
    """expected 可以是單一字串，或是可接受答案的 list。"""
    actual_text = normalize_text(actual_text)
    candidates = expected if isinstance(expected, list) else [expected]
    return any(normalize_text(candidate) in actual_text for candidate in candidates)


@pytest.fixture(scope="module")
def client():
    return get_client()


@pytest.mark.parametrize("image_name", sorted(GROUND_TRUTH.keys()))
def test_ocr_matches_ground_truth(client, image_name):
    image_path = find_image_path(image_name)
    expected_boxes = GROUND_TRUTH[image_name]

    actual_boxes = ocr_image(client, image_path)

    out_path = os.path.join(RESULT_DIR, image_name)
    draw_result(image_path, actual_boxes, out_path)

    assert len(actual_boxes) == len(expected_boxes), (
        f"{image_name}: 偵測到的紙箱數量不符，"
        f"預期 {len(expected_boxes)} 個，實際 {len(actual_boxes)} 個\n{actual_boxes}"
    )

    # 順序無關比對：為每個 expected 找一個尚未配對過、且 product_name/日期都相符的 actual。
    remaining_actual = list(actual_boxes)

    for expected in expected_boxes:
        match = next(
            (
                actual
                for actual in remaining_actual
                if contains_any(actual.get("product_name"), expected["product_name"])
                and actual.get("manufacturer_date") == expected["manufacture_date"]
                and actual.get("expiration_date") == expected["expiry_date"]
            ),
            None,
        )

        assert match is not None, (
            f"{image_name}: 找不到符合的偵測結果，預期 {expected}\n"
            f"剩餘可配對的實際結果：{remaining_actual}"
        )

        remaining_actual.remove(match)
