"""
提示詞日誌系統
本地記錄所有 LLM 調用的完整系統提示詞和用戶提示詞
用於版本控制和 prompt 優化分析
"""

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Any


DB_PATH = Path(".tmp") / "prompts.db"


def _init_db() -> None:
    """初始化提示詞數據庫"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompt_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            pipeline_id TEXT NOT NULL,
            stage TEXT NOT NULL,
            system_prompt TEXT NOT NULL,
            user_prompt TEXT NOT NULL,
            system_hash TEXT NOT NULL,
            user_hash TEXT NOT NULL,
            model TEXT,
            provider TEXT,
            output TEXT,
            output_length INTEGER,
            success BOOLEAN,
            error_message TEXT
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp ON prompt_logs(timestamp DESC)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_pipeline_stage ON prompt_logs(pipeline_id, stage)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_system_hash ON prompt_logs(system_hash)
    """)

    conn.commit()
    conn.close()


_init_db()


def hash_prompt(text: str) -> str:
    """計算提示詞哈希（16 字符）"""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


async def log_prompt_call(
    pipeline_id: str,
    stage: str,
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    output: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None,
) -> str:
    """
    記錄完整的提示詞調用

    Args:
        pipeline_id: 管道識別符（e.g., 'web-api', 'cli', 'batch'）
        stage: 處理階段（e.g., 'caption-generation', 'extraction'）
        system_prompt: 系統提示詞（完整）
        user_prompt: 用戶提示詞（完整）
        model: 使用的模型
        provider: 提供者（claude, gemini, gpt）
        output: LLM 輸出內容
        success: 調用是否成功
        error_message: 錯誤信息（失敗時）

    Returns:
        日誌記錄 ID
    """
    timestamp = int(datetime.now().timestamp() * 1000)
    system_hash = hash_prompt(system_prompt)
    user_hash = hash_prompt(user_prompt)
    output_length = len(output) if output else 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO prompt_logs (
            timestamp, pipeline_id, stage, system_prompt, user_prompt,
            system_hash, user_hash, model, provider, output, output_length,
            success, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        pipeline_id,
        stage,
        system_prompt,
        user_prompt,
        system_hash,
        user_hash,
        model,
        provider,
        output,
        output_length,
        success,
        error_message,
    ))

    conn.commit()
    log_id = cursor.lastrowid
    conn.close()

    return str(log_id)


def get_logs_by_stage(
    pipeline_id: str,
    stage: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """查詢指定 stage 的所有日誌"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM prompt_logs
        WHERE pipeline_id = ? AND stage = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (pipeline_id, stage, limit))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_versions_by_system_hash(system_hash: str) -> list[dict[str, Any]]:
    """查詢同一系統提示詞的所有版本"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT system_hash, user_hash, COUNT(*) as call_count,
               AVG(CASE WHEN success THEN 1 ELSE 0 END) as success_rate,
               MIN(timestamp) as first_call,
               MAX(timestamp) as last_call
        FROM prompt_logs
        WHERE system_hash = ?
        GROUP BY user_hash
        ORDER BY last_call DESC
    """, (system_hash,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_latest_calls(limit: int = 50) -> list[dict[str, Any]]:
    """查詢最新 N 個調用"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, timestamp, pipeline_id, stage, system_hash, user_hash,
               model, provider, output_length, success, error_message
        FROM prompt_logs
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def export_prompts_json(
    pipeline_id: str,
    stage: str,
    output_file: Optional[str] = None,
) -> str:
    """
    匯出提示詞為 JSON 文件

    Args:
        pipeline_id: 管道 ID
        stage: 階段
        output_file: 輸出文件路徑（可選，默認為 .tmp/prompts_export.json）

    Returns:
        導出文件路徑
    """
    if output_file is None:
        output_file = str(Path(".tmp") / f"prompts_{pipeline_id}_{stage}.json")

    logs = get_logs_by_stage(pipeline_id, stage, limit=1000)

    # 轉換為可序列化的格式
    export_data = []
    for log in logs:
        export_data.append({
            "id": log["id"],
            "timestamp": log["timestamp"],
            "pipeline_id": log["pipeline_id"],
            "stage": log["stage"],
            "system_prompt": log["system_prompt"],
            "user_prompt": log["user_prompt"],
            "system_hash": log["system_hash"],
            "user_hash": log["user_hash"],
            "model": log["model"],
            "provider": log["provider"],
            "output_length": log["output_length"],
            "success": log["success"],
            "error_message": log["error_message"],
        })

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"[prompt-logger] Exported {len(export_data)} prompts to {output_file}")
    return output_file


def get_statistics(pipeline_id: str, stage: str) -> dict[str, Any]:
    """獲取統計信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total_calls,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_calls,
            COUNT(DISTINCT system_hash) as unique_system_prompts,
            COUNT(DISTINCT user_hash) as unique_user_prompts,
            AVG(output_length) as avg_output_length,
            MIN(timestamp) as first_call,
            MAX(timestamp) as last_call
        FROM prompt_logs
        WHERE pipeline_id = ? AND stage = ?
    """, (pipeline_id, stage))

    row = cursor.fetchone()
    conn.close()

    total = row[0] or 0
    successful = row[1] or 0

    return {
        "total_calls": total,
        "successful_calls": successful,
        "success_rate": (successful / total) if total > 0 else 0,
        "unique_system_prompts": row[2] or 0,
        "unique_user_prompts": row[3] or 0,
        "avg_output_length": row[4] or 0,
        "first_call": row[5],
        "last_call": row[6],
    }


def clear_old_logs(days: int = 30) -> int:
    """清除 N 天前的日誌"""
    import time
    cutoff_timestamp = int((time.time() - days * 86400) * 1000)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM prompt_logs WHERE timestamp < ?", (cutoff_timestamp,))
    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted
