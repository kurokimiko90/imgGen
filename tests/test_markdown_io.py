"""tests/test_markdown_io.py — Tests for src/markdown_io.py"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.content import AccountType, Content, ContentStatus
from src.markdown_io import export_markdown, import_markdown, parse_markdown


def make_content(id_="1", status=ContentStatus.PENDING_REVIEW, body="內文內容") -> Content:
    return Content(
        id=id_,
        account_type=AccountType.A,
        status=status,
        title="測試標題",
        body=body,
        reasoning="這是 reasoning",
        image_path=None,
    )


# ---------------------------------------------------------------------------
# export_markdown
# ---------------------------------------------------------------------------


def test_export_md_writes_all_pending(tmp_path):
    contents = [make_content("1"), make_content("2")]
    out = tmp_path / "review.md"
    export_markdown(contents, out)
    text = out.read_text()
    assert "ID:1" in text
    assert "ID:2" in text


def test_export_md_format_correct(tmp_path):
    content = make_content("42")
    out = tmp_path / "review.md"
    export_markdown([content], out)
    text = out.read_text()
    assert "**標題**: 測試標題" in text
    assert "**內文**:" in text
    assert "**Action**: SKIP" in text


def test_export_md_default_action_is_skip(tmp_path):
    out = tmp_path / "review.md"
    export_markdown([make_content("1")], out)
    text = out.read_text()
    assert "**Action**: SKIP" in text
    # The first word after "**: " on the Action line should be SKIP
    import re
    action_match = re.search(r"\*\*Action\*\*:\s*(\S+)", text)
    assert action_match and action_match.group(1) == "SKIP"


# ---------------------------------------------------------------------------
# parse_markdown
# ---------------------------------------------------------------------------


SAMPLE_MD = """\
# Content Review - 2026-04-01

---

## [PENDING_REVIEW] ID:10 · 帳號A · 2026-04-01 · NEWS_RECAP
**標題**: 標題一
**內文**:
原始內文

**Action**: APPROVE  <!-- 改成 APPROVE / REJECT / SKIP -->

---

## [PENDING_REVIEW] ID:20 · 帳號A · 2026-04-01 · NEWS_RECAP
**標題**: 標題二
**內文**:
另一段內文

**Action**: REJECT  <!-- 改成 APPROVE / REJECT / SKIP -->

---

## [PENDING_REVIEW] ID:30 · 帳號A · 2026-04-01 · NEWS_RECAP
**標題**: 標題三
**內文**:
跳過的內文

**Action**: SKIP  <!-- 改成 APPROVE / REJECT / SKIP -->

---
"""

MODIFIED_BODY_MD = """\
# Content Review - 2026-04-01

---

## [PENDING_REVIEW] ID:99 · 帳號A · 2026-04-01 · NEWS_RECAP
**標題**: 標題
**內文**:
修改後的內文，更加精彩

**Action**: APPROVE  <!-- 改成 APPROVE / REJECT / SKIP -->

---
"""


def test_parse_md_approve(tmp_path):
    f = tmp_path / "review.md"
    f.write_text(SAMPLE_MD)
    parsed = parse_markdown(f)
    approve_items = [p for p in parsed if p["id"] == "10"]
    assert len(approve_items) == 1
    assert approve_items[0]["action"] == "APPROVE"


def test_parse_md_reject(tmp_path):
    f = tmp_path / "review.md"
    f.write_text(SAMPLE_MD)
    parsed = parse_markdown(f)
    reject_items = [p for p in parsed if p["id"] == "20"]
    assert reject_items[0]["action"] == "REJECT"


def test_parse_md_skip(tmp_path):
    f = tmp_path / "review.md"
    f.write_text(SAMPLE_MD)
    parsed = parse_markdown(f)
    skip_items = [p for p in parsed if p["id"] == "30"]
    assert skip_items[0]["action"] == "SKIP"


def test_parse_md_modified_body(tmp_path):
    f = tmp_path / "review.md"
    f.write_text(MODIFIED_BODY_MD)
    parsed = parse_markdown(f)
    assert parsed[0]["body"] == "修改後的內文，更加精彩"


def test_parse_md_unmodified_body(tmp_path):
    f = tmp_path / "review.md"
    f.write_text(SAMPLE_MD)
    parsed = parse_markdown(f)
    item = next(p for p in parsed if p["id"] == "10")
    assert item["body"] == "原始內文"


# ---------------------------------------------------------------------------
# import_markdown
# ---------------------------------------------------------------------------


def test_import_md_updates_db_correctly(tmp_path):
    f = tmp_path / "review.md"
    f.write_text(SAMPLE_MD)

    content_approve = make_content("10")
    content_reject = make_content("20")

    dao = MagicMock()
    dao.find_by_id.side_effect = lambda cid: {
        "10": content_approve,
        "20": content_reject,
        "30": make_content("30"),
    }.get(cid)

    config = MagicMock()
    config.get_account.return_value = MagicMock(publish_time="09:00")

    result = import_markdown(f, dao, config)
    assert result["approved"] == 1
    assert result["rejected"] == 1
    assert result["skipped"] == 1


def test_import_md_returns_summary(tmp_path):
    f = tmp_path / "review.md"
    f.write_text(SAMPLE_MD)

    content_approve = make_content("10")
    content_reject = make_content("20")

    dao = MagicMock()
    dao.find_by_id.side_effect = lambda cid: {
        "10": content_approve,
        "20": content_reject,
        "30": make_content("30"),
    }.get(cid)
    config = MagicMock()
    config.get_account.return_value = MagicMock(publish_time="09:00")

    summary = import_markdown(f, dao, config)
    assert "approved" in summary
    assert "rejected" in summary
    assert "skipped" in summary
    assert "errors" in summary


def test_import_md_invalid_id_reports_error(tmp_path):
    md = """\
# Content Review - 2026-04-01

---

## [PENDING_REVIEW] ID:999 · 帳號A · 2026-04-01 · NEWS_RECAP
**標題**: X
**內文**:
body

**Action**: APPROVE

---
"""
    f = tmp_path / "review.md"
    f.write_text(md)

    dao = MagicMock()
    dao.find_by_id.return_value = None  # ID 999 not found

    config = MagicMock()
    summary = import_markdown(f, dao, config)
    assert summary["approved"] == 0
    assert len(summary["errors"]) == 1
    assert "999" in summary["errors"][0]
