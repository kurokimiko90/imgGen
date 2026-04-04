"""
src/markdown_io.py - Markdown export/import for content review workflow.

Allows reviewers to audit content in a text editor (e.g. on mobile),
then import their APPROVE/REJECT decisions back into the database.
"""

import re
from datetime import date
from pathlib import Path
from typing import Optional

from src.content import Content, ContentStatus
from src.db import ContentDAO
from src.scheduler import calculate_scheduled_time


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def export_markdown(
    contents: list[Content],
    output_path: Path,
    account_configs: Optional[dict] = None,
) -> Path:
    """Write a Markdown review file for *contents*.

    Each content block includes title, body, reasoning, image path, and
    an ``Action`` field defaulting to ``SKIP``.

    Returns the path to the written file.
    """
    lines: list[str] = [
        f"# Content Review - {date.today().isoformat()}",
        "",
    ]

    for content in contents:
        account_name = content.account_type.value
        if account_configs and content.account_type.value in account_configs:
            account_name = account_configs[content.account_type.value].name

        created_date = (
            content.created_at.strftime("%Y-%m-%d")
            if hasattr(content, "created_at") and content.created_at
            else "未知日期"
        )

        lines.append("---")
        lines.append("")
        lines.append(
            f"## [{content.status.value}] ID:{content.id} · "
            f"{account_name} · {created_date} · {content.content_type.value}"
        )
        lines.append(f"**標題**: {content.title}")
        lines.append("**內文**:")
        lines.append(content.body)
        lines.append("")
        if content.reasoning:
            lines.append(f"**Reasoning**: {content.reasoning}")
        if content.image_path:
            lines.append(f"**圖卡**: {content.image_path}")
        lines.append("**Action**: SKIP  <!-- 改成 APPROVE / REJECT / SKIP -->")
        lines.append("")

    lines.append("---")
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------


def parse_markdown(file_path: Path) -> list[dict]:
    """Parse a review Markdown file and return a list of action dicts.

    Each dict contains:
      - ``id``: content id (str)
      - ``action``: ``APPROVE``, ``REJECT``, or ``SKIP``
      - ``body``: updated body text (str, may equal original)
    """
    text = file_path.read_text(encoding="utf-8")
    blocks = re.split(r"\n---\n", text)

    results: list[dict] = []
    for block in blocks:
        # Must contain an ID
        id_match = re.search(r"ID:(\S+)", block)
        if not id_match:
            continue

        content_id = id_match.group(1)

        action_match = re.search(
            r"\*\*Action\*\*:\s*(APPROVE|REJECT|SKIP)", block
        )
        action = action_match.group(1) if action_match else "SKIP"

        # Extract body (text between "**內文**:" and next "**..." line or blank + **)
        body_match = re.search(
            r"\*\*內文\*\*:\s*\n(.*?)(?=\n\*\*|\Z)", block, re.DOTALL
        )
        body = body_match.group(1).strip() if body_match else ""

        results.append({"id": content_id, "action": action, "body": body})

    return results


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------


def import_markdown(
    file_path: Path,
    dao: ContentDAO,
    config,
) -> dict:
    """Read a review Markdown file and apply decisions to the database.

    Returns a summary dict:
      ``{"approved": int, "rejected": int, "skipped": int, "errors": list[str]}``
    """
    parsed = parse_markdown(file_path)
    summary = {"approved": 0, "rejected": 0, "skipped": 0, "errors": []}

    for item in parsed:
        content_id = item["id"]
        action = item["action"]
        body = item["body"]

        if action == "SKIP":
            summary["skipped"] += 1
            continue

        content = dao.find_by_id(content_id)
        if content is None:
            summary["errors"].append(f"ID {content_id} 不存在")
            continue

        try:
            if action == "APPROVE":
                if body:
                    content.body = body
                content.transition_to(ContentStatus.APPROVED)

                # Assign scheduled_time from account config
                try:
                    account_cfg = config.get_account(content.account_type.value)
                    content.scheduled_time = calculate_scheduled_time(
                        account_cfg.publish_time
                    )
                except (ValueError, FileNotFoundError):
                    pass  # scheduled_time remains None if config missing

                dao.update(content)
                summary["approved"] += 1

            elif action == "REJECT":
                content.transition_to(ContentStatus.REJECTED)
                dao.update(content)
                summary["rejected"] += 1

        except Exception as exc:
            summary["errors"].append(f"ID {content_id} 處理失敗：{exc}")

    return summary
