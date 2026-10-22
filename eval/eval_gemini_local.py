"""Local eval: call gemini_pipeline.gemini_ocr.ocr_image directly, score with eval/scoring.py.
Usage: python eval/eval_gemini_local.py OUT.json [prompt_file] [only=img1,img2]"""
import json, os, sys, time, importlib.util
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); os.chdir(ROOT)
from dotenv import load_dotenv; load_dotenv(os.path.join(ROOT, ".env"))
import scoring
from gemini_pipeline import gemini_ocr

out = sys.argv[1]
if len(sys.argv) > 2 and sys.argv[2] != "-":
    gemini_ocr.PROMPT = open(sys.argv[2], encoding="utf-8").read()
only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
DATA = os.path.join(ROOT, "eval_dataset/20260920_v3")
gt_all = json.load(open(os.path.join(DATA, "ground_truth.json"), encoding="utf-8"))
names = sorted(gt_all, key=scoring.sort_key)
if only: names = [n for n in names if n in only]
client = gemini_ocr.get_client()

def date(d):
    if not isinstance(d, dict): return None
    return scoring.normalize_date(d)

def run(fname):
    gt = gt_all[fname]
    for attempt in range(4):
        try:
            t0 = time.time(); res = gemini_ocr.ocr_image(client, os.path.join(DATA, fname)); el = time.time()-t0
            break
        except Exception as e:
            err = str(e); time.sleep(5*(attempt+1))
    else:
        return {"image": fname, "error": err, "all_ok": False, "name_ok": False, "exp_ok": False, "mfg_ok": False, "raw": None}
    boxes = res or []
    sim = lambda b: scoring.name_similarity(b.get("product_name") or "", gt["product_name"])
    pred = max(boxes, key=sim) if boxes else {}
    s = sim(pred) if pred else 0.0
    r = {"image": fname, "elapsed": round(el, 2), "n_boxes": len(boxes), "gt_name": gt["product_name"],
         "pred_name": pred.get("product_name"), "name_sim": round(s, 3), "name_ok": s >= 0.6,
         "gt_exp": date(gt["expiration_date"]), "pred_exp": date(pred.get("expiration_date")),
         "gt_mfg": date(gt["manufacturer_date"]), "pred_mfg": date(pred.get("manufacturer_date")), "raw": boxes}
    r["exp_ok"] = r["gt_exp"] == r["pred_exp"]; r["mfg_ok"] = r["gt_mfg"] == r["pred_mfg"]
    r["all_ok"] = r["name_ok"] and r["exp_ok"] and r["mfg_ok"]
    return r

with ThreadPoolExecutor(12) as ex:
    results = list(ex.map(run, names))
json.dump(results, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n = len(results); P = lambda k: 100*sum(bool(r.get(k)) for r in results)/n
for r in results:
    if not r["all_ok"]:
        print(f"{r['image']:9s} name{'✓' if r['name_ok'] else '✗'} {r.get('name_sim')} exp{'✓' if r['exp_ok'] else '✗'} {r.get('pred_exp')} gt={r.get('gt_exp')} mfg{'✓' if r['mfg_ok'] else '✗'} {r.get('pred_mfg')} gt={r.get('gt_mfg')} | {r.get('pred_name')} || GT {r.get('gt_name')} {r.get('error','')}")
print(f"N={n} name {P('name_ok'):.1f} exp {P('exp_ok'):.1f} mfg {P('mfg_ok'):.1f} ALL {P('all_ok'):.1f}")
