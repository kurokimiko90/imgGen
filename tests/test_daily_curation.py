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
        dao.find_by_source_url.return_value = None  # No duplicates

        with (
            patch("scripts.daily_curation.call_claude_api_batch", return_value=[make_ai_output()]),
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
        dao.find_by_source_url.return_value = None  # No duplicates

        with patch("scripts.daily_curation.call_claude_api_batch", return_value=[make_ai_output(should_publish=False)]):
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
        dao.find_by_source_url.return_value = None  # No duplicates
        # First call raises, second succeeds
        dao.create.side_effect = [RuntimeError("DB error"), None]

        # Batch call succeeds for both items
        ai_outputs = [make_ai_output(), make_ai_output()]

        with (
            patch("scripts.daily_curation.call_claude_api_batch", return_value=ai_outputs),
            patch("scripts.daily_curation.generate_image", return_value=str(tmp_path / "img.png")),
        ):
            count = await curate_for_account("A", scraper, config, dao)

        # Should process both items, one fails but second succeeds
        assert count == 1
        # Verify both were attempted (2 calls despite 1 failing)
        assert dao.create.call_count == 2

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
    async def test_batch_failure_falls_back_to_per_item(self):
        """When batch AI call fails, should fall back to per-item calls."""
        from scripts.daily_curation import curate_for_account

        scraper = MagicMock()
        scraper.fetch.return_value = [make_raw_item("Item 1"), make_raw_item("Item 2")]

        config = MagicMock()
        config.get_account.return_value = make_account_config()

        dao = MagicMock()
        dao.find_by_source_url.return_value = None  # No duplicates

        # Batch call fails, but per-item fallback succeeds
        with (
            patch("scripts.daily_curation.call_claude_api_batch", side_effect=RuntimeError("CLI not found")),
            patch("scripts.daily_curation.call_claude_api", return_value=make_ai_output()),
            patch("scripts.daily_curation.generate_image", return_value="/tmp/img.png"),
        ):
            count = await curate_for_account("A", scraper, config, dao)

        # Should still create drafts via per-item fallback
        assert count == 2
        assert dao.create.call_count == 2

    @pytest.mark.asyncio
    async def test_deduplicates_by_source_url(self, tmp_path):
        """Should skip items with duplicate source URLs in DB."""
        from scripts.daily_curation import curate_for_account

        scraper = MagicMock()
        scraper.fetch.return_value = [
            make_raw_item("Item 1", "http://example.com/1"),
            make_raw_item("Item 2", "http://example.com/2"),
        ]

        config = MagicMock()
        config.get_account.return_value = make_account_config()

        dao = MagicMock()
        # First URL exists in DB, second doesn't
        def find_by_url_side_effect(url):
            if url == "http://example.com/1":
                return MagicMock(id="123")  # Existing content
            return None
        dao.find_by_source_url.side_effect = find_by_url_side_effect

        with (
            patch("scripts.daily_curation.call_claude_api_batch", return_value=[make_ai_output()]),
            patch("scripts.daily_curation.generate_image", return_value=str(tmp_path / "img.png")),
        ):
            count = await curate_for_account("A", scraper, config, dao)

        # Should only create draft for Item 2 (Item 1 is duplicate)
        assert count == 1
        dao.create.assert_called_once()

        # Verify find_by_source_url was called for both items
        assert dao.find_by_source_url.call_count == 2

    @pytest.mark.asyncio
    async def test_dry_run_does_not_write_db(self):
        from scripts.daily_curation import curate_for_account

        scraper = MagicMock()
        scraper.fetch.return_value = [make_raw_item()]

        config = MagicMock()
        config.get_account.return_value = make_account_config()
        dao = MagicMock()
        dao.find_by_source_url.return_value = None  # No duplicates

        with patch("scripts.daily_curation.call_claude_api_batch", return_value=[make_ai_output()]):
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
        dao.find_by_source_url.return_value = None  # No duplicates

        with (
            patch("scripts.daily_curation.call_claude_api_batch", return_value=[make_ai_output()]),
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

        with patch("scripts.daily_curation._call_claude", return_value=bad_response):
            with pytest.raises(ValueError, match="should_publish"):
                call_claude_api(str(prompt_file), make_raw_item())


# ---------------------------------------------------------------------------
# call_claude_api_batch tests
# ---------------------------------------------------------------------------


class TestCallClaudeApiBatch:
    def test_batch_returns_array_of_results(self, tmp_path):
        from scripts.daily_curation import call_claude_api_batch

        prompt_file = tmp_path / "account_a.txt"
        prompt_file.write_text(
            "---BATCH---\nTitle: {title}\nURL: {url}\nSummary: {summary}\nSource: {source}"
        )

        items = [make_raw_item("Item 1"), make_raw_item("Item 2")]

        batch_response = """
        [
            {
                "should_publish": true,
                "title": "Result 1",
                "body": "Body 1",
                "content_type": "NEWS_RECAP",
                "reasoning": "Good news"
            },
            {
                "should_publish": false,
                "title": "Result 2",
                "body": "Body 2",
                "content_type": "NEWS_RECAP",
                "reasoning": "Not relevant"
            }
        ]
        """

        with patch("scripts.daily_curation._call_claude", return_value=batch_response):
            results = call_claude_api_batch(str(prompt_file), items)

        assert len(results) == 2
        assert results[0]["should_publish"] is True
        assert results[1]["should_publish"] is False

    def test_batch_fallback_to_per_item_on_parse_error(self, tmp_path):
        from scripts.daily_curation import call_claude_api_batch

        prompt_file = tmp_path / "account_a.txt"
        prompt_file.write_text(
            "---BATCH---\nTitle: {title}\nURL: {url}\nSummary: {summary}\nSource: {source}"
        )

        items = [make_raw_item("Item 1"), make_raw_item("Item 2")]

        # Invalid JSON array (fallback should trigger)
        bad_response = "This is not JSON"

        with (
            patch("scripts.daily_curation._call_claude", return_value=bad_response),
            patch("scripts.daily_curation.call_claude_api", return_value=make_ai_output()),
        ):
            results = call_claude_api_batch(str(prompt_file), items)

        # Should have fallen back to per-item calls (1 call for each of 2 items)
        assert len(results) == 2
        assert all(r.get("should_publish") for r in results)

    def test_batch_empty_items_returns_empty(self, tmp_path):
        from scripts.daily_curation import call_claude_api_batch

        prompt_file = tmp_path / "account_a.txt"
        prompt_file.write_text("template")

        results = call_claude_api_batch(str(prompt_file), [])
        assert results == []
