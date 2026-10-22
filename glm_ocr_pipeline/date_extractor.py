"""
date_extractor.py — 從 OCR 文字中擷取並解析日期資訊

支援格式：yyyy.mm.dd  |  yyyy/mm/dd  |  yyyy mm dd  |  yyyymmdd
          dd mm yyyy（日月年）  |  dd/MON/yyyy  |  yymmdd（6 位數）
          區間「製造 - 有效」（如 25.10.28-26.09.27）

公開 API：
  extract_date_str(text)  → 原始日期字串 or None
  parse_date(date_str)    → {"year":str, "month":str, "day":str} or None
  extract_date_type(text) → "expiry" | "manufacture"
  extract_dates(text)     → {"expiry": dict|None, "manufacture": dict|None}
"""

import re
from datetime import date
from typing import Optional

from dateutil.relativedelta import relativedelta

# ── 日期 Regex（依優先順序：點 > 斜線 > 空白 > 無分隔）──────────────────────
_PAT_DOT     = re.compile(r'(\d{4})\.(\d{1,2})\.(\d{1,2})')
_PAT_SLASH   = re.compile(r'(\d{4})/(\d{1,2})/(\d{1,2})')
_PAT_SPACE   = re.compile(r'(\d{4})[ \t]+(\d{1,2})[ \t]+(\d{1,2})')
# yyyymmdd 無分隔：month 限 01-12、day 限 01-31，且前後不可緊鄰其他數字（避免誤中條碼）
_PAT_COMPACT = re.compile(
    r'(?<!\d)'
    r'(\d{4})'
    r'(0[1-9]|1[0-2])'
    r'(0[1-9]|[12]\d|3[01])'
    r'(?!\d)'
)
# 混合分隔符：每個分隔符可獨立為「.」「/」或空白，處理 OCR 漏辨識分隔符的情況
# 例如："2026 09.15"（空白+點）或 "2026.09 15"（點+空白）
_PAT_MIXED = re.compile(r'(\d{4})[ \t./]+(\d{1,2})[ \t./]+(\d{1,2})')

# 日月年（年份在最後）：例如 "EXP 01 09 2027" → 2027-09-01
_PAT_DMY = re.compile(r'(?<!\d)(\d{1,2})[ \t./-]+(\d{1,2})[ \t./-]+(\d{4})(?!\d)')
# 日月年（英文月份縮寫）：例如 "07/APR/2027" → 2027-04-07
_MONTH_ABBR = {m: i for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], start=1)}
_PAT_DMY_ABBR = re.compile(
    r'(?<!\d)(\d{1,2})[ \t./-]*(' + "|".join(_MONTH_ABBR) + r')[a-z]*[ \t./-]*(\d{4})(?!\d)',
    re.IGNORECASE,
)
# yymmdd 6 位數無分隔：例如黑松外箱噴印 "270401 19354 132" → 2027-04-01
# 年份限 20~39（避免把條碼片段當日期），month 01-12、day 01-31，前後不可緊鄰數字
_PAT_YYMMDD = re.compile(
    r'(?<!\d)'
    r'([23]\d)'
    r'(0[1-9]|1[0-2])'
    r'(0[1-9]|[12]\d|3[01])'
    r'(?!\d)'
)

# 優先嘗試嚴格格式（純點/斜線/空白/無分隔），再 fallback 到混合格式，
# 最後才是較寬鬆的日月年與 yymmdd（避免搶走原本就能正確解析的年月日格式）
# 每筆為 (regex, 欄位順序)
_PATTERNS = [
    (_PAT_DOT, "ymd"),
    (_PAT_SLASH, "ymd"),
    (_PAT_SPACE, "ymd"),
    (_PAT_COMPACT, "ymd"),
    (_PAT_MIXED, "ymd"),
    (_PAT_DMY, "dmy"),
    (_PAT_DMY_ABBR, "dmy_abbr"),
    (_PAT_YYMMDD, "yymmdd"),
]

# 日期區間：「製造日期 - 有效日期」，例如 "25.10.28-26.09.27"、"2026 06 25 - 2027 06 24"
# 年份可為 2 位或 4 位，分隔符為「-」「=」「~」「～」
_RANGE_DATE = r'(\d{4}|\d{2})[ \t./]+(\d{1,2})[ \t./]+(\d{1,2})'
_PAT_RANGE = re.compile(r'(?<!\d)' + _RANGE_DATE + r'[ \t]*[-=~～][ \t]*' + _RANGE_DATE + r'(?!\d)')

# 關鍵字（較長的優先，避免「製造日期」被「製造」截斷）
_MANUFACTURE_KW = ["製造日期", "製造"]
_EXPIRY_KW      = ["有效日期", "有效期限", "有效期"]

# 保存期限：匹配「保存期限」後接數字與「個月」，中間允許任意分隔符與空白
_PAT_SHELF = re.compile(r'保存期限[：: \t]*(\d+)\s*個月')


# ── 公開函式 ──────────────────────────────────────────────────────────────────

def extract_date_str(text: str) -> Optional[str]:
    """
    從任意 OCR 字串中提取第一個符合格式的日期子字串。
    日期前後可有任意字元。

    >>> extract_date_str("有效日期:2026 10 10 07:56 002")
    '2026 10 10'
    >>> extract_date_str("2027.01.13.19:55\\n樂事")
    '2027.01.13'
    """
    for pat, _ in _PATTERNS:
        m = pat.search(text)
        if m and _to_date(m, _) is not None:
            return m.group(0)
    return None


def parse_date(date_str: str) -> Optional[dict]:
    """
    將日期字串解析為結構化 dict。

    >>> parse_date("2027.01.13")
    {'year': '2027', 'month': '01', 'day': '13'}
    >>> parse_date("2026/5/5")
    {'year': '2026', 'month': '05', 'day': '05'}
    """
    for pat, order in _PATTERNS:
        m = pat.search(date_str)
        if m:
            d = _to_date(m, order)
            if d is not None:
                return d
    return None


def extract_date_type(text: str) -> str:
    """
    根據文字中的關鍵字判斷日期類型。

    規則：
      - 含「製造」相關字 → "manufacture"
      - 含「有效日期」相關字，或無任何標籤 → "expiry"（預設）

    >>> extract_date_type("製造2026/05/05")
    'manufacture'
    >>> extract_date_type("有效日期:2027.01.13")
    'expiry'
    >>> extract_date_type("2027.01.13")
    'expiry'
    """
    for kw in _MANUFACTURE_KW:
        if kw in text:
            return "manufacture"
    return "expiry"


def extract_dates(text: str) -> dict:
    """
    從 OCR 文字中同時擷取有效日期（expiry）與製造日期（manufacture）。

    規則：
      1. 找「製造」系列關鍵字後的日期 → manufacture
      2. 找「有效日期」系列關鍵字後的日期 → expiry
      3. 若無 expiry 標籤，第一個出現的日期預設為 expiry

    回傳：
      {"expiry": {"year":str, "month":str, "day":str} | None,
       "manufacture": {"year":str, "month":str, "day":str} | None}

    >>> extract_dates("製造2026/05/05\\n有效日期:2027/05/05")
    {'expiry': {'year': '2027', 'month': '05', 'day': '05'}, 'manufacture': {'year': '2026', 'month': '05', 'day': '05'}}
    >>> extract_dates("2027.01.13.19:55\\n樂事洋芋片")
    {'expiry': {'year': '2027', 'month': '01', 'day': '13'}, 'manufacture': None}
    """
    result: dict = {"expiry": None, "manufacture": None}

    # 步驟 0：日期區間「製造 - 有效」（例如 "25.10.28-26.09.27"），前者為製造、後者為有效
    rng = extract_date_range(text)
    if rng:
        result["manufacture"], result["expiry"] = rng
        return result

    # 步驟 1：尋找製造日期
    for kw in _MANUFACTURE_KW:
        d = _date_after_keyword(text, kw)
        if d:
            result["manufacture"] = d
            break

    # 步驟 2：若有製造日期，嘗試從「保存期限 X 個月」推算有效日期
    if result["manufacture"] is not None:
        months = extract_shelf_life_months(text)
        if months is not None:
            result["expiry"] = _add_months(result["manufacture"], months)
            result["shelf_life_months"] = months

    # 步驟 3：尋找明確標示的有效日期（優先覆蓋推算值）
    for kw in _EXPIRY_KW:
        d = _date_after_keyword(text, kw)
        if d:
            result["expiry"] = d
            break

    # 步驟 4：仍無有效日期時，第一個出現的日期預設為 expiry
    if result["expiry"] is None:
        date_str = extract_date_str(text)
        if date_str:
            parsed = parse_date(date_str)
            if parsed and parsed != result["manufacture"]:
                result["expiry"] = parsed

    return result


def extract_shelf_life_months(text: str) -> Optional[int]:
    """
    從文字中擷取「保存期限 X 個月」的 X 值。

    >>> extract_shelf_life_months("保存期限:10個月")
    10
    >>> extract_shelf_life_months("保存期限 6 個月")
    6
    >>> extract_shelf_life_months("無相關資訊")
    """
    m = _PAT_SHELF.search(text)
    return int(m.group(1)) if m else None


def extract_date_range(text: str) -> Optional[tuple[dict, dict]]:
    """
    擷取「製造日期 - 有效日期」區間，回傳 (manufacture, expiry)；後者須晚於前者才採用。

    >>> extract_date_range("25.10.28-26.09.27 20:59 023")
    ({'year': '2025', 'month': '10', 'day': '28'}, {'year': '2026', 'month': '09', 'day': '27'})
    >>> extract_date_range("2026 06 25 - 2027 06 24")
    ({'year': '2026', 'month': '06', 'day': '25'}, {'year': '2027', 'month': '06', 'day': '24'})
    """
    for m in _PAT_RANGE.finditer(text):
        g = m.groups()
        start = _make_date(_expand_year(g[0]), g[1], g[2])
        end = _make_date(_expand_year(g[3]), g[4], g[5])
        if start and end and _as_tuple(end) > _as_tuple(start):
            return start, end
    return None


# ── 內部輔助 ──────────────────────────────────────────────────────────────────

def _to_date(m: re.Match, order: str) -> Optional[dict]:
    """依欄位順序把 regex 匹配結果轉為日期 dict；月/日超出範圍時回傳 None。"""
    a, b, c = m.group(1), m.group(2), m.group(3)
    if order == "ymd":
        return _make_date(a, b, c)
    if order == "dmy":
        return _make_date(c, b, a)
    if order == "dmy_abbr":
        return _make_date(c, str(_MONTH_ABBR[b[:3].upper()]), a)
    if order == "yymmdd":
        return _make_date(_expand_year(a), b, c)
    raise ValueError(order)


def _make_date(year: str, month: str, day: str) -> Optional[dict]:
    if not (1 <= int(month) <= 12 and 1 <= int(day) <= 31):
        return None
    return {"year": year, "month": month.zfill(2), "day": day.zfill(2)}


def _expand_year(y: str) -> str:
    """兩位數年份補為 20YY。"""
    return y if len(y) == 4 else "20" + y


def _as_tuple(d: dict) -> tuple[int, int, int]:
    return int(d["year"]), int(d["month"]), int(d["day"])


def _date_after_keyword(text: str, keyword: str) -> Optional[dict]:
    """在關鍵字之後的文字中提取第一個日期。"""
    idx = text.find(keyword)
    if idx == -1:
        return None
    after = text[idx + len(keyword):]
    date_str = extract_date_str(after)
    return parse_date(date_str) if date_str else None


def _add_months(d: dict, months: int) -> dict:
    """將日期往後推算指定月數，閏年與月底溢位由 relativedelta 處理。"""
    dt = date(int(d["year"]), int(d["month"]), int(d["day"]))
    dt2 = dt + relativedelta(months=months)
    return {
        "year":  str(dt2.year),
        "month": str(dt2.month).zfill(2),
        "day":   str(dt2.day).zfill(2),
    }


# ── 快速自測 ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cases = [
        "2027.01.13.19:55\n樂事\n洋芋片\n青檸享清新口味",
        "製造2026/05/05\n50Gx10入\n玉黍叔\n甜辣口味",
        "製造2026/05/05\n保存期限:10個月\n玉黍叔",          # 推算有效日期
        "製造2026/07/31\n保存期限:1個月\n月底溢位測試",      # 7/31 + 1月 = 8/31
        "有效日期：\n280g(14人)X12包\n2027.03.15 65859\n益生菌",
        "有效日期:2026 10 10 07:56 002 00232 1B2\n科学超",
        "有效日期:2026.10.05 07:15 002\n韓式泡菜\n來一客",
        "2027 10 09 C072\n維他露P\n易開罐250毫升x24罐",
        "製造2026/05/04\n有效日期:2027/05/04\n華元真魷味",   # 明確有效日期優先
        "華元\n製造2026/05/05\n50GX10入\n真魷味\n保存期限:10個月",
        "MOS BURGER\n6包/盒；4盒/箱\n有效日期：20280409",     # yyyymmdd 無分隔
        "barcode 14710421020084\n有效日期：20280409",         # 條碼不誤判
    ]

    for ocr in cases:
        first_line = ocr.split("\n")[0]
        result = extract_dates(ocr)
        print(f"OCR : {first_line}")
        print(f"  expiry   : {result['expiry']}")
        print(f"  manufacture: {result['manufacture']}")
        print()
