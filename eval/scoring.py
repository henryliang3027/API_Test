"""Scoring functions shared by the eval scripts.

  - product_name: fuzzy match (normalized SequenceMatcher ratio >= threshold)
  - expiration_date / manufacturer_date: exact match (null == null counts as correct)
"""
import difflib
import re
import unicodedata


def normalize_name(s):
    # full-width -> half-width, lowercase, drop spaces/punctuation/symbols
    s = unicodedata.normalize("NFKC", s or "").lower()
    return "".join(c for c in s if unicodedata.category(c)[0] in "LN")


def name_similarity(pred, gt):
    p, g = normalize_name(pred), normalize_name(gt)
    if not p or not g:
        return 0.0
    if p in g or g in p:
        # containment: e.g. missing brand prefix, score by length coverage
        return max(difflib.SequenceMatcher(None, p, g).ratio(), min(len(p), len(g)) / max(len(p), len(g)))
    return difflib.SequenceMatcher(None, p, g).ratio()


def normalize_date(d):
    if not isinstance(d, dict):
        return None
    try:
        return f"{int(d['year']):04d}-{int(d['month']):02d}-{int(d['day']):02d}"
    except (KeyError, TypeError, ValueError):
        return None


def sort_key(f):
    return (f[0], int(re.search(r"\d+", f).group()))


def product_name(box):
    product = box.get("product") or {}
    brand, name = product.get("brand") or "", product.get("name") or ""
    return f"{brand} {name}".strip()


def box_similarity(box, gt_name):
    # API splits brand/name; GT sometimes includes the brand, sometimes not
    product = box.get("product") or {}
    return max(name_similarity(product_name(box), gt_name),
               name_similarity(product.get("name") or "", gt_name))
