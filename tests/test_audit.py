"""tests/test_audit.py — Integration tests for scripts/audit.py"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from scripts.audit import _handle_action, _run_interactive, audit
from src.content import AccountType, Content, ContentStatus


def make_content(
    id_="1",
    status=ContentStatus.PENDING_REVIEW,
    body="短內文",
    image_path=None,
) -> Content:
    return Content(
        id=id_,
        account_type=AccountType.A,
        status=status,
        title="測試標題",
        body=body,
        reasoning="Reasoning 文字",
        image_path=image_path,
    )


def make_account_config(platforms=None, publish_time="09:00"):
    cfg = MagicMock()
    cfg.name = "帳號 A"
    cfg.platforms = platforms or ["x"]
    cfg.publish_time = publish_time
    return cfg


# ---------------------------------------------------------------------------
# _handle_action tests
# ---------------------------------------------------------------------------


def test_approve_sets_status_approved():
    content = make_content()
    dao = MagicMock()
    account_cfg = make_account_config()
    _handle_action("a", content, dao, account_cfg)
    assert content.status == ContentStatus.APPROVED
    dao.update.assert_called_once_with(content)


def test_approve_sets_scheduled_time():
    content = make_content()
    dao = MagicMock()
    account_cfg = make_account_config(publish_time="09:00")
    _handle_action("a", content, dao, account_cfg)
    assert content.scheduled_time is not None


def test_reject_sets_status_rejected():
    content = make_content()
    dao = MagicMock()
    _handle_action("d", content, dao)
    assert content.status == ContentStatus.REJECTED
    dao.update.assert_called_once_with(content)


def test_skip_preserves_status():
    content = make_content()
    dao = MagicMock()
    result = _handle_action("s", content, dao)
    assert content.status == ContentStatus.PENDING_REVIEW
    dao.update.assert_not_called()
    assert "skipped" in result


def test_approve_with_preflight_warnings_shows_warnings():
    # Image required for instagram but not provided → ERROR warning
    content = make_content(image_path=None)
    dao = MagicMock()
    account_cfg = make_account_config(platforms=["instagram"])

    result = _handle_action("a", content, dao, account_cfg)
    assert "skipped" in result
    dao.update.assert_not_called()


def test_edit_updates_body():
    content = make_content()
    dao = MagicMock()
    account_cfg = make_account_config()

    new_body = "修改後的內文"
    with patch("scripts.audit._open_editor", return_value=new_body):
        _handle_action("e", content, dao, account_cfg)

    assert content.body == new_body
    assert content.status == ContentStatus.APPROVED


# ---------------------------------------------------------------------------
# Batch mode
# ---------------------------------------------------------------------------


def test_batch_mode_processes_all_drafts(tmp_path):
    db_path = str(tmp_path / "test.db")
    config_path = str(tmp_path / "accounts.toml")

    dao = MagicMock()
    contents = [make_content("1"), make_content("2"), make_content("3")]
    dao.find_by_status.return_value = contents

    account_cfg = make_account_config(platforms=["x"])
    config = MagicMock()
    config.get_account.return_value = account_cfg

    runner = CliRunner()
    with (
        patch("scripts.audit.ContentDAO", return_value=dao),
        patch("scripts.audit.LevelUpConfig", return_value=config),
    ):
        result = runner.invoke(audit, ["--batch", "--db-path", db_path, "--config-path", config_path])

    assert result.exit_code == 0
    assert dao.update.call_count == 3


def test_batch_mode_skips_preflight_errors(tmp_path):
    db_path = str(tmp_path / "test.db")
    config_path = str(tmp_path / "accounts.toml")

    # Content missing image for instagram → ERROR → skip
    content_err = make_content("1", image_path=None)
    content_ok = make_content("2")

    dao = MagicMock()
    dao.find_by_status.return_value = [content_err, content_ok]

    account_cfg_ig = make_account_config(platforms=["instagram"])
    account_cfg_x = make_account_config(platforms=["x"])
    config = MagicMock()
    # First content (err) → instagram, second (ok) → x
    config.get_account.side_effect = [account_cfg_ig, account_cfg_x]

    runner = CliRunner()
    with (
        patch("scripts.audit.ContentDAO", return_value=dao),
        patch("scripts.audit.LevelUpConfig", return_value=config),
    ):
        result = runner.invoke(audit, ["--batch", "--db-path", db_path, "--config-path", config_path])

    assert result.exit_code == 0
    # Only content_ok should be approved (content_err skipped due to ERROR)
    assert dao.update.call_count == 1


# ---------------------------------------------------------------------------
# _run_interactive
# ---------------------------------------------------------------------------


def test_run_interactive_returns_summary():
    contents = [make_content("1"), make_content("2")]
    dao = MagicMock()
    config = MagicMock()
    config.get_account.return_value = make_account_config()

    # Simulate: approve first, skip second
    with patch("click.prompt", side_effect=["a", "s"]):
        summary = _run_interactive(contents, dao, config)

    assert summary["approved"] == 1
    assert summary["skipped"] == 1
    assert summary["rejected"] == 0
