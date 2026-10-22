import base64
import requests
from io import BytesIO
from PIL import Image

with open("test_images/v2/b1.jpg", "rb") as f:
    resp = requests.post(
        "https://logistics2.sstc-aiteam.org/api/v1/detect/image",
        files={"file": f},
        data={"include_annotated_image": "true"},
    )
resp.raise_for_status()
data = resp.json()

print(f"共偵測到 {data['total_boxes']} 個紙箱")
for box in data["boxes"]:
    product = box["product"]
    brand   = product["brand"] if product and product["brand"] else ""
    name    = product["name"] if product else "未知品項"
    expiry  = box["expiry_date"]
    expiry_str = f"{expiry['year']}-{expiry['month']}-{expiry['day']}" if expiry else "無法解析"
    print(f"box_id={box['box_id']} product={brand}{name} expiry_date={expiry_str}")

if data["annotated_image_base64"]:
    image = Image.open(BytesIO(base64.b64decode(data["annotated_image_base64"])))
    image.show()