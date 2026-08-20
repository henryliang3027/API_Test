from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
CIRCLE_RADIUS = 10


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
