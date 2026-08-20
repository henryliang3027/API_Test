import base64
import requests
from io import BytesIO
from PIL import Image

with open("test_images/test2/螢幕擷取畫面 2026-08-05 102248.png", "rb") as f:
    resp = requests.post(
        "https://logistics.sstc-aiteam.org/api/v1/detect/image",
        files={"file": f},
        data={"include_annotated_image": "true"},
    )
resp.raise_for_status()
data = resp.json()

print(f"共偵測到 {data['total_boxes']} 個紙箱")
for box in data["boxes"]:
    product = box["product"]["name"] if box["product"] else "未知品項"
    expiry  = box["expiry_date"]
    expiry_str = f"{expiry['year']}-{expiry['month']}-{expiry['day']}" if expiry else "無法解析"
    print(f"box_id={box['box_id']} confidence={box['confidence']:.2f} "
          f"product={product} expiry_date={expiry_str}")

if data["annotated_image_base64"]:
    image = Image.open(BytesIO(base64.b64decode(data["annotated_image_base64"])))
    image.show()