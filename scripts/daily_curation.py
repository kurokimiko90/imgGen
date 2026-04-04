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
from src.pipeline import PipelineOptions, run_pipeline
from src.scrapers.base_scraper import RawItem
from src.scrapers.football_scraper import FootballScraper
from src.scrapers.pmp_scraper import PMPScraper
from src.scrapers.tech_scraper import TechScraper

DEFAULT_DB_PATH = Path("~/.imggen/history.db").expanduser()
DEFAULT_CONFIG_PATH = Path("~/.imggen/accounts.toml").expanduser()
OUTPUT_DIR = PROJECT_ROOT / "output"

# Account → scraper mapping
SCRAPERS: dict[str, type] = {
    "A": TechScraper,
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


def generate_image(body: str, theme: str, account_type: str) -> str | None:
    """Generate an image card using the imgGen pipeline.

    Returns the image path string, or None on failure.
    """
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / f"draft_{account_type}_{timestamp}.png"

        options = PipelineOptions(
            theme=theme,
            format="story",
            provider="cli",  # Use Claude Code CLI by default (no API key needed)
            mode="smart",
            color_mood=theme,
        )
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

    drafted = 0
    for item in raw_items[:5]:  # cap at 5 items per account per run
        try:
            _emit("item_fetched", title=item.title, source=item.source)
            ai_output = call_claude_api(account_config.prompt_file, item)

            if not ai_output.get("should_publish"):
                reason = ai_output.get("reasoning", "")
                print(f"[{account_type}] Skip: {item.title[:50]} — {reason[:60]}")
                _emit("item_skipped", title=item.title, reason=reason)
                continue

            image_path = None
            if not dry_run:
                _emit("generating_image", title=ai_output.get("title", item.title))
                image_path = generate_image(
                    ai_output["body"],
                    account_config.color_mood,
                    account_type,
                )

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
@click.option("--db-path", default=str(DEFAULT_DB_PATH), help="DB 路徑")
@click.option("--config-path", default=str(DEFAULT_CONFIG_PATH), help="帳號設定路徑")
def main(account, dry_run, db_path, config_path):
    """Daily content curation — fetch, AI-curate, and save DRAFTs."""
    config = LevelUpConfig(config_path)
    dao = ContentDAO(db_path)

    accounts_to_run = [account] if account else list(SCRAPERS.keys())

    async def _run():
        tasks = []
        for acct in accounts_to_run:
            scraper = SCRAPERS[acct]()
            tasks.append(
                curate_for_account(acct, scraper, config, dao, dry_run=dry_run)
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
