from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"

TYPE_COLORS = {
    "can": "red",
    "bottle": "lime",
    "box": "cyan",
    "other": "yellow",
}


def draw_shelf_result(image_path, result, out_path):
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    font_size = max(14, image.width // 80)
    font = ImageFont.truetype(FONT_PATH, font_size)

    for idx, item in enumerate(result.get("items", []), start=1):
        ymin, xmin, ymax, xmax = item["box_2d"]
        xmin = xmin / 1000 * image.width
        xmax = xmax / 1000 * image.width
        ymin = ymin / 1000 * image.height
        ymax = ymax / 1000 * image.height

        color = TYPE_COLORS.get(item.get("type"), "yellow")
        draw.rectangle([xmin, ymin, xmax, ymax], outline=color, width=2)

        text = item.get("product_name", str(idx))
        print(f"Drawing box for {text} at ({xmin}, {ymin}, {xmax}, {ymax}) with color {color}")
        text_bbox = draw.textbbox((xmin, ymin), text, font=font)
        draw.rectangle(text_bbox, fill=color)
        draw.text((xmin, ymin), text, font=font, fill="black")

    header_font = ImageFont.truetype(FONT_PATH, max(20, image.width // 30))
    header_text = f"總數量: {result.get('total_count')}"
    header_bbox = draw.textbbox((10, 10), header_text, font=header_font)
    draw.rectangle(header_bbox, fill=(0, 0, 0, 180))
    draw.text((10, 10), header_text, font=header_font, fill="white")

    image.save(out_path)
