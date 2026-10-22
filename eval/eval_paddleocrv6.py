"""Evaluate the PP-OCRv6 + date string parsing + product json DB method on a labeled image folder.

Metrics (eval/scoring.py):
  - product_name: fuzzy match (normalized SequenceMatcher ratio >= --threshold) on "brand name"
  - expiration_date / manufacturer_date: exact match (null == null counts as correct)
  - seconds per image (PP-OCRv6 inference + parsing)

The whole image is sent to PP-OCRv6 as a single box (no YOLO segmentation).

Environment: needs paddleocr, run with paddle_venv/bin/python.
Runs on the AMD GPU by default; set PPOCRV6_DEVICE=cpu for Paddle Inference on CPU.

Usage:
    paddle_venv/bin/python eval/eval_paddleocrv6.py [--data eval_dataset/20260920_v3] [--threshold 0.6]
"""
import argparse
import json
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scoring import box_similarity, normalize_date, product_name, sort_key
from paddleocrv6_pipeline import config
from paddleocrv6_pipeline.pipeline import PaddleOcrV6Pipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=os.path.join(ROOT, "eval_dataset", "20260920_v3"))
    parser.add_argument("--threshold", type=float, default=0.6, help="fuzzy match threshold for product_name")
    parser.add_argument("--out", default=os.path.join(ROOT, "eval", "results", "paddleocrv6_gpu_per_image.json" if config.USE_GPU else "paddleocrv6_per_image.json"), help="per-image results json")
    args = parser.parse_args()

    with open(os.path.join(args.data, "ground_truth.json"), encoding="utf-8") as f:
        ground_truth = json.load(f)

    pipeline = PaddleOcrV6Pipeline()
    results = []
    for i, fname in enumerate(sorted(ground_truth, key=sort_key), 1):
        gt = ground_truth[fname]
        t0 = time.time()
        try:
            data = pipeline.run(os.path.join(args.data, fname))
            error = None
        except Exception as e:
            data, error = {}, str(e)
        elapsed = time.time() - t0

        boxes = data.get("boxes") or []
        pred = max(boxes, key=lambda b: box_similarity(b, gt["product_name"])) if boxes else {}
        sim = box_similarity(pred, gt["product_name"]) if pred else 0.0
        r = {
            "image": fname,
            "elapsed": round(elapsed, 3),
            "error": error,
            "n_boxes": len(boxes),
            "gt_name": gt["product_name"],
            "pred_name": product_name(pred) if pred and pred.get("product") else None,
            "name_sim": round(sim, 3),
            "name_ok": sim >= args.threshold,
            "gt_exp": normalize_date(gt["expiration_date"]),
            "pred_exp": normalize_date(pred.get("expiry_date")),
            "gt_mfg": normalize_date(gt["manufacturer_date"]),
            "pred_mfg": normalize_date(pred.get("manufacture_date")),
            "ocr_text": data.get("ocr_text"),
        }
        r["exp_ok"] = r["gt_exp"] == r["pred_exp"]
        r["mfg_ok"] = r["gt_mfg"] == r["pred_mfg"]
        r["all_ok"] = r["name_ok"] and r["exp_ok"] and r["mfg_ok"]
        results.append(r)

        mark = lambda ok: "✓" if ok else "✗"
        print(f"[{i:3d}/{len(ground_truth)}] {fname:9s} {elapsed:5.2f}s boxes={len(boxes)} "
              f"name {mark(r['name_ok'])} {sim:.2f}  exp {mark(r['exp_ok'])} "
              f"pred={r['pred_exp']} gt={r['gt_exp']}  mfg {mark(r['mfg_ok'])}  | {r['pred_name']}"
              + (f"  ERROR: {error}" if error else ""), flush=True)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    n = len(results)
    pct = lambda key, rs=results: 100 * sum(r[key] for r in rs) / len(rs) if rs else 0.0
    exp_labeled = [r for r in results if r["gt_exp"]]
    mfg_labeled = [r for r in results if r["gt_mfg"]]
    times = [r["elapsed"] for r in results]
    print(f"\n=== PP-OCRv6 + 日期字串解析 + 品名json資料庫 eval ({n} images) ===")
    print(f"request success      : {100 * sum(r['error'] is None for r in results) / n:.1f}%")
    print(f"product matched (DB) : {100 * sum(r['pred_name'] is not None for r in results) / n:.1f}%")
    print(f"product_name (fuzzy≥{args.threshold}): {pct('name_ok'):.1f}%   mean sim {statistics.mean(r['name_sim'] for r in results):.3f}")
    print(f"expiration_date      : {pct('exp_ok'):.1f}%   (on {len(exp_labeled)} labeled: {pct('exp_ok', exp_labeled):.1f}%)")
    print(f"manufacturer_date    : {pct('mfg_ok'):.1f}%   (on {len(mfg_labeled)} labeled: {pct('mfg_ok', mfg_labeled):.1f}%)")
    print(f"name + exp + mfg ok  : {pct('all_ok'):.1f}%")
    print(f"time / image         : mean {statistics.mean(times):.2f}s  median {statistics.median(times):.2f}s  "
          f"min {min(times):.2f}s  max {max(times):.2f}s")
    print(f"per-image results    : {args.out}")


if __name__ == "__main__":
    main()
