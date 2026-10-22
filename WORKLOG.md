# 工作紀錄：紙箱品名／日期辨識評估

最後更新：2026-10-05。新開 Claude Code session 時，請先讀這份檔案。

## 目錄結構

- `eval_dataset/`：評估資料集。
- `gemini_pipeline/`：方法 A 的實作，包含 `gemini_ocr.py`、`draw_utils.py`，prompt 各版本放在 `prompts/`。
- `glm_ocr_pipeline/`：方法 B 的實作。
- `paddleocrv6_pipeline/`：方法 C 的實作。
- `gpt_pipeline/`：方法 D 的實作。根目錄的 `gpt_ocr.py` 是早期版本。
- `eval/`：評估腳本，從專案根目錄執行，例如 `pvenv/bin/python eval/eval_glm_ocr.py`。結果放在 `eval/results/`。
- 環境：系統沒有 `python` 指令，`vlmvenv` 缺套件，跑評估請用 `pvenv/bin/python`。方法 C 需要 paddleocr，改用 `paddle_venv/bin/python`，預設跑在 AMD GPU 上。
- 其他（早期 GPT 實驗、Mistral、MiniCPM、貨架計數、`test_*.py`、`test_images/`）是早期實驗，留在根目錄。

## 評估資料與指標

- **資料集**：`eval_dataset/20260920_v3`，共 144 張圖。答案在 `ground_truth.json`，備註在 `ground_truth_notes.tsv`。
- **評分方式**：評分函式在 `eval/scoring.py`，原本在 `eval_gemini.py`，該檔已於 2026-10-05 刪除。
  - 品名：正規化後的 SequenceMatcher 相似度 ≥ 0.6 算對。
  - 有效日期、製造日期：需完全相符，兩邊都是 null 也算對。
  - 主要指標：**name + exp + mfg 三項全對**。

## 方法 A：Gemini（`gemini_pipeline/gemini_ocr.py`，模型 `gemini-3.5-flash-lite`）

- `PROMPT`：原 prompt，**目前 `ocr_image()` 使用這一版**。
- `PROMPT_V4`：調優版。要改用的話，把 `ocr_image()` 裡的 `PROMPT` 換成 `PROMPT_V4`。
- **本機評估**：直接呼叫 `ocr_image()`，不經 `box_matcher`。腳本是 `eval/eval_gemini_local.py`。
  - 用法：`pvenv/bin/python eval/eval_gemini_local.py OUT.json [prompt檔]`，OUT 的相對路徑以專案根目錄為準。
  - 會平行跑 12 張。
- **調優過程**：v1～v5 的 prompt 存在 `gemini_pipeline/prompts/prompt_v*.txt`，原 prompt 與 v4 的評估結果在 `eval/results/gemini_local/`。

| | 品名 | 有效日期 | 製造日期 | 三項全對 | 每張耗時 |
|---|---|---|---|---|---|
| 原 prompt（2 次） | 88.9 / 83.3 | 95.1 / 95.1 | 98.6 / 100 | **83.3 / 79.9** | 約 5.8s |
| v4（2 次） | 99.3 / 99.3 | 97.2 / 97.9 | 100 / 100 | **96.5 / 97.2** | 約 5.7s |

- **v4 調整方向**：
  - 品名：排除容量規格、廣告標語、英文翻譯、法規類別；中英對照的品牌只取中文；保留商品 Logo 上的文字。
  - 日期：新增日期區間、yymmdd、日月年格式；製造日期只看明確標示；外箱噴印的日期優先；描述點陣數字的字形。
  - 紙箱：同一箱多面合併；開口展示箱也算紙箱。
- **v4 仍錯的圖**：
  - t24、t25 年份模糊，待人工確認。`ground_truth.json` 標 2020，`notes.tsv` 標 2026/2024。
  - t59、t90 點陣日期讀錯。
- **注意事項**：
  - Gemini 在 temperature=0 下結果還是會飄。原 prompt 跑兩次，就有 19 張結果不一致。2026-10-02 跑了第 3 次（`base3.json`），三項全對 81.9%，和第 2 次比有 21 張結果不同。2026-10-05 跑了第 4 次（`base4.json`），三項全對 79.2%。
  - v4 的範例有不少取自測試圖，有過擬合風險，建議用另一批新圖驗證。
- **遠端 API**（`https://logistics2.sstc-aiteam.org/api/v1/detect/image`）：
  - 之前用 `eval_gemini.py` 評估，結果見 `eval/results/gemini_api_report.txt`，原始結果 71.5%。這支腳本已於 2026-10-05 刪除，目前沒有遠端評估腳本。
  - 遠端分數偏低，主因是遠端服務的 `box_matcher.py` 會用它的 `box_name.json` 關鍵字覆蓋品名，例如「統一」會被改成「統一 冰塊」。
  - 遠端尚未部署 v4。

## 方法 B：GLM-OCR + 日期字串解析 + 品名 json 資料庫（`glm_ocr_pipeline/`，不含 YOLO）

- **參考來源**：`/home/ubuntu/Documents/Github/service_template`。
- **Runtime**：`llama-b1287/`，已加進 `.gitignore`。
- **模型**：`models/glm-ocr/GLM-OCR-f16.gguf`、`mmproj-GLM-OCR-Q8_0.gguf`。
- **啟動 llama-server**：`python -m glm_ocr_pipeline.llama_server`，使用 port 8010。
  - service_template 自己的 server 在 port 8000，不要動它。
- **評估**：`pvenv/bin/python eval/eval_glm_ocr.py`，一次跑一張。
  - 逐張結果寫到 `eval/results/glm_ocr_per_image.json`。
  - 報告存成 `eval/results/glm_ocr_report.txt`。
- **品名資料庫**：以 `glm_ocr_pipeline/box_name.json` 為主，共 92 筆。
  - 這份是依這 144 張的 GT 品項建立的，品名準確度會比實際上線樂觀。
  - 本機原有 Gemini 用的 `box_matcher.py` 和 `box_name.json`，已於 2026-10-02 刪除，因為已不再使用。
- **日期解析**：`glm_ocr_pipeline/date_extractor.py`，以 service_template 版為基礎，新增 yymmdd、日期區間、日月年（含英文月份縮寫）。

| | 品名 | 有效日期 | 製造日期 | 三項全對 | 每張耗時 |
|---|---|---|---|---|---|
| 原始 10 筆資料庫 | 11.8 | 79.2 | 97.2 | 11.8 | 1.42s |
| 黑松純水移除 PURE WATER 關鍵字 | 93.1 | 87.5 | 97.9 | 81.2 | 1.49s |
| **目前狀態**（92 筆資料庫＋新日期格式，黑松純水已加回 PURE WATER） | 95.8 | 87.5 | 97.9 | **84.0** | 1.44s |

- **與 Gemini 的比較結論**：
  - GLM 只贏在品名，因為它從照答案建的資料庫挑標準名稱，Gemini 則要自由寫出品名。
  - 把 Gemini 的品名也送進同一個資料庫比對，Gemini 原 prompt 的三項全對是 **88.9 / 89.6%**，高於 GLM。
  - GLM 的日期明顯較弱：87.5%，Gemini 是 95%。

## 方法 C：PP-OCRv6 + 日期字串解析 + 品名 json 資料庫（`paddleocrv6_pipeline/`，不含 YOLO）

- 2026-10-05 建立。流程同方法 B，只把 OCR 換成 PP-OCRv6；`date_extractor.py` 和 `box_name.json` 直接沿用 `glm_ocr_pipeline/`。
- **環境**：`paddle_venv/`（paddle 3.3.1 CPU 版、paddleocr 3.7.0、torch 2.13.0+rocm7.2）。原本是 `PaddleVL/pvenv`，2026-10-05 移到根目錄，`PaddleVL/` 已刪除。
- **預設用 GPU**（Radeon RX 9070 XT，gfx1201）。`config.DEVICE` 決定引擎，可用環境變數 `PPOCRV6_DEVICE` 切換：
  - `gpu:0`（預設）：`engine="transformers"`，透過 PyTorch ROCm 推論，讀 `models/paddleocrv6/PP-OCRv6_medium_{det,rec}_safetensors`。paddlepaddle 本身不支援 AMD GPU。
  - `cpu`：`engine="paddle"`（Paddle Inference），讀 `models/paddleocrv6/PP-OCRv6_medium_{det,rec}`（pdiparams）。
- **模型來源**：原 `PaddleVL/` 裡沒有 v6 模型。pdiparams 版從 `~/.paddlex/official_models/` 複製；safetensors 版是 paddlex 從 Hugging Face 自動下載後再複製過來的。
- **GPU 注意事項**：
  - 一定要設 `MIOPEN_FIND_MODE=FAST`（`ocr_client.py` 已在 import torch 前設定）。MIOpen 預設的演算法搜尋會一次要 5.3GB workspace，FAST 模式峰值約 1GB。
  - 每遇到新的圖片尺寸，MIOpen 第一次要編譯 kernel，多花 1～3 秒。編譯結果會快取在磁碟。
  - VRAM 不夠會 OOM（每張需要 0.4～0.7GB 暫存）。第一次跑時 port 8000 和 8010 的 llama-server 共占 14GB，有 40 張 OOM。2026-10-05 停掉本專案 port 8010 的 GLM server 後重跑才成功，要跑方法 B 時要重新啟動它。同一時間 port 8000 的 service_template server 也已經不在了，不是這個 session 停掉的。
- **CPU 注意事項**：CPU 開 oneDNN 會報 `ConvertPirAttribute2RuntimeAttribute` 錯誤，所以預設 `enable_mkldnn=False`。Paddle 每張圖都會把 PIR trace 印到 stdout。
- **評估**：`paddle_venv/bin/python eval/eval_paddleocrv6.py`。報告在 `eval/results/paddleocrv6_report.txt`，同時含 CPU 版和 GPU 版。
  - 逐張結果：CPU 版是 `paddleocrv6_per_image.json`，GPU 版是 `paddleocrv6_gpu_per_image.json`（腳本會依裝置自動選檔名）。

| | 品名 | 有效日期 | 製造日期 | 三項全對 | 每張耗時 |
|---|---|---|---|---|---|
| PP-OCRv6 medium（CPU，Paddle Inference） | 88.9 | 84.0 | 97.9 | **74.3** | 平均 5.82s，中位數 4.56s |
| PP-OCRv6 medium（GPU，transformers 引擎，2 次） | 88.2 / 88.2 | 81.9 / 81.9 | 97.9 / 97.9 | **72.2 / 72.2** | 平均 0.63s，中位數 0.59s |

- GPU 版兩次結果完全相同，跑起來是確定的。但它和 CPU 版只有 18 張 OCR 文字完全一樣，因為兩個引擎的前處理和數值實作不同。
  - 三項全對只有 GPU 版對的：t56、t61、t97。
  - 只有 CPU 版對的：t19、t48、t51、t55、t114、t136。

- **主要錯誤**（CPU 和 GPU 版相同）：
  - 品名：OCR 輸出簡體字（科学、满漢、葱燒、红燒），比對不到繁體關鍵字；品牌 Logo 字常沒讀到（茶裏王、悅氏）。
  - 日期：噴印日期被切段，例如「2027 0415」；日期和時間黏在一起，例如「EXP2026072209:31」。這兩種 `date_extractor` 都解析不到。
  - 點陣日期反而比 GLM 好：b6、t13、t40、t58、t59、t60、t137 這 7 張 PP-OCRv6 對、GLM 錯。
- **可能的改進（尚未做）**：OCR 文字先轉繁體（opencc）再比對品名；`date_extractor` 支援空格分隔的 yyyy mmdd 和日期後接時間。

## 方法 D：GPT（`gpt_pipeline/gpt_ocr.py`，模型 `gpt-5.6-sol`）

- 2026-10-05 建立。介面同方法 A（`get_client()`、`ocr_image()`、`PROMPT`）。
  - prompt 和大圖縮小（`_load_image_bytes`）直接從 `gemini_pipeline.gemini_ocr` 引用，與 Gemini 用完全相同的 prompt。
  - `reasoning.effort="high"`，對應 Gemini 的 `thinking_level=HIGH`。推理模型不支援 temperature。
  - 模型和 effort 可用環境變數 `GPT_MODEL`、`GPT_REASONING_EFFORT` 覆蓋。帳號可用的同系列模型還有 `gpt-5.6-luna`、`gpt-5.6-terra`、`gpt-6-sol`、`gpt-6.1-sol`。
- **評估**：`pvenv/bin/python eval/eval_gpt_local.py OUT.json [prompt檔]`，用法同 `eval_gemini_local.py`，平行 12 張。結果在 `eval/results/gpt_local/`（`base1.json` 為原 prompt，`v4a.json` 為 v4）。

| | 品名 | 有效日期 | 製造日期 | 三項全對 | 每張耗時 |
|---|---|---|---|---|---|
| 原 prompt（1 次） | 85.4 | 78.5 | 97.9 | **68.8** | 平均 12.5s，中位數 10.6s |
| v4（1 次） | 98.6 | 84.0 | 100 | **82.6** | 平均 10.0s，中位數 8.9s |

- **與 Gemini 比較**：同一個 prompt 下，GPT 兩版都比 Gemini 低約 14 個百分點（Gemini 原 prompt 約 80～83%，v4 約 97%），而且慢約一倍。
  - 品名在 v4 下和 Gemini 接近（98.6 vs 99.3）。
  - 主要差距在有效日期（84.0 vs 約 97.5）：點陣數字讀錯，例如 t90、t130 把 2028 讀成 2023，t124 把 2028 讀成 2026，t96、t99 把 08 讀成 09。
- 目前每種 prompt 只跑 1 次，還沒確認結果在不同次執行之間穩不穩定。

## 待辦／待決定

1. **品名比對的同分問題**：目前比對規則是「關鍵字命中數最多者勝，同分取資料庫中排前面的」。
   - 已發生的案例：
     - t96～t100 黑松純水被判成黑松 FIN，因為兩者都命中「黑松」。目前靠加回 `PURE WATER` 關鍵字暫時解決，同分規則本身還沒改。
     - t43 樂事經濟包被判成樂事青檸。
   - 候選做法，**待使用者決定**：
     1. 依關鍵字長度計分。
     2. 同分時只回傳品牌和系列，不硬選口味。
     3. 維持現狀。
2. **date_extractor 還沒支援的格式**：
   - 「2023年8月31日」（b7）
   - 「P2024/10/25 E2027/10/24」（t17）
   - 「保存期限：5年」（t44，目前只支援「X個月」）
   - 日期後面緊接數字的「2024122633」（b4）
3. **t24、t25 的 ground truth 年份**：待人工確認。
4. **v4 部署到遠端 API**：遠端還沒部署 v4。若要讓遠端分數達標，遠端服務 `box_name.json` 的關鍵字也需要調整，例如「統一」「VITALON」。

## 結果圖（`result/`）

- `t86_*`、`t66_*`、`t103_*`、`t9_*`：分別是 `_orig`（原 prompt）和 `_v4`，Gemini 原 prompt 與 v4 的對照。
- `t43_glm.jpg`：GLM-OCR 的結果，圖片下方附 OCR 原始文字。
