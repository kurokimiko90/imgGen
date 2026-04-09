"""
scripts/daily_curation.py — Daily content curation pipeline.

Fetches raw items from each account's scraper, uses Claude to evaluate
and draft posts, generates image cards via imgGen pipeline, and saves
DRAFT content to the database.

Usage:
    python scripts/daily_curation.py
    python scripts/daily_curation.py --account A   # Single account
    python scripts/daily_curation.py --dry-run     # Print drafts without saving
"""

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import click

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import LevelUpConfig
from src.content import AccountType, Content, ContentStatus, ContentType
from src.db import ContentDAO
from src.pipeline import PipelineOptions, run_pipeline, run_carousel_pipeline
from src.scrapers.base_scraper import RawItem
from src.scrapers.ai_scraper import AIScraper
from src.scrapers.football_scraper import FootballScraper
from src.scrapers.pmp_scraper import PMPScraper
from src.scrapers.tech_scraper import TechScraper

DEFAULT_DB_PATH = Path("~/.imggen/history.db").expanduser()
DEFAULT_CONFIG_PATH = Path("~/.imggen/accounts.toml").expanduser()
OUTPUT_DIR = PROJECT_ROOT / "output"

# Account → scraper mapping
SCRAPERS: dict[str, type] = {
    "A": AIScraper,
    "B": PMPScraper,
    "C": FootballScraper,
}


# ---------------------------------------------------------------------------
# AI curation
# ---------------------------------------------------------------------------


def _load_prompt(prompt_file: str, item: RawItem) -> str:
    """Load account prompt template and inject the news item."""
    prompt_path = PROJECT_ROOT / prompt_file
    template = prompt_path.read_text(encoding="utf-8")
    return (
        template
        .replace("{title}", item.title)
        .replace("{url}", item.url)
        .replace("{summary}", item.summary or "")
        .replace("{source}", item.source)
    )


def call_claude_api(prompt_file: str, item: RawItem, provider: str = "cli") -> dict:
    """Call Claude to curate content and return parsed JSON decision.

    Args:
        prompt_file: Path to account-specific prompt template
        item: RawItem from scraper
        provider: "cli" (default, no API key needed) or "claude" (requires ANTHROPIC_API_KEY)

    Returns:
        Dict with keys: should_publish, title, body, content_type, reasoning

    Raises:
        ValueError: If the response cannot be parsed as valid JSON with required fields.
        RuntimeError: If claude CLI is not found (when provider="cli")
    """
    prompt = _load_prompt(prompt_file, item)
    raw = _call_claude(prompt, provider=provider)

    # Extract JSON from response (may have surrounding text)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in response: {raw[:200]}")

    data = json.loads(match.group())
    if "should_publish" not in data:
        raise ValueError("Missing 'should_publish' in AI response")
    if data.get("should_publish") and not data.get("reasoning", "").strip():
        raise ValueError("reasoning field is empty but should_publish=true")

    return data


def call_claude_api_batch(
    prompt_file: str, items: list[RawItem], provider: str = "cli"
) -> list[dict]:
    """Call Claude to curate multiple items in a single batch request.

    Builds a single prompt with all items in JSON format, requests JSON array response,
    and maps results back to items by index.

    Args:
        prompt_file: Path to account-specific prompt template
        items: List of RawItems to evaluate
        provider: "cli" (default) or "claude"

    Returns:
        List of dicts (parallel to items), each with keys:
        should_publish, title, body, content_type, reasoning

    If parsing fails, falls back to per-item calls.
    """
    if not items:
        return []

    # Load base template
    prompt_path = PROJECT_ROOT / prompt_file
    template = prompt_path.read_text(encoding="utf-8")

    # Serialize items to JSON to prevent prompt injection
    items_data = [
        {
            "index": idx,
            "title": item.title,
            "url": item.url,
            "summary": item.summary or "",
            "source": item.source,
        }
        for idx, item in enumerate(items, 1)
    ]

    batch_prompt = (
        template
        + "\n\n--- ITEMS TO EVALUATE (JSON) ---\n"
        + json.dumps(items_data, ensure_ascii=False, indent=2)
        + "\n\nReturn a JSON array of decisions (in the same order as items above, indexed by item index). "
        + "Each object must have: should_publish, title, body, content_type, reasoning."
    )

    try:
        raw = _call_claude(batch_prompt, provider=provider)

        # Extract JSON array from response
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON array found in response: {raw[:200]}")

        results = json.loads(match.group())
        if not isinstance(results, list):
            raise ValueError("Batch response is not a JSON array")

        # Validate and normalize each result
        output = []
        for idx, result in enumerate(results):
            if not isinstance(result, dict):
                raise ValueError(f"Item {idx} is not a dict: {result}")
            if "should_publish" not in result:
                raise ValueError(f"Item {idx} missing 'should_publish'")
            if result.get("should_publish") and not result.get("reasoning", "").strip():
                raise ValueError(f"Item {idx}: reasoning is empty but should_publish=true")
            output.append(result)

        if len(output) != len(items):
            raise ValueError(
                f"Batch response has {len(output)} items, expected {len(items)}"
            )

        return output

    except (ValueError, json.JSONDecodeError) as exc:
        # Fallback to per-item calls on parse error
        print(f"[batch] Parse failed: {exc}. Falling back to per-item calls...")
        return [call_claude_api(prompt_file, item, provider=provider) for item in items]


def _call_claude(prompt: str, provider: str = "cli", model: str = "haiku") -> str:
    """Call Claude via CLI or API and return raw text response.

    Args:
        prompt: Full prompt for Claude
        provider: "cli" (default) or "claude"
        model: Model variant — "haiku" or "sonnet"

    Returns:
        Raw text response from Claude

    Raises:
        RuntimeError: If CLI not found or execution fails
        ValueError: If provider is unknown
    """
    if provider == "cli":
        # Use Claude Code CLI — no API key needed
        claude_cli = shutil.which("claude")
        if not claude_cli:
            raise RuntimeError(
                "claude CLI not found. Install via: https://claude.ai/code"
            )

        # Filter env to avoid interfering with claude CLI's auth
        env = {
            k: v for k, v in os.environ.items()
            if k not in {"CLAUDECODE", "ANTHROPIC_API_KEY"}
        }

        result = subprocess.run(
            [claude_cli, "-p", "--output-format", "text", "--model", model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )

        if result.returncode != 0:
            raise RuntimeError(f"claude CLI failed: {result.stderr.strip()}")

        return result.stdout.strip()

    elif provider == "claude":
        # Use Anthropic API — requires ANTHROPIC_API_KEY env var
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your_anthropic_key_here":
            raise ValueError(
                "ANTHROPIC_API_KEY env var not set or is placeholder. "
                "Use provider='cli' instead to avoid needing an API key."
            )

        client = anthropic.Anthropic(api_key=api_key)

        # Map haiku/sonnet to full model IDs
        model_map = {
            "haiku": "claude-haiku-4-5-20251001",
            "sonnet": "claude-sonnet-4-6",
        }
        full_model = model_map.get(model, "claude-haiku-4-5-20251001")

        message = client.messages.create(
            model=full_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text

    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'cli' or 'claude'.")


def generate_image(
    body: str,
    theme: str,
    account_type: str,
    carousel: bool = False,
    num_slides: int = 5,
) -> str | None:
    """Generate image card(s) using the imgGen pipeline.

    Args:
        body: Article body text.
        theme: Color theme/mood.
        account_type: Account identifier (A/B/C).
        carousel: If True, generate multi-slide carousel.
        num_slides: Number of carousel slides (3-7).

    Returns:
        Image path (single) or comma-separated paths (carousel), or None on failure.
    """
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        options = PipelineOptions(
            theme=theme,
            format="story",
            provider="cli",
            mode="smart",
            color_mood=theme,
        )

        if carousel:
            carousel_dir = OUTPUT_DIR / f"carousel_{account_type}_{timestamp}"
            _, paths = run_carousel_pipeline(body, options, carousel_dir, num_slides=num_slides)
            return ",".join(str(p) for p in paths)
        else:
            output_path = OUTPUT_DIR / f"draft_{account_type}_{timestamp}.png"
            _, img_path = run_pipeline(body, options, output_path)
            return str(img_path)
    except Exception as exc:
        print(f"[daily_curation] Image generation failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Per-account curation
# ---------------------------------------------------------------------------


async def curate_for_account(
    account_type: str,
    scraper,
    levelup_config: LevelUpConfig,
    dao: ContentDAO,
    dry_run: bool = False,
    skip_image: bool = False,
    carousel: bool = False,
    num_slides: int = 5,
    progress_callback=None,  # callback(type: str, **kwargs) for SSE streaming
) -> int:
    """Run the full curation pipeline for one account.

    Returns the number of DRAFT items created.
    Args:
        progress_callback: Optional callable(type, **kwargs). Called at each
                           pipeline stage for real-time SSE streaming.
                           Event types: item_fetched, generating_image,
                           saved_draft, item_skipped, item_error.
    """
    def _emit(event_type: str, **kwargs):
        if progress_callback:
            progress_callback(event_type, account=account_type, **kwargs)

    account_config = levelup_config.get_account(account_type)
    raw_items = scraper.fetch()

    if not raw_items:
        print(f"[{account_type}] No items fetched.")
        return 0

    # Deduplicate by source URL: skip items already in DB (unless REJECTED)
    # Use up to 10 items per account to support multiple sources (BBC, Japan players, etc)
    items_to_process = []
    for item in raw_items[:10]:
        existing = dao.find_by_source_url(item.url)
        if existing:
            print(f"[{account_type}] Skip duplicate: {item.title[:50]} (existing id={existing.id})")
            _emit("item_skipped", title=item.title, reason="Duplicate URL in DB")
            continue
        items_to_process.append(item)

    if not items_to_process:
        print(f"[{account_type}] All items already processed.")
        return 0

    # Batch AI evaluation: single call for all items
    # If batch fails, fall back to per-item calls
    try:
        ai_outputs = call_claude_api_batch(account_config.prompt_file, items_to_process)
    except Exception as exc:
        print(f"[{account_type}] Batch evaluation failed ({exc}), falling back to per-item...")
        ai_outputs = [
            call_claude_api(account_config.prompt_file, item)
            for item in items_to_process
        ]

    # Filter to publishable items only, then generate images in parallel
    publishable = [
        (item, ai_output)
        for item, ai_output in zip(items_to_process, ai_outputs)
        if ai_output.get("should_publish")
    ]
    for item, ai_output in zip(items_to_process, ai_outputs):
        if not ai_output.get("should_publish"):
            reason = ai_output.get("reasoning", "")
            print(f"[{account_type}] Skip: {item.title[:50]} — {reason[:60]}")
            _emit("item_skipped", title=item.title, reason=reason)

    # Parallel image generation for all publishable items
    image_paths: dict[int, str | None] = {}
    if not dry_run and not skip_image and publishable:
        import concurrent.futures

        def _gen(idx_item_output):
            idx, (item, ai_output) = idx_item_output
            _emit("generating_image", title=ai_output.get("title", item.title))
            return idx, generate_image(
                ai_output["body"],
                account_config.color_mood,
                account_type,
                carousel=carousel,
                num_slides=num_slides,
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(publishable)) as executor:
            for idx, path in executor.map(_gen, enumerate(publishable)):
                image_paths[idx] = path

    drafted = 0
    for idx, (item, ai_output) in enumerate(publishable):
        try:
            _emit("item_fetched", title=item.title, source=item.source)
            image_path = image_paths.get(idx) if not dry_run and not skip_image else None

            content = Content(
                id="0",  # DAO will assign real id
                account_type=AccountType(account_type),
                status=ContentStatus.DRAFT,
                content_type=ContentType(ai_output.get("content_type", "NEWS_RECAP")),
                title=ai_output.get("title", item.title[:15]),
                body=ai_output["body"],
                image_path=image_path,
                output_path=image_path or "",
                reasoning=ai_output["reasoning"],
                theme=account_config.color_mood,
                format="story",
                provider="cli",
                source_url=item.url,
                source=item.source,
            )

            if dry_run:
                print(f"[{account_type}] DRY-RUN draft: {content.title}")
                print(f"  body: {content.body[:80]}...")
                print(f"  reasoning: {content.reasoning[:80]}...")
            else:
                dao.create(content)
                print(f"[{account_type}] Created draft: {content.title}")
                _emit("saved_draft", title=content.title)

            drafted += 1

        except Exception as exc:
            print(f"[{account_type}] Error for '{item.title[:50]}': {exc}")
            _emit("item_error", title=item.title, error=str(exc))

    return drafted


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


@click.command()
@click.option("--account", default=None, type=click.Choice(["A", "B", "C"]), help="只執行指定帳號")
@click.option("--dry-run", is_flag=True, help="列印草稿但不寫入 DB 或產生圖片")
@click.option("--no-image", is_flag=True, help="跳過圖片生成（僅評估內容）")
@click.option("--carousel", is_flag=True, help="生成輪播圖（5 張 slides）")
@click.option("--slides", default=5, type=click.IntRange(3, 7), help="輪播圖張數（3-7）")
@click.option("--db-path", default=str(DEFAULT_DB_PATH), help="DB 路徑")
@click.option("--config-path", default=str(DEFAULT_CONFIG_PATH), help="帳號設定路徑")
def main(account, dry_run, no_image, carousel, slides, db_path, config_path):
    """Daily content curation — fetch, AI-curate, and save DRAFTs."""
    config = LevelUpConfig(config_path)
    dao = ContentDAO(db_path)

    accounts_to_run = [account] if account else list(SCRAPERS.keys())

    async def _run():
        tasks = []
        for acct in accounts_to_run:
            scraper = SCRAPERS[acct]()
            tasks.append(
                curate_for_account(
                    acct, scraper, config, dao,
                    dry_run=dry_run, skip_image=no_image,
                    carousel=carousel, num_slides=slides,
                )
            )
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total = 0
        for acct, result in zip(accounts_to_run, results):
            if isinstance(result, Exception):
                print(f"[{acct}] FAILED: {result}")
            else:
                total += result

        label = "(dry-run) " if dry_run else ""
        print(f"\nDaily curation {label}complete: {total} new DRAFTs created")

    asyncio.run(_run())


if __name__ == "__main__":
    main()
