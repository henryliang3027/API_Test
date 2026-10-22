"""Rescore Gemini/GPT local eval results with the GLM-OCR product json DB (glm_ocr_pipeline/box_name.json),
so product_name is compared under the same condition as method B. No API calls: reuses each result's "raw" boxes.

Each box's product_name goes through ProductDatabase.match (same keyword scoring as GLM, which matches on OCR text):
  - db     : no match -> product=None (same as GLM)
  - db+fb  : no match -> keep the model's own product_name
Dates are unchanged.

Usage: pvenv/bin/python eval/rescore_with_db.py RESULT.json [RESULT.json ...]
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import scoring
from glm_ocr_pipeline.product_db import ProductDatabase

db = ProductDatabase()


def db_name(box, fallback):
    matched = db.match(box.get("product_name") or "")
    if matched:
        return f"{matched['brand']} {matched['name']}", matched["name"]
    return (box.get("product_name") or "", None) if fallback else ("", None)


def name_ok(boxes, gt_name, fallback):
    # same as eval_glm_ocr.box_similarity: max of "brand name" and name alone; best box vs GT
    sims = [max(scoring.name_similarity(full, gt_name), scoring.name_similarity(name or "", gt_name))
            for full, name in (db_name(b, fallback) for b in boxes)]
    return max(sims, default=0.0) >= 0.6


for path in sys.argv[1:]:
    results = json.load(open(path, encoding="utf-8"))
    n = len(results)
    P = lambda xs: 100 * sum(xs) / n
    row = {"orig": [r["name_ok"] for r in results]}
    for label, fb in (("db", False), ("db+fb", True)):
        row[label] = [name_ok(r.get("raw") or [], r["gt_name"], fb) if r.get("gt_name") else False for r in results]
    dates = [r["exp_ok"] and r["mfg_ok"] for r in results]
    print(f"{os.path.relpath(path, ROOT)}  N={n}  exp {P([r['exp_ok'] for r in results]):.1f}  mfg {P([r['mfg_ok'] for r in results]):.1f}")
    for label, oks in row.items():
        print(f"  {label:6s} name {P(oks):5.1f}  ALL {P([a and d for a, d in zip(oks, dates)]):5.1f}")
