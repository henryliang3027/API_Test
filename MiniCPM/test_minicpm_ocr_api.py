import glob
import os
import time

from minicpm_ocr import get_model, ocr_image

# image_dir = "../test_images/博亞藥局/20260918"

# image_paths = [os.path.join(image_dir, "S__287867042.jpg")]

image_dir = "../test_images/博亞藥局/20260918"

image_paths = [os.path.join(image_dir, "S__287867042.jpg")]

model, tokenizer = get_model()


for image_path in image_paths:
    start_time = time.perf_counter()
    result = ocr_image(model, tokenizer, image_path)
    inference_time = time.perf_counter() - start_time

    print(f"===== {os.path.basename(image_path)} =====")
    print(result)
    print(f"inference time: {inference_time:.2f}s")
    print()
