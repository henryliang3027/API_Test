# 紙箱品名／日期辨識評估

## 目錄

```
eval_dataset/20260920_v3/   評估資料集（144 張圖 + ground_truth.json）
gemini_pipeline/            方法 A：Gemini OCR
  gemini_ocr.py             ocr_image()，預設用 PROMPT（原 prompt），另有 PROMPT_V4
  prompts/prompt_v*.txt     prompt 調優各版本
glm_ocr_pipeline/           方法 B：GLM-OCR + 日期字串解析 + 品名 json 資料庫
eval/                       評估腳本
  scoring.py                共用評分函式
  results/                  評估結果
```

## 共通說明

- 所有指令都在**專案根目錄**執行，Python 使用 `pvenv/bin/python`。
- 評分指標：
  - 品名：正規化後 SequenceMatcher 相似度 ≥ 0.6 算對。
  - 有效日期、製造日期：需完全相符，兩邊都是 null 也算對。
  - 主要指標是 `name + exp + mfg` 三項全對。

## gemini_pipeline 評估

需要在 `.env` 設定 `GEMINI_API_KEY`。

### 本機評估（直接呼叫 `gemini_ocr.ocr_image()`）

```bash
pvenv/bin/python eval/eval_gemini_local.py OUT.json [prompt檔|-] [圖片1,圖片2,...]
```

- `OUT.json`：逐張結果輸出路徑，相對路徑以專案根目錄為準。
- `prompt檔`：可省略。省略或給 `-` 時，使用 `gemini_ocr.py` 裡的 `PROMPT`。
- 第三個參數：只跑指定的圖片，以逗號分隔。
- 12 張平行執行，144 張約需 1～2 分鐘。

範例：

```bash
# 原 prompt
pvenv/bin/python eval/eval_gemini_local.py eval/results/gemini_local/base.json

# v4 prompt
pvenv/bin/python eval/eval_gemini_local.py eval/results/gemini_local/v4.json gemini_pipeline/prompts/prompt_v4.txt

# 只跑幾張
pvenv/bin/python eval/eval_gemini_local.py /tmp/out.json - t24.jpg,t59.jpg
```

輸出會列出錯誤的圖片，最後一行是總結：

```
N=144 name 87.5 exp 94.4 mfg 99.3 ALL 81.9
```

> Gemini 即使在 temperature=0 下結果也會飄，原 prompt 四次結果是 83.3 / 79.9 / 81.9 / 79.2%。比較 prompt 時建議多跑幾次。

## glm_ocr_pipeline 評估

需要的檔案：llama.cpp runtime `llama-b1287/`，以及模型 `models/glm-ocr/GLM-OCR-f16.gguf`、`models/glm-ocr/mmproj-GLM-OCR-Q8_0.gguf`。這兩者都不在 git 中，路徑可以用環境變數覆蓋，見 `glm_ocr_pipeline/config.py`。

1. 啟動 llama-server（port 8010），另開一個終端執行並保持運行：

   ```bash
   pvenv/bin/python -m glm_ocr_pipeline.llama_server
   ```

   確認已啟動：

   ```bash
   curl localhost:8010/health    # {"status":"ok"}
   ```

2. 執行評估：

   ```bash
   pvenv/bin/python eval/eval_glm_ocr.py [--data eval_dataset/20260920_v3] [--threshold 0.6] [--out OUT.json]
   ```

   - 一次跑一張，144 張約需 3～4 分鐘。
   - 逐張結果預設寫到 `eval/results/glm_ocr_per_image.json`。
   - 要保存報告的話，可以導出終端輸出：

     ```bash
     pvenv/bin/python eval/eval_glm_ocr.py | tee eval/results/glm_ocr_report.txt
     ```

- 品名資料庫：`glm_ocr_pipeline/box_name.json`
- 日期解析：`glm_ocr_pipeline/date_extractor.py`
