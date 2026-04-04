"""
tests/test_batch.py - Unit tests for batch processing module (v2.0).

TDD RED phase: written before implementation.
Tests parse_batch_file, process_entry, and run_batch.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, call
import pytest


# ---------------------------------------------------------------------------
# parse_batch_file
# ---------------------------------------------------------------------------


class TestParseBatchFile:
    def test_empty_file_returns_empty_list(self, tmp_path):
        """parse_batch_file returns [] for an empty file."""
        from src.batch import parse_batch_file

        batch_file = tmp_path / "batch.txt"
        batch_file.write_text("")
        result = parse_batch_file(batch_file)
        assert result == []

    def test_skips_blank_lines(self, tmp_path):
        """parse_batch_file skips blank lines."""
        from src.batch import parse_batch_file

        batch_file = tmp_path / "batch.txt"
        batch_file.write_text("\nhttps://example.com\n\nhttps://other.com\n\n")
        result = parse_batch_file(batch_file)
        assert result == ["https://example.com", "https://other.com"]

    def test_skips_comment_lines(self, tmp_path):
        """parse_batch_file skips lines starting with #."""
        from src.batch import parse_batch_file

        batch_file = tmp_path / "batch.txt"
        batch_file.write_text(
            "# This is a comment\nhttps://example.com\n# Another comment\n"
        )
        result = parse_batch_file(batch_file)
        assert result == ["https://example.com"]

    def test_returns_urls_correctly(self, tmp_path):
        """parse_batch_file returns http and https URLs."""
        from src.batch import parse_batch_file

        batch_file = tmp_path / "batch.txt"
        batch_file.write_text(
            "https://example.com/article\nhttp://old-site.com/page\n"
        )
        result = parse_batch_file(batch_file)
        assert result == ["https://example.com/article", "http://old-site.com/page"]

    def test_returns_file_paths_correctly(self, tmp_path):
        """parse_batch_file returns absolute and relative file paths."""
        from src.batch import parse_batch_file

        batch_file = tmp_path / "batch.txt"
        batch_file.write_text(
            "/absolute/path/article.txt\nrelative/path/article.txt\n"
        )
        result = parse_batch_file(batch_file)
        assert result == [
            "/absolute/path/article.txt",
            "relative/path/article.txt",
        ]

    def test_mixed_content_with_comments_and_blanks(self, tmp_path):
        """parse_batch_file handles mix of URLs, paths, comments, blanks."""
        from src.batch import parse_batch_file

        batch_file = tmp_path / "batch.txt"
        batch_file.write_text(
            "# Section 1: URLs\n"
            "https://example.com\n"
            "\n"
            "# Section 2: files\n"
            "/some/article.txt\n"
            "\n"
        )
        result = parse_batch_file(batch_file)
        assert result == ["https://example.com", "/some/article.txt"]

    def test_strips_trailing_whitespace_from_entries(self, tmp_path):
        """parse_batch_file strips leading/trailing whitespace from each entry."""
        from src.batch import parse_batch_file

        batch_file = tmp_path / "batch.txt"
        batch_file.write_text("  https://example.com  \n  /some/path.txt  \n")
        result = parse_batch_file(batch_file)
        assert result == ["https://example.com", "/some/path.txt"]


# ---------------------------------------------------------------------------
# process_entry - success
# ---------------------------------------------------------------------------


FAKE_DATA = {
    "title": "Test Title",
    "key_points": [{"emoji": "✅", "text": "Point 1"}],
    "source": "test",
    "theme_suggestion": "dark",
}

DEFAULT_OPTIONS = {
    "theme": "dark",
    "format": "story",
    "provider": "claude",
    "scale": 2,
    "webp": False,
    "watermark_data": None,
    "watermark_position": "bottom-right",
    "watermark_opacity": 0.8,
    "brand_name": None,
}


class TestProcessEntrySuccess:
    def test_returns_ok_status_on_success(self, tmp_path):
        """process_entry returns dict with status='ok' on success."""
        from src.batch import process_entry

        fake_output = tmp_path / "card.png"
        fake_output.write_bytes(b"PNG")

        with (
            patch("src.batch._process_text", return_value=fake_output) as mock_pipeline,
        ):
            semaphore = asyncio.Semaphore(3)
            result = asyncio.run(
                process_entry("https://example.com", 1, DEFAULT_OPTIONS, tmp_path, semaphore)
            )

        assert result["status"] == "ok"
        assert result["index"] == 1

    def test_returns_output_path_on_success(self, tmp_path):
        """process_entry result contains the output file path as string on success."""
        from src.batch import process_entry

        fake_output = tmp_path / "card.png"
        fake_output.write_bytes(b"PNG")

        with patch("src.batch._process_text", return_value=fake_output):
            semaphore = asyncio.Semaphore(3)
            result = asyncio.run(
                process_entry("/some/article.txt", 2, DEFAULT_OPTIONS, tmp_path, semaphore)
            )

        assert result["status"] == "ok"
        assert result["output"] == str(fake_output)
        assert result["index"] == 2

    def test_input_stored_in_result(self, tmp_path):
        """process_entry result contains the input entry."""
        from src.batch import process_entry

        fake_output = tmp_path / "card.png"
        fake_output.write_bytes(b"PNG")

        with patch("src.batch._process_text", return_value=fake_output):
            semaphore = asyncio.Semaphore(3)
            result = asyncio.run(
                process_entry("https://example.com", 3, DEFAULT_OPTIONS, tmp_path, semaphore)
            )

        assert result["input"] == "https://example.com"


# ---------------------------------------------------------------------------
# process_entry - failure
# ---------------------------------------------------------------------------


class TestProcessEntryFailure:
    def test_returns_error_status_on_exception(self, tmp_path):
        """process_entry returns dict with status='error' when pipeline raises."""
        from src.batch import process_entry

        with patch("src.batch._process_text", side_effect=RuntimeError("boom")):
            semaphore = asyncio.Semaphore(3)
            result = asyncio.run(
                process_entry("https://broken.com", 1, DEFAULT_OPTIONS, tmp_path, semaphore)
            )

        assert result["status"] == "error"
        assert result["index"] == 1

    def test_returns_error_message_on_exception(self, tmp_path):
        """process_entry result contains error message on failure."""
        from src.batch import process_entry

        with patch("src.batch._process_text", side_effect=ValueError("bad input")):
            semaphore = asyncio.Semaphore(3)
            result = asyncio.run(
                process_entry("https://broken.com", 2, DEFAULT_OPTIONS, tmp_path, semaphore)
            )

        assert result["status"] == "error"
        assert "bad input" in result["error"]
        assert result["index"] == 2

    def test_error_result_contains_input(self, tmp_path):
        """process_entry error result contains the input entry."""
        from src.batch import process_entry

        with patch("src.batch._process_text", side_effect=RuntimeError("network fail")):
            semaphore = asyncio.Semaphore(3)
            result = asyncio.run(
                process_entry("https://broken.com", 5, DEFAULT_OPTIONS, tmp_path, semaphore)
            )

        assert result["input"] == "https://broken.com"


# ---------------------------------------------------------------------------
# run_batch
# ---------------------------------------------------------------------------


class TestRunBatch:
    def test_empty_entries_returns_empty_list(self, tmp_path):
        """run_batch with empty entries list returns []."""
        from src.batch import run_batch

        results = asyncio.run(run_batch([], DEFAULT_OPTIONS, tmp_path, workers=3))
        assert results == []

    def test_calls_process_entry_for_each_entry(self, tmp_path):
        """run_batch calls process_entry for every entry in the list."""
        from src.batch import run_batch

        entries = ["https://a.com", "https://b.com", "https://c.com"]
        fake_result = {"status": "ok", "output": str(tmp_path / "x.png"), "index": 1, "input": "x"}

        with patch("src.batch.process_entry", new_callable=AsyncMock, return_value=fake_result) as mock_pe:
            results = asyncio.run(run_batch(entries, DEFAULT_OPTIONS, tmp_path, workers=3))

        assert mock_pe.call_count == 3

    def test_does_not_abort_on_single_failure(self, tmp_path):
        """run_batch continues processing all entries even if one fails."""
        from src.batch import run_batch

        entries = ["https://ok.com", "https://fail.com", "https://ok2.com"]

        ok_result = {"status": "ok", "output": str(tmp_path / "x.png"), "index": 1, "input": "x"}
        fail_result = {"status": "error", "error": "HTTP error: 404", "index": 2, "input": "https://fail.com"}

        call_count = 0

        async def mock_process_entry(entry, index, options, output_dir, semaphore):
            nonlocal call_count
            call_count += 1
            if entry == "https://fail.com":
                return fail_result
            return {**ok_result, "index": index, "input": entry}

        with patch("src.batch.process_entry", side_effect=mock_process_entry):
            results = asyncio.run(run_batch(entries, DEFAULT_OPTIONS, tmp_path, workers=3))

        assert call_count == 3
        statuses = {r["status"] for r in results}
        assert "ok" in statuses
        assert "error" in statuses

    def test_results_contain_all_entries(self, tmp_path):
        """run_batch returns one result dict per entry."""
        from src.batch import run_batch

        entries = ["https://a.com", "https://b.com"]
        ok_result = {"status": "ok", "output": "/some/path.png", "index": 1, "input": "x"}

        with patch("src.batch.process_entry", new_callable=AsyncMock, return_value=ok_result):
            results = asyncio.run(run_batch(entries, DEFAULT_OPTIONS, tmp_path, workers=3))

        assert len(results) == 2

    def test_semaphore_limits_concurrency(self, tmp_path):
        """run_batch uses a Semaphore(workers) to limit concurrency."""
        from src.batch import run_batch
        import asyncio as _asyncio

        entries = ["https://a.com", "https://b.com", "https://c.com", "https://d.com", "https://e.com"]
        active_at_once = []
        current_active = 0
        max_observed = 0

        async def mock_process_entry(entry, index, options, output_dir, semaphore):
            nonlocal current_active, max_observed
            # Acquire and check inside the semaphore context to measure true concurrency
            async with semaphore:
                current_active += 1
                if current_active > max_observed:
                    max_observed = current_active
                await _asyncio.sleep(0.01)
                current_active -= 1
            return {"status": "ok", "output": "/x.png", "index": index, "input": entry}

        # patch process_entry but let run_batch create and pass its own semaphore
        with patch("src.batch.process_entry", side_effect=mock_process_entry):
            asyncio.run(run_batch(entries, DEFAULT_OPTIONS, tmp_path, workers=2))

        # With workers=2, at most 2 should run concurrently
        assert max_observed <= 2

    def test_results_ordered_by_index(self, tmp_path):
        """run_batch results list is ordered by entry index (1-based)."""
        from src.batch import run_batch

        entries = ["https://a.com", "https://b.com", "https://c.com"]

        async def mock_process_entry(entry, index, options, output_dir, semaphore):
            return {"status": "ok", "output": "/x.png", "index": index, "input": entry}

        with patch("src.batch.process_entry", side_effect=mock_process_entry):
            results = asyncio.run(run_batch(entries, DEFAULT_OPTIONS, tmp_path, workers=3))

        indices = [r["index"] for r in results]
        assert indices == sorted(indices)


# ---------------------------------------------------------------------------
# _process_text internals (URL vs file path dispatch)
# ---------------------------------------------------------------------------


class TestProcessTextDispatch:
    def test_url_entry_fetches_url_content(self, tmp_path):
        """_process_text with a URL entry calls _fetch_url_content."""
        from src.batch import _process_text

        fake_output = tmp_path / "out.png"
        fake_output.write_bytes(b"PNG")

        with (
            patch("src.batch._fetch_url_content", return_value="Article text from URL") as mock_fetch,
            patch("src.batch.extract", return_value=FAKE_DATA),
            patch("src.batch.render_and_capture", return_value=fake_output),
        ):
            result = _process_text("https://example.com/article", 1, DEFAULT_OPTIONS, tmp_path)

        mock_fetch.assert_called_once_with("https://example.com/article")

    def test_file_path_entry_reads_file(self, tmp_path):
        """_process_text with a file path reads the file content."""
        from src.batch import _process_text

        article_file = tmp_path / "article.txt"
        article_file.write_text("Article text from file")
        fake_output = tmp_path / "out.png"
        fake_output.write_bytes(b"PNG")

        with (
            patch("src.batch.extract", return_value=FAKE_DATA),
            patch("src.batch.render_and_capture", return_value=fake_output),
        ):
            result = _process_text(str(article_file), 1, DEFAULT_OPTIONS, tmp_path)

        assert result == fake_output

    def test_calls_extract_key_points(self, tmp_path):
        """_process_text calls extract_key_points with the article text."""
        from src.batch import _process_text

        fake_output = tmp_path / "out.png"
        fake_output.write_bytes(b"PNG")

        with (
            patch("src.batch._fetch_url_content", return_value="Some article text"),
            patch("src.batch.extract", return_value=FAKE_DATA) as mock_extract,
            patch("src.batch.render_and_capture", return_value=fake_output),
        ):
            _process_text("https://example.com", 1, DEFAULT_OPTIONS, tmp_path)

        mock_extract.assert_called_once_with("Some article text", provider="claude")

    def test_calls_render_and_capture(self, tmp_path):
        """_process_text calls render_and_capture with extracted data and options."""
        from src.batch import _process_text

        fake_output = tmp_path / "out.png"
        fake_output.write_bytes(b"PNG")

        with (
            patch("src.batch._fetch_url_content", return_value="Some article text"),
            patch("src.batch.extract", return_value=FAKE_DATA),
            patch("src.batch.render_and_capture", return_value=fake_output) as mock_render,
        ):
            _process_text("https://example.com", 1, DEFAULT_OPTIONS, tmp_path)

        mock_render.assert_called_once()
        args, kwargs = mock_render.call_args
        assert args[0] == FAKE_DATA  # data
        assert args[1].theme == "dark"  # PipelineOptions.theme

    def test_calls_render_and_capture_returns_path(self, tmp_path):
        """_process_text calls render_and_capture and returns its result."""
        from src.batch import _process_text

        fake_output = tmp_path / "out.png"
        fake_output.write_bytes(b"PNG")

        with (
            patch("src.batch._fetch_url_content", return_value="Some article text"),
            patch("src.batch.extract", return_value=FAKE_DATA),
            patch("src.batch.render_and_capture", return_value=fake_output) as mock_ss,
        ):
            result = _process_text("https://example.com", 1, DEFAULT_OPTIONS, tmp_path)

        mock_ss.assert_called_once()
        assert result == fake_output

    def test_auto_names_output_file_with_index(self, tmp_path):
        """_process_text auto-generates output filename containing index."""
        from src.batch import _process_text

        fake_output = tmp_path / "card_dark_20240101_120000_story_001.png"
        fake_output.write_bytes(b"PNG")

        with (
            patch("src.batch._fetch_url_content", return_value="Some article text"),
            patch("src.batch.extract", return_value=FAKE_DATA),
            patch("src.batch.render_and_capture", return_value=fake_output) as mock_ss,
        ):
            _process_text("https://example.com", 1, DEFAULT_OPTIONS, tmp_path)

        # Verify the output path passed to render_and_capture contains 001 index
        mock_ss.assert_called_once()
        out_path_arg = mock_ss.call_args[0][2]  # (data, pipe_opts, output_path)
        assert "001" in str(out_path_arg)

    def test_http_url_entry_fetches_url_content(self, tmp_path):
        """_process_text treats http:// entries as URLs."""
        from src.batch import _process_text

        fake_output = tmp_path / "out.png"
        fake_output.write_bytes(b"PNG")

        with (
            patch("src.batch._fetch_url_content", return_value="HTTP article text") as mock_fetch,
            patch("src.batch.extract", return_value=FAKE_DATA),
            patch("src.batch.render_and_capture", return_value=fake_output),
        ):
            _process_text("http://example.com/article", 1, DEFAULT_OPTIONS, tmp_path)

        mock_fetch.assert_called_once_with("http://example.com/article")


# ---------------------------------------------------------------------------
# _fetch_url_content unit tests
# ---------------------------------------------------------------------------


class TestFetchUrlContent:
    def test_returns_plain_text_for_non_html_response(self):
        """_fetch_url_content returns response text for non-HTML content types."""
        from src.batch import _fetch_url_content
        import httpx

        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "plain article text"
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_response):
            result = _fetch_url_content("https://example.com/article.txt")

        assert result == "plain article text"

    def test_strips_html_tags_for_html_response(self):
        """_fetch_url_content strips HTML tags for HTML content type."""
        from src.batch import _fetch_url_content

        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.text = "<html><body><p>Hello world</p></body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_response):
            result = _fetch_url_content("https://example.com/page")

        assert "<html>" not in result
        assert "Hello world" in result

    def test_raises_runtime_error_on_http_error(self):
        """_fetch_url_content raises RuntimeError on HTTP status error."""
        from src.batch import _fetch_url_content
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 404
        http_error = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)

        with patch("httpx.get", side_effect=http_error):
            with pytest.raises(RuntimeError, match="HTTP error"):
                _fetch_url_content("https://example.com/missing")

    def test_raises_runtime_error_on_network_error(self):
        """_fetch_url_content raises RuntimeError on network/connection error."""
        from src.batch import _fetch_url_content
        import httpx

        network_error = httpx.RequestError("Connection refused", request=MagicMock())

        with patch("httpx.get", side_effect=network_error):
            with pytest.raises(RuntimeError, match="Network error"):
                _fetch_url_content("https://unreachable.example.com")

    def test_strips_script_and_style_tags(self):
        """_fetch_url_content removes <script> and <style> blocks from HTML."""
        from src.batch import _fetch_url_content

        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = (
            "<html><head><style>body{color:red}</style></head>"
            "<body><script>alert('x')</script><p>Content here</p></body></html>"
        )
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_response):
            result = _fetch_url_content("https://example.com/page")

        assert "alert" not in result
        assert "color:red" not in result
        assert "Content here" in result
