"""tests/test_daily_curation.py — Tests for scripts/daily_curation.py."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.scrapers.base_scraper import RawItem


def make_raw_item(title="AI News", url="http://example.com"):
    return RawItem(
        title=title,
        url=url,
        summary="Summary",
        published_at=datetime.now(timezone.utc),
        source="hacker_news",
    )


def make_ai_output(should_publish=True):
    return {
        "should_publish": should_publish,
        "title": "AI新工具上線",
        "body": "Claude 4.5 正式推出原生工具呼叫，工程師們的 PTSD 又要觸發了。",
        "content_type": "NEWS_RECAP",
        "reasoning": "這則新聞對 AI 帳號受眾直接相關，預期互動率高，工程師社群會大量轉發分享。",
        "tags": ["#AI", "#Claude"],
        "image_suggestion": "dark_tech",
    }


def make_account_config(prompt_file="prompts/account_a.txt", color_mood="dark_tech"):
    cfg = MagicMock()
    cfg.prompt_file = prompt_file
    cfg.color_mood = color_mood
    cfg.publish_time = "12:30"
    return cfg


# ---------------------------------------------------------------------------
# curate_for_account tests
# ---------------------------------------------------------------------------


class TestCurateForAccount:
    @pytest.mark.asyncio
    async def test_curate_creates_draft_content(self, tmp_path):
        from scripts.daily_curation import curate_for_account

        scraper = MagicMock()
        scraper.fetch.return_value = [make_raw_item()]

        config = MagicMock()
        config.get_account.return_value = make_account_config()

        dao = MagicMock()

        with (
            patch("scripts.daily_curation.call_claude_api", return_value=make_ai_output()),
            patch("scripts.daily_curation.generate_image", return_value=str(tmp_path / "img.png")),
        ):
            count = await curate_for_account("A", scraper, config, dao)

        assert count == 1
        dao.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_skip_when_should_publish_false(self):
        from scripts.daily_curation import curate_for_account

        scraper = MagicMock()
        scraper.fetch.return_value = [make_raw_item()]

        config = MagicMock()
        config.get_account.return_value = make_account_config()

        dao = MagicMock()

        with patch("scripts.daily_curation.call_claude_api", return_value=make_ai_output(should_publish=False)):
            count = await curate_for_account("A", scraper, config, dao)

        assert count == 0
        dao.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_item_error_does_not_block_others(self, tmp_path):
        from scripts.daily_curation import curate_for_account

        scraper = MagicMock()
        scraper.fetch.return_value = [make_raw_item("Bad"), make_raw_item("Good")]

        config = MagicMock()
        config.get_account.return_value = make_account_config()

        dao = MagicMock()

        def ai_side_effect(prompt_file, item):
            if item.title == "Bad":
                raise RuntimeError("AI API error")
            return make_ai_output()

        with (
            patch("scripts.daily_curation.call_claude_api", side_effect=ai_side_effect),
            patch("scripts.daily_curation.generate_image", return_value=str(tmp_path / "img.png")),
        ):
            count = await curate_for_account("A", scraper, config, dao)

        assert count == 1

    @pytest.mark.asyncio
    async def test_empty_scraper_returns_zero(self):
        from scripts.daily_curation import curate_for_account

        scraper = MagicMock()
        scraper.fetch.return_value = []

        config = MagicMock()
        config.get_account.return_value = make_account_config()
        dao = MagicMock()

        count = await curate_for_account("A", scraper, config, dao)
        assert count == 0

    @pytest.mark.asyncio
    async def test_dry_run_does_not_write_db(self):
        from scripts.daily_curation import curate_for_account

        scraper = MagicMock()
        scraper.fetch.return_value = [make_raw_item()]

        config = MagicMock()
        config.get_account.return_value = make_account_config()
        dao = MagicMock()

        with patch("scripts.daily_curation.call_claude_api", return_value=make_ai_output()):
            count = await curate_for_account("A", scraper, config, dao, dry_run=True)

        assert count == 1
        dao.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_draft_has_nonempty_reasoning(self, tmp_path):
        from scripts.daily_curation import curate_for_account

        scraper = MagicMock()
        scraper.fetch.return_value = [make_raw_item()]

        config = MagicMock()
        config.get_account.return_value = make_account_config()
        dao = MagicMock()

        with (
            patch("scripts.daily_curation.call_claude_api", return_value=make_ai_output()),
            patch("scripts.daily_curation.generate_image", return_value=str(tmp_path / "img.png")),
        ):
            await curate_for_account("A", scraper, config, dao)

        created_content = dao.create.call_args[0][0]
        assert created_content.reasoning.strip()


# ---------------------------------------------------------------------------
# call_claude_api tests
# ---------------------------------------------------------------------------


class TestCallClaudeApi:
    def test_raises_on_missing_should_publish(self, tmp_path):
        from scripts.daily_curation import call_claude_api

        bad_response = '{"title": "test"}'  # missing should_publish

        prompt_file = tmp_path / "account_a.txt"
        prompt_file.write_text(
            "---ITEM---\nTitle: {title}\nURL: {url}\nSummary: {summary}\nSource: {source}"
        )

        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=bad_response)]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_msg

        with patch("scripts.daily_curation.anthropic.Anthropic", return_value=mock_client):
            with pytest.raises(ValueError, match="should_publish"):
                call_claude_api(str(prompt_file), make_raw_item())
