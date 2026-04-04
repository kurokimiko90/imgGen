"""
scripts/audit.py — Human-in-the-loop content review system.

Usage:
    python scripts/audit.py                        # Interactive review
    python scripts/audit.py --account A            # Filter by account
    python scripts/audit.py --batch                # Auto-approve batch mode
    python scripts/audit.py --export-md            # Export review.md
    python scripts/audit.py --import-md review.md  # Re-import from edited file
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import click

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import LevelUpConfig
from src.content import AccountType, Content, ContentStatus
from src.db import ContentDAO
from src.markdown_io import export_markdown, import_markdown
from src.preflight import preflight_check
from src.scheduler import calculate_scheduled_time

DEFAULT_DB_PATH = Path("~/.imggen/history.db").expanduser()
DEFAULT_CONFIG_PATH = Path("~/.imggen/accounts.toml").expanduser()

# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------


def _display_content(
    content: Content,
    index: int,
    total: int,
    account_config=None,
) -> None:
    """Print a single content card for review."""
    account_name = (
        account_config.name if account_config else content.account_type.value
    )
    sep_thick = "═" * 40
    sep_thin = "─" * 40

    click.echo(f"\n{sep_thick}")
    click.echo(
        f"[{index}/{total}]  帳號 {account_name} · "
        f"{content.content_type.value} · {content.id}"
    )
    click.echo(sep_thick)
    click.echo(f"標題：{content.title}")
    click.echo("")
    click.echo("內文：")
    click.echo(content.body)
    if content.reasoning:
        click.echo("")
        click.echo("Reasoning：")
        click.echo(content.reasoning)
    if content.image_path:
        click.echo(f"\n圖卡：{content.image_path}")
    click.echo(sep_thin)
    click.echo("(A) 核准  (E) 編輯並核准  (D) 捨棄  (S) 跳過  (Q) 離開")


# ---------------------------------------------------------------------------
# Editor integration
# ---------------------------------------------------------------------------


def _open_editor(body: str) -> str:
    """Open $EDITOR with *body*, returning the edited content."""
    editors = [
        os.environ.get("EDITOR"),
        os.environ.get("VISUAL"),
        "vim",
        "nano",
    ]
    editor = next((e for e in editors if e), None)
    if not editor:
        click.echo("無法找到可用的編輯器，跳過編輯。")
        return body

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(body)
        tmp_path = tmp.name

    try:
        subprocess.run([editor, tmp_path], check=True)
        return Path(tmp_path).read_text(encoding="utf-8")
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        click.echo(f"編輯器執行失敗：{exc}")
        return body
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Action handler
# ---------------------------------------------------------------------------


def _handle_action(
    action: str,
    content: Content,
    dao: ContentDAO,
    account_config=None,
) -> str:
    """Execute a review action and return a description string."""
    action = action.lower()

    if action == "a":
        platforms = account_config.platforms if account_config else []
        warnings = preflight_check(content, platforms)
        error_warnings = [w for w in warnings if w.startswith("[ERROR]")]
        if warnings:
            click.echo("\n⚠ Pre-flight 警告：")
            for w in warnings:
                click.echo(f"  {w}")
            if error_warnings:
                click.echo("有 ERROR 級警告，已跳過核准。")
                return "skipped (preflight error)"
            if not click.confirm("仍要核准？"):
                return "skipped"

        content.transition_to(ContentStatus.APPROVED)
        if account_config:
            try:
                content.scheduled_time = calculate_scheduled_time(
                    account_config.publish_time
                )
            except ValueError:
                pass
        dao.update(content)
        scheduled = (
            content.scheduled_time.strftime("%Y-%m-%d %H:%M")
            if content.scheduled_time
            else "未排程"
        )
        return f"approved (scheduled: {scheduled})"

    elif action == "e":
        new_body = _open_editor(content.body)
        content.body = new_body
        return _handle_action("a", content, dao, account_config)

    elif action == "d":
        content.transition_to(ContentStatus.REJECTED)
        dao.update(content)
        return "rejected"

    elif action == "s":
        return "skipped"

    return "unknown action"


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------


def _print_summary(summary: dict) -> None:
    click.echo("\n" + "═" * 40)
    click.echo("審核完成")
    click.echo("═" * 40)
    click.echo(f"  核准：{summary.get('approved', 0)}")
    click.echo(f"  捨棄：{summary.get('rejected', 0)}")
    click.echo(f"  跳過：{summary.get('skipped', 0)}")


# ---------------------------------------------------------------------------
# Interactive loop
# ---------------------------------------------------------------------------


def _run_interactive(
    contents: list[Content],
    dao: ContentDAO,
    config,
) -> dict:
    """Run the interactive review loop. Returns summary dict."""
    summary = {"approved": 0, "rejected": 0, "skipped": 0}
    total = len(contents)

    for i, content in enumerate(contents, start=1):
        account_config = None
        try:
            account_config = config.get_account(content.account_type.value)
        except (ValueError, FileNotFoundError):
            pass

        _display_content(content, i, total, account_config)

        while True:
            raw = click.prompt("", prompt_suffix="> ").strip().lower()
            if raw in ("a", "e", "d", "s", "q"):
                break
            click.echo("請輸入 a / e / d / s / q")

        if raw == "q":
            click.echo("離開審核。")
            break

        result = _handle_action(raw, content, dao, account_config)
        click.echo(f"→ {result}")

        if "approved" in result:
            summary["approved"] += 1
        elif "rejected" in result:
            summary["rejected"] += 1
        else:
            summary["skipped"] += 1

    _print_summary(summary)
    return summary


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


@click.command()
@click.option("--account", default=None, help="只審核指定帳號（A / B / C）")
@click.option("--batch", is_flag=True, help="批次自動核准模式")
@click.option("--export-md", "export_md", is_flag=True, help="匯出 review.md")
@click.option(
    "--import-md",
    "import_md",
    default=None,
    type=click.Path(exists=True),
    help="從 Markdown 檔案回寫 DB",
)
@click.option("--db-path", default=str(DEFAULT_DB_PATH), help="DB 路徑")
@click.option("--config-path", default=str(DEFAULT_CONFIG_PATH), help="帳號設定路徑")
def audit(account, batch, export_md, import_md, db_path, config_path):
    """HITL 內容審核系統"""
    dao = ContentDAO(db_path)

    try:
        config = LevelUpConfig(config_path)
    except FileNotFoundError:
        click.echo(f"⚠ 找不到帳號設定：{config_path}，將以無設定模式執行")
        config = None

    # --import-md: re-import from edited Markdown file
    if import_md:
        summary = import_markdown(Path(import_md), dao, config)
        click.echo(
            f"匯入完成 — 核准:{summary['approved']} "
            f"捨棄:{summary['rejected']} "
            f"跳過:{summary['skipped']} "
            f"錯誤:{len(summary['errors'])}"
        )
        for err in summary["errors"]:
            click.echo(f"  [ERROR] {err}")
        return

    # Load PENDING_REVIEW content
    account_filter = AccountType(account).value if account else None
    contents = dao.find_by_status(ContentStatus.PENDING_REVIEW, account_filter)

    if not contents:
        click.echo("目前沒有待審核的內容。")
        return

    # --export-md: dump to file and exit
    if export_md:
        out = Path("review.md")
        export_markdown(contents, out)
        click.echo(f"已匯出 {len(contents)} 篇內容至 {out}")
        return

    # --batch: auto-approve without preflight errors
    if batch:
        summary = {"approved": 0, "rejected": 0, "skipped": 0}
        for content in contents:
            account_config = None
            if config:
                try:
                    account_config = config.get_account(content.account_type.value)
                except (ValueError, FileNotFoundError):
                    pass

            platforms = account_config.platforms if account_config else []
            warnings = preflight_check(content, platforms)
            errors = [w for w in warnings if w.startswith("[ERROR]")]
            if errors:
                summary["skipped"] += 1
                continue

            content.transition_to(ContentStatus.APPROVED)
            if account_config:
                try:
                    content.scheduled_time = calculate_scheduled_time(
                        account_config.publish_time
                    )
                except ValueError:
                    pass
            dao.update(content)
            summary["approved"] += 1

        _print_summary(summary)
        return

    # Default: interactive review
    if config is None:
        # Create a stub config for interactive mode
        class _StubConfig:
            def get_account(self, _):
                raise ValueError("no config")

        config = _StubConfig()

    _run_interactive(contents, dao, config)


if __name__ == "__main__":
    audit()
