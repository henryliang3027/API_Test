import os
import time

from dotenv import load_dotenv

from draw_utils import draw_result
from gemini_ocr import get_client, ocr_image

load_dotenv()

image_path = "test_images/v1/00c1.jpg"
result_dir = "result"
os.makedirs(result_dir, exist_ok=True)

client = get_client()

start_time = time.perf_counter()
result = ocr_image(client, image_path)
inference_time = time.perf_counter() - start_time

print(f"===== {os.path.basename(image_path)} =====")
print(result)
print(f"inference time: {inference_time:.2f}s")

out_path = os.path.join(result_dir, os.path.basename(image_path))
draw_result(image_path, result, out_path)
