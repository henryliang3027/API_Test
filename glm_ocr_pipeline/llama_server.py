"""
llama_server.py — 啟動 / 停止本專案的 llama.cpp runtime（llama-server 載入 GLM-OCR）
=================================================================================
用法：
    python -m glm_ocr_pipeline.llama_server          # 前景啟動，Ctrl+C 結束

    from glm_ocr_pipeline.llama_server import LlamaServer
    with LlamaServer():                              # 程式內啟動，離開 with 自動關閉
        ...
"""

import os
import subprocess
import time

import httpx

from glm_ocr_pipeline import config


def build_command() -> list[str]:
    return [
        config.LLAMA_SERVER_BIN,
        "-m", config.GLM_OCR_MODEL,
        "--mmproj", config.GLM_OCR_MMPROJ,
        "--host", config.LLAMA_HOST,
        "--port", str(config.LLAMA_PORT),
        "--ctx-size", config.CTX_SIZE,
        "-ngl", config.N_GPU_LAYERS,
    ]


def is_ready(port: int = config.LLAMA_PORT) -> bool:
    try:
        return httpx.get(f"http://localhost:{port}/health", timeout=2).status_code == 200
    except Exception:
        return False


class LlamaServer:
    """以子程序啟動 llama-server；若該 port 已有 server 在跑則直接沿用。"""

    def __init__(self, timeout: int = 180, log_path: str | None = None) -> None:
        self.timeout = timeout
        self.log_path = log_path
        self.proc: subprocess.Popen | None = None

    def start(self) -> None:
        if is_ready():
            print(f"[llama-server] port {config.LLAMA_PORT} 已就緒，沿用既有 server")
            return
        env = os.environ.copy()
        # llama-b1287 內附 ROCm / ggml 動態函式庫
        env["LD_LIBRARY_PATH"] = config.LLAMA_DIR + ":" + env.get("LD_LIBRARY_PATH", "")
        cmd = build_command()
        print(f"[llama-server] starting: {' '.join(cmd)}")
        out = open(self.log_path, "w") if self.log_path else None
        self.proc = subprocess.Popen(cmd, env=env, stdout=out, stderr=subprocess.STDOUT if out else None)

        deadline = time.time() + self.timeout
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"llama-server 啟動失敗 (exit {self.proc.returncode})")
            if is_ready():
                print("[llama-server] ready")
                return
            time.sleep(2)
        self.stop()
        raise RuntimeError(f"llama-server 在 {self.timeout}s 內未就緒")

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            print("[llama-server] shutting down")
            self.proc.terminate()
            self.proc.wait(timeout=30)
        self.proc = None

    def __enter__(self) -> "LlamaServer":
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.stop()


if __name__ == "__main__":
    server = LlamaServer()
    server.start()
    try:
        while server.proc is None or server.proc.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
