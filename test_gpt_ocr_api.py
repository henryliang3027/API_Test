import glob
import os
import time

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

from gpt_ocr import get_client, ocr_image

load_dotenv()

image_dir = "test_images/v2"
result_dir = "result"
os.makedirs(result_dir, exist_ok=True)

FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
CIRCLE_RADIUS = 10

image_paths = sorted(glob.glob(os.path.join(image_dir, "*")))

client = get_client()


def format_date(date):
    if not date:
        return "未知"
    return f"{date['year']}-{date['month']}-{date['day']}"


def draw_result(image_path, result, out_path):
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    font_size = max(16, image.width // 40)
    font = ImageFont.truetype(FONT_PATH, font_size)

    for box in result:
        ymin, xmin, ymax, xmax = box["box_2d"]
        xmin = xmin / 1000 * image.width
        xmax = xmax / 1000 * image.width
        ymin = ymin / 1000 * image.height
        ymax = ymax / 1000 * image.height
        cx = (xmin + xmax) / 2
        cy = (ymin + ymax) / 2

        draw.rectangle([xmin, ymin, xmax, ymax], outline="red", width=3)
        draw.ellipse(
            [cx - CIRCLE_RADIUS, cy - CIRCLE_RADIUS, cx + CIRCLE_RADIUS, cy + CIRCLE_RADIUS],
            fill="red",
            outline="white",
            width=2,
        )

        text = (
            f"{box['product_name']}\n"
            f"製造: {format_date(box['manufacturer_date'])}\n"
            f"有效: {format_date(box['expiration_date'])}"
        )

        text_bbox = draw.multiline_textbbox((cx, cy), text, font=font)
        draw.rectangle(text_bbox, fill=(0, 0, 0, 180))
        draw.multiline_text((cx, cy), text, font=font, fill="yellow")

    image.save(out_path)


for image_path in image_paths:
    start_time = time.perf_counter()
    result = ocr_image(client, image_path)
    inference_time = time.perf_counter() - start_time

    print(f"===== {os.path.basename(image_path)} =====")
    print(result)
    print(f"inference time: {inference_time:.2f}s")
    print()

    out_path = os.path.join(result_dir, f"gpt_{os.path.basename(image_path)}")
    draw_result(image_path, result, out_path)
