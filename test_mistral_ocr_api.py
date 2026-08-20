import os
import base64
from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

api_key = os.environ["MISTRAL_API_KEY"]

client = Mistral(api_key=api_key)

image_path = "test_images/cropped/FB_IMG_1787033771874_box_o1.png"

with open(image_path, "rb") as f:
    base64_image = base64.b64encode(f.read()).decode("utf-8")

ocr_response = client.ocr.process(
    model="mistral-ocr-latest",
    document={
        "type": "image_url",
        "image_url": f"data:image/png;base64,{base64_image}",
    },
    include_image_base64=True,
)

for page in ocr_response.pages:
    print(page.markdown)
