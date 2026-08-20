"""
測試 https://logistics.sstc-aiteam.org 的紙箱偵測 API
(POST /api/v1/detect/image)

- 呼叫 API 時 include_annotated_image=false，僅取得 JSON 結果
- 依 JSON 內的 mask 座標與日期等資訊，自行畫在原始圖片上並存檔
"""

import argparse
import sys
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

API_URL = "https://logistics.sstc-aiteam.org/api/v1/detect/image"

# 每個 box 用不同顏色，避免重疊看不清楚
COLORS = [
    (255, 0, 0),
    (0, 200, 0),
    (0, 120, 255),
    (255, 165, 0),
    (200, 0, 200),
    (0, 200, 200),
    (255, 255, 0),
]


def call_detect_api(image_path: str) -> dict:
    """呼叫偵測 API，include_annotated_image=false，回傳 JSON 結果"""
    with open(image_path, "rb") as f:
        resp = requests.post(
            API_URL,
            files={"file": f},
            data={"include_annotated_image": "false"},
        )
    resp.raise_for_status()
    data = resp.json()

    # 依 API 文件說明，未要求標注圖時 annotated_image_base64 應為 null
    assert data.get("annotated_image_base64") is None, (
        "include_annotated_image=false 時 annotated_image_base64 應為 null"
    )
    return data


def format_date(date_dict):
    if not date_dict:
        return "無法解析"
    return f"{date_dict['year']}-{date_dict['month']}-{date_dict['day']}"


def draw_result(image_path: str, data: dict, output_path: str):
    """把 JSON 結果（mask、box_id、confidence、品項、日期）畫在原圖上"""
    image = Image.open(image_path).convert("RGBA")
    width, height = image.size
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc", 22
        )
    except OSError:
        font = ImageFont.load_default()

    # 先把所有 mask（半透明填色 + 邊框線）畫在 overlay 上，再與原圖合成
    polygons = []
    for i, box in enumerate(data.get("boxes", [])):
        color = COLORS[i % len(COLORS)]
        fill_color = (*color, 40)

        # mask 座標是正規化(0~1)後的值，需還原成像素座標
        mask = box.get("mask") or []
        polygon = [(x * width, y * height) for x, y in mask]
        polygons.append(polygon)
        if len(polygon) >= 3:
            overlay_draw.polygon(polygon, fill=fill_color)
        if len(polygon) >= 2:
            overlay_draw.line(polygon + [polygon[0]], fill=color, width=3)

    image = Image.alpha_composite(image, overlay)
    draw = ImageDraw.Draw(image)

    # 再把文字標籤畫在合成後的圖片最上層，確保不被半透明 mask 蓋住
    for i, box in enumerate(data.get("boxes", [])):
        color = COLORS[i % len(COLORS)]
        polygon = polygons[i]

        product = box.get("product")
        product_str = (
            f"{product['brand']} {product['name']}" if product else "未知品項"
        )
        expiry_str = format_date(box.get("expiry_date"))
        manufacture_str = format_date(box.get("manufacture_date"))

        label_lines = [
            f"#{box['box_id']} conf={box['confidence']:.2f}",
            f"{product_str}",
            f"exp={expiry_str} mfg={manufacture_str}",
        ]

        # 標籤畫在該 box mask 的左上角附近
        if polygon:
            anchor_x = min(p[0] for p in polygon)
            anchor_y = min(p[1] for p in polygon)
        else:
            anchor_x, anchor_y = 10, 10 + i * 60

        text = "\n".join(label_lines)
        bbox = draw.multiline_textbbox((anchor_x, anchor_y), text, font=font)
        draw.rectangle(bbox, fill=color, outline=(0, 0, 0), width=2)
        draw.multiline_text((anchor_x, anchor_y), text, fill=(0, 0, 0), font=font)

    image.convert("RGB").save(output_path)
    print(f"已將標注結果存檔至: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="測試紙箱偵測 API 並手動繪製標注結果")
    parser.add_argument(
        "image",
        nargs="?",
        default="test_images/sample.jpg",
        help="要測試的圖片路徑（預設 test_images/sample.jpg）",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="輸出圖片路徑（預設為原檔名加上 _annotated 後綴）",
    )
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"找不到圖片: {image_path}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output or str(
        image_path.with_name(image_path.stem + "_annotated" + image_path.suffix)
    )

    print(f"呼叫 API 中: {API_URL} (file={image_path}, include_annotated_image=false)")
    data = call_detect_api(str(image_path))

    print(f"filename    = {data['filename']}")
    print(f"total_boxes = {data['total_boxes']}")
    for box in data["boxes"]:
        product = box["product"]["name"] if box["product"] else "未知品項"
        print(
            f"  box_id={box['box_id']} confidence={box['confidence']:.2f} "
            f"product={product} expiry_date={format_date(box['expiry_date'])}"
        )

    draw_result(str(image_path), data, output_path)


if __name__ == "__main__":
    main()
