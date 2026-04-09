"""
LLM-Forge 自動上傳層
將每個 LLM 調用自動報告到中央 Hub
離線隊列機制（失敗時本地保存）
"""

import asyncio
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

import aiohttp


@dataclass
class LLMCallRecord:
    """LLM 調用記錄"""
    id: str
    projectId: str
    pipelineId: str
    stage: str
    systemPromptHash: str
    userPromptHash: str
    outputLength: int
    tokensIn: int
    tokensOut: int
    costUSD: float
    durationMs: int
    model: str
    success: bool
    errorMessage: Optional[str] = None
    timestamp: int = 0
    systemPrompt: Optional[str] = None
    userPrompt: Optional[str] = None


# 配置（從環境變數讀取）
HUB_URL = os.getenv("LLM_FORGE_HUB_URL", "http://localhost:8765")
PROJECT_ID = os.getenv("LLM_FORGE_PROJECT_ID", "imggen")
ENABLED = os.getenv("LLM_FORGE_ENABLED", "false").lower() == "true"

OFFLINE_QUEUE_PATH = Path(".tmp") / "llm-forge-queue.json"
offline_queue: list[LLMCallRecord] = []


# ─── 初始化 ────────────────────────────────────────────────────────────


async def load_offline_queue() -> None:
    """加載離線隊列"""
    global offline_queue
    try:
        if OFFLINE_QUEUE_PATH.exists():
            with open(OFFLINE_QUEUE_PATH) as f:
                data = json.load(f)
                offline_queue = [LLMCallRecord(**record) for record in data]
                print(f"[llm-forge] Loaded {len(offline_queue)} offline records")
    except Exception as e:
        print(f"[llm-forge] Failed to load offline queue: {e}")


async def save_offline_queue() -> None:
    """保存離線隊列"""
    try:
        OFFLINE_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OFFLINE_QUEUE_PATH, "w") as f:
            json.dump([asdict(record) for record in offline_queue], f, indent=2)
    except Exception as e:
        print(f"[llm-forge] Failed to save offline queue: {e}")


async def flush_offline_queue() -> None:
    """刷新離線隊列"""
    global offline_queue
    if not ENABLED or not offline_queue:
        return

    remaining = []
    for record in offline_queue:
        success = await report_to_hub(record, save_on_failure=False)
        if not success:
            remaining.append(record)

    offline_queue = remaining
    await save_offline_queue()

    if len(offline_queue) < len(remaining):
        print(f"[llm-forge] Flushed {len(remaining) - len(offline_queue)} offline records")


# ─── 上傳機制 ────────────────────────────────────────────────────────────


async def report_to_hub(
    record: LLMCallRecord, save_on_failure: bool = True
) -> bool:
    """報告到 Hub"""
    global offline_queue
    if not ENABLED:
        return True

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{HUB_URL}/api/hub/call-record",
                json=asdict(record),
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status == 201:
                    return True

                if save_on_failure:
                    offline_queue.append(record)
                    await save_offline_queue()
                return False
    except Exception as e:
        if save_on_failure:
            offline_queue.append(record)
            await save_offline_queue()
        return False


# ─── 公開 API ────────────────────────────────────────────────────────────


async def init_llm_forge_auto_report() -> None:
    """初始化 LLM-Forge 自動報告"""
    if not ENABLED:
        print("[llm-forge] Auto-reporting disabled (set LLM_FORGE_ENABLED=true to enable)")
        return

    await load_offline_queue()
    await flush_offline_queue()
    print(f"[llm-forge] Auto-reporting enabled (Hub: {HUB_URL})")


async def record_llm_call(
    pipeline_id: str,
    stage: str,
    system_prompt: str,
    user_prompt: str,
    output: str,
    tokens_in: int,
    tokens_out: int,
    model: str,
    duration_ms: int,
    success: bool,
    error_message: Optional[str] = None,
) -> None:
    """記錄 LLM 調用"""
    if not ENABLED:
        return

    import time
    record = LLMCallRecord(
        id=f"{int(time.time() * 1000)}{hash(user_prompt) % 10000:04d}",
        projectId=PROJECT_ID,
        pipelineId=pipeline_id,
        stage=stage,
        systemPromptHash=hash_text(system_prompt),
        userPromptHash=hash_text(user_prompt),
        outputLength=len(output),
        tokensIn=tokens_in,
        tokensOut=tokens_out,
        costUSD=calculate_cost(model, tokens_in, tokens_out),
        durationMs=duration_ms,
        model=model,
        success=success,
        errorMessage=error_message,
        timestamp=int(time.time() * 1000),
        systemPrompt=system_prompt,
        userPrompt=user_prompt,
    )

    reported = await report_to_hub(record)
    if not reported:
        print(f"[llm-forge] Failed to report call {record.id}, saved to offline queue")


def hash_text(text: str) -> str:
    """計算文本哈希"""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """計算成本"""
    rates = {
        "claude-haiku-4-5-20251001": {"input": 0.8 / 1000000, "output": 4 / 1000000},
        "claude-sonnet-4-6": {"input": 3 / 1000000, "output": 15 / 1000000},
        "claude-opus-4-6": {"input": 15 / 1000000, "output": 75 / 1000000},
        "gemini-2.5-flash": {"input": 0.075 / 1000000, "output": 0.3 / 1000000},
        "gpt-4o": {"input": 2.5 / 1000000, "output": 10 / 1000000},
    }
    rate = rates.get(model, rates["claude-sonnet-4-6"])
    return tokens_in * rate["input"] + tokens_out * rate["output"]


async def flush_and_shutdown() -> None:
    """關閉前刷新隊列"""
    try:
        await asyncio.wait_for(flush_offline_queue(), timeout=5.0)
        if not offline_queue:
            print("[llm-forge] All records flushed")
        else:
            print(f"[llm-forge] {len(offline_queue)} records remain in offline queue")
    except asyncio.TimeoutError:
        if offline_queue:
            print(
                f"[llm-forge] Shutdown with {len(offline_queue)} records in offline queue (will retry on next run)"
            )
