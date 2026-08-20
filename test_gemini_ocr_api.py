import glob
import os
import time

from dotenv import load_dotenv

from draw_utils import draw_result
from gemini_ocr import get_client, ocr_image

load_dotenv()

image_dir = "test_images/v1"
result_dir = "result"
os.makedirs(result_dir, exist_ok=True)

image_paths = sorted(glob.glob(os.path.join(image_dir, "*")))

client = get_client()


for image_path in image_paths:
    start_time = time.perf_counter()
    result = ocr_image(client, image_path)
    inference_time = time.perf_counter() - start_time

    print(f"===== {os.path.basename(image_path)} =====")
    print(result)
    print(f"inference time: {inference_time:.2f}s")
    print()

    out_path = os.path.join(result_dir, os.path.basename(image_path))
    draw_result(image_path, result, out_path)
