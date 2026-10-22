import glob
import os
import time

from dotenv import load_dotenv

from draw_shelf_count import draw_shelf_result
from gemini_shelf_count import get_client, count_shelf_products

load_dotenv()

image_dir = "test_images/博亞藥局/shelf"
result_dir = "result_shelf_count"
os.makedirs(result_dir, exist_ok=True)

image_paths = sorted(glob.glob(os.path.join(image_dir, "*")))

client = get_client()


for image_path in image_paths:
    start_time = time.perf_counter()
    result = count_shelf_products(client, image_path)
    inference_time = time.perf_counter() - start_time

    print(f"===== {os.path.basename(image_path)} =====")
    print(f"total_count: {result.get('total_count')}, items detected: {len(result.get('items', []))}")
    print(result)
    print(f"inference time: {inference_time:.2f}s")
    print()

    out_path = os.path.join(result_dir, os.path.basename(image_path))
    draw_shelf_result(image_path, result, out_path)
