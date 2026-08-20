# 依 test_gemini_ocr_api.py 這次實際跑出的結果整理的 ground truth 快照。
#
# - manufacture_date / expiry_date 為 None 代表沒有可辨識的日期文字，
#   否則用 {'year': 'YYYY', 'month': 'MM', 'day': 'DD'} dict 表示（字串、月/日補零）。
# - product_name 直接採用模型當次輸出的完整字串。

GROUND_TRUTH = {
    "sample.jpg": [
        {
            "product_name": "樂事洋芋片 青檸享清新口味",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "01", "day": "13"},
        },
        {
            "product_name": "維他露P",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "10", "day": "09"},
        },
        {
            "product_name": "來一客 牛肉蔬菜風味",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "09", "day": "07"},
        },
        {
            "product_name": "來一客 鮮蝦魚板風味",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "09", "day": "15"},
        },
        {
            "product_name": "來一客 韓式泡菜風味",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "10", "day": "05"},
        },
        {
            "product_name": "科學麵 原味",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "10", "day": "10"},
        },
        {
            "product_name": "益生菌小Q果凍 葡萄",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "03", "day": "15"},
        },
        {
            "product_name": "玉黍叔甜辣口味",
            "manufacture_date": {"year": "2026", "month": "05", "day": "05"},
            "expiry_date": {"year": "2027", "month": "03", "day": "05"},
        },
        {
            "product_name": "真魷味 紅燒口味",
            "manufacture_date": {"year": "2026", "month": "05", "day": "04"},
            "expiry_date": {"year": "2027", "month": "03", "day": "04"},
        },
        {
            "product_name": "MOS BURGER",
            "manufacture_date": None,
            "expiry_date": {"year": "2028", "month": "04", "day": "09"},
        },
    ],
    "sample2.jpg": [
        {
            "product_name": "MOS BURGER",
            "manufacture_date": None,
            "expiry_date": {"year": "2028", "month": "04", "day": "09"},
        },
        {
            "product_name": "玉黍叔甜辣口味",
            "manufacture_date": {"year": "2026", "month": "05", "day": "05"},
            "expiry_date": {"year": "2027", "month": "03", "day": "05"},
        },
        {
            "product_name": "來一客鮮蝦魚板風味",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "09", "day": "15"},
        },
        {
            "product_name": "來一客牛肉蔬菜風味",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "09", "day": "07"},
        },
        {
            "product_name": "來一客韓式泡菜風味",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "10", "day": "05"},
        },
        {
            "product_name": "真魷味紅燒口味",
            "manufacture_date": {"year": "2026", "month": "05", "day": "04"},
            "expiry_date": {"year": "2027", "month": "03", "day": "04"},
        },
    ],
    "b1.jpg": [
        {
            "product_name": "環保紙湯杯",
            "manufacture_date": None,
            "expiry_date": None,
        },
        {
            "product_name": "780 湯杯",
            "manufacture_date": None,
            "expiry_date": None,
        },
        {
            "product_name": "390紙湯杯",
            "manufacture_date": None,
            "expiry_date": None,
        },
    ],
    "b2.jpg": [
        {
            "product_name": "雁牌 薑母茶",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "02", "day": "26"},
        },
    ],
    "b3.jpg": [
        {
            "product_name": "統一冰塊",
            "manufacture_date": None,
            "expiry_date": {"year": "2025", "month": "08", "day": "08"},
        },
    ],
    "b4.jpg": [
        {
            "product_name": "蘇菲彈力貼身",
            "manufacture_date": {"year": "2024", "month": "12", "day": "26"},
            "expiry_date": {"year": "2027", "month": "12", "day": "26"},
        },
        {
            "product_name": "蘇菲彈力貼身",
            "manufacture_date": {"year": "2024", "month": "08", "day": "13"},
            "expiry_date": {"year": "2027", "month": "08", "day": "13"},
        },
    ],
    "b5.jpg": [
        {
            "product_name": "琦美製冰",
            "manufacture_date": None,
            "expiry_date": {"year": "2028", "month": "04", "day": "21"},
        },
    ],
    "b6.jpg": [
        {
            "product_name": "Paxlovid 150 mg/100 mg tablets",
            "manufacture_date": None,
            "expiry_date": {"year": "2023", "month": "08", "day": "31"},
        },
    ],
    "sample3.jpg": [
        {
            "product_name": "維他露P",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "12", "day": "10"},
        },
        {
            "product_name": "維他露P",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "10", "day": "09"},
        },
        {
            "product_name": "維他露P",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "12", "day": "22"},
        },
        {
            "product_name": "MOS BURGER",
            "manufacture_date": None,
            "expiry_date": {"year": "2028", "month": "04", "day": "09"},
        },
        {
            "product_name": "MOS BURGER",
            "manufacture_date": None,
            "expiry_date": {"year": "2028", "month": "04", "day": "09"},
        },
    ],
    "sample4.jpg": [
        {
            "product_name": "維他露P",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "12", "day": "22"},
        },
        {
            "product_name": "維他露P",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "12", "day": "10"},
        },
        {
            "product_name": "維他露P",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "10", "day": "09"},
        },
        {
            "product_name": "維他露P",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "12", "day": "22"},
        },
    ],
    "sample5.jpg": [
        {
            "product_name": "來一客 牛肉蔬菜風味",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "09", "day": "07"},
        },
        {
            "product_name": "來一客 韓式泡菜風味",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "10", "day": "05"},
        },
        {
            "product_name": "來一客 鮮蝦魚板風味",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "09", "day": "15"},
        },
        {
            "product_name": "維他露P",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "12", "day": "10"},
        },
        {
            "product_name": "維他露P",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "10", "day": "09"},
        },
        {
            "product_name": "維他露P",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "12", "day": "22"},
        },
    ],
    "sample6.jpg": [
        {
            "product_name": "來一客 牛肉蔬菜風味",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "09", "day": "07"},
        },
        {
            "product_name": "來一客 韓式泡菜風味",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "10", "day": "05"},
        },
        {
            "product_name": "來一客 鮮蝦魚板風味",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "09", "day": "15"},
        },
        {
            "product_name": "維他露P",
            "manufacture_date": None,
            "expiry_date": {"year": "2026", "month": "12", "day": "10"},
        },
        {
            "product_name": "維他露P",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "10", "day": "09"},
        },
        {
            "product_name": "維他露P",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "12", "day": "22"},
        },
        {
            "product_name": "真魷味 紅燒口味",
            "manufacture_date": None,
            "expiry_date": None,
        },
        {
            "product_name": "玉黍叔 甜辣口味",
            "manufacture_date": {"year": "2026", "month": "05", "day": "05"},
            "expiry_date": {"year": "2027", "month": "03", "day": "05"},
        },
    ],
    "sample7.jpg": [
        {
            "product_name": "MOS BURGER",
            "manufacture_date": None,
            "expiry_date": {"year": "2028", "month": "04", "day": "09"},
        },
        {
            "product_name": "MOS BURGER",
            "manufacture_date": None,
            "expiry_date": {"year": "2028", "month": "04", "day": "09"},
        },
        {
            "product_name": "真魷味 紅燒口味",
            "manufacture_date": {"year": "2026", "month": "05", "day": "04"},
            "expiry_date": {"year": "2027", "month": "03", "day": "04"},
        },
        {
            "product_name": "玉黍叔 甜辣口味",
            "manufacture_date": {"year": "2026", "month": "05", "day": "05"},
            "expiry_date": {"year": "2027", "month": "03", "day": "05"},
        },
    ],
    "t1.jpg": [
        {
            "product_name": "VITALON 舒跑",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "09", "day": "15"},
        },
    ]
    * 10,
    "t2.jpg": [
        {
            "product_name": "維他露P",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "11", "day": "28"},
        },
    ]
    * 4,
    "t3.jpg": [
        {
            "product_name": "COCO CLUB 100% Coconut Water 酷椰嶼椰子俱樂部100%椰子水",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "04", "day": "07"},
        },
    ]
    * 3,
    "t4.jpg": [
        {
            "product_name": "舒跑 Super Supau",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "06", "day": "29"},
        },
        {
            "product_name": "舒跑 Super Supau",
            "manufacture_date": None,
            "expiry_date": {"year": "2027", "month": "05", "day": "24"},
        },
        {
            "product_name": "舒跑 Super Supau",
            "manufacture_date": None,
            "expiry_date": None,
        },
    ],
}
