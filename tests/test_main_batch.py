"""
tests/test_main_batch.py - CLI integration tests for --batch option (v2.0).

TDD RED phase: written before implementation.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fake_results(entries):
    """Build a list of fake successful result dicts for a list of entries."""
    return [
        {
            "status": "ok",
            "output": f"/fake/output_{i + 1:03d}.png",
            "index": i + 1,
            "input": entry,
        }
        for i, entry in enumerate(entries)
    ]


def _make_batch_file(tmp_path, lines):
    """Write lines to a batch file and return its path."""
    batch_file = tmp_path / "batch.txt"
    batch_file.write_text("\n".join(lines) + "\n")
    return batch_file


# ---------------------------------------------------------------------------
# Help text / option presence
# ---------------------------------------------------------------------------


class TestHelpText:
    def test_batch_flag_in_help(self):
        """--batch flag appears in --help output."""
        from main import main
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "--batch" in result.output

    def test_workers_flag_in_help(self):
        """--workers flag appears in --help output."""
        from main import main
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "--workers" in result.output

    def test_output_dir_flag_in_help(self):
        """--output-dir flag appears in --help output."""
        from main import main
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "--output-dir" in result.output


# ---------------------------------------------------------------------------
# Mutual exclusion
# ---------------------------------------------------------------------------


class TestMutualExclusion:
    def test_batch_with_text_raises_usage_error(self, tmp_path):
        """--batch combined with --text raises UsageError."""
        from main import main
        runner = CliRunner()
        batch_file = _make_batch_file(tmp_path, ["https://example.com"])
        result = runner.invoke(main, ["--batch", str(batch_file), "--text", "some text"])
        assert result.exit_code != 0
        assert "mutually exclusive" in result.output.lower() or "cannot" in result.output.lower() or "usage" in result.output.lower()

    def test_batch_with_url_raises_usage_error(self, tmp_path):
        """--batch combined with --url raises UsageError."""
        from main import main
        runner = CliRunner()
        batch_file = _make_batch_file(tmp_path, ["https://example.com"])
        result = runner.invoke(main, ["--batch", str(batch_file), "--url", "https://example.com"])
        assert result.exit_code != 0

    def test_batch_with_file_raises_usage_error(self, tmp_path):
        """--batch combined with --file raises UsageError."""
        from main import main
        runner = CliRunner()
        batch_file = _make_batch_file(tmp_path, ["https://example.com"])
        article_file = tmp_path / "article.txt"
        article_file.write_text("Some article text that is long enough")
        result = runner.invoke(main, ["--batch", str(batch_file), "--file", str(article_file)])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Empty batch file
# ---------------------------------------------------------------------------


class TestEmptyBatch:
    def test_empty_batch_exits_cleanly(self, tmp_path):
        """Empty batch file exits with code 0 and 0 succeeded."""
        from main import main
        runner = CliRunner()
        batch_file = tmp_path / "empty.txt"
        batch_file.write_text("")

        with patch("main.run_batch") as mock_rb:
            import asyncio
            mock_rb.return_value = []
            # asyncio.run is called with run_batch coroutine - mock at module level
            result = runner.invoke(main, ["--batch", str(batch_file), "--output-dir", str(tmp_path)])

        # Should exit 0 (or non-error) with 0 succeeded message
        assert result.exit_code == 0

    def test_empty_batch_writes_report_with_zero_counts(self, tmp_path):
        """Empty batch file writes batch_report.json with total=0."""
        from main import main
        runner = CliRunner()
        batch_file = tmp_path / "empty.txt"
        batch_file.write_text("")

        with patch("main.run_batch") as mock_rb:
            mock_rb.return_value = []
            result = runner.invoke(main, ["--batch", str(batch_file), "--output-dir", str(tmp_path)])

        report_path = tmp_path / "batch_report.json"
        assert report_path.exists()
        report = json.loads(report_path.read_text())
        assert report["total"] == 0
        assert report["succeeded"] == 0
        assert report["failed"] == 0


# ---------------------------------------------------------------------------
# Successful batch processing
# ---------------------------------------------------------------------------


class TestBatchProcessing:
    def test_batch_processes_entries_and_writes_report(self, tmp_path):
        """--batch with valid entries processes them and writes batch_report.json."""
        from main import main
        runner = CliRunner()
        entries = ["https://a.com", "https://b.com"]
        batch_file = _make_batch_file(tmp_path, entries)
        fake_results = _make_fake_results(entries)

        with patch("main.run_batch") as mock_rb:
            mock_rb.return_value = fake_results
            result = runner.invoke(
                main,
                ["--batch", str(batch_file), "--output-dir", str(tmp_path)],
            )

        assert result.exit_code == 0
        report_path = tmp_path / "batch_report.json"
        assert report_path.exists()

    def test_batch_report_json_structure(self, tmp_path):
        """batch_report.json has correct top-level keys: total, succeeded, failed, results."""
        from main import main
        runner = CliRunner()
        entries = ["https://a.com", "https://b.com", "https://c.com"]
        batch_file = _make_batch_file(tmp_path, entries)
        fake_results = _make_fake_results(entries)

        with patch("main.run_batch") as mock_rb:
            mock_rb.return_value = fake_results
            runner.invoke(
                main,
                ["--batch", str(batch_file), "--output-dir", str(tmp_path)],
            )

        report = json.loads((tmp_path / "batch_report.json").read_text())
        assert "total" in report
        assert "succeeded" in report
        assert "failed" in report
        assert "results" in report
        assert report["total"] == 3
        assert report["succeeded"] == 3
        assert report["failed"] == 0
        assert len(report["results"]) == 3

    def test_batch_report_counts_failures(self, tmp_path):
        """batch_report.json correctly counts failed entries."""
        from main import main
        runner = CliRunner()
        entries = ["https://a.com", "https://fail.com"]
        batch_file = _make_batch_file(tmp_path, entries)
        fake_results = [
            {"status": "ok", "output": "/fake/a.png", "index": 1, "input": entries[0]},
            {"status": "error", "error": "HTTP error: 404", "index": 2, "input": entries[1]},
        ]

        with patch("main.run_batch") as mock_rb:
            mock_rb.return_value = fake_results
            runner.invoke(
                main,
                ["--batch", str(batch_file), "--output-dir", str(tmp_path)],
            )

        report = json.loads((tmp_path / "batch_report.json").read_text())
        assert report["total"] == 2
        assert report["succeeded"] == 1
        assert report["failed"] == 1

    def test_batch_report_results_items_ok(self, tmp_path):
        """batch_report.json results items have correct fields for ok entries."""
        from main import main
        runner = CliRunner()
        entries = ["https://a.com"]
        batch_file = _make_batch_file(tmp_path, entries)
        fake_results = _make_fake_results(entries)

        with patch("main.run_batch") as mock_rb:
            mock_rb.return_value = fake_results
            runner.invoke(
                main,
                ["--batch", str(batch_file), "--output-dir", str(tmp_path)],
            )

        report = json.loads((tmp_path / "batch_report.json").read_text())
        item = report["results"][0]
        assert item["index"] == 1
        assert item["input"] == "https://a.com"
        assert item["status"] == "ok"
        assert "output" in item

    def test_batch_report_results_items_error(self, tmp_path):
        """batch_report.json results items have correct fields for error entries."""
        from main import main
        runner = CliRunner()
        entries = ["https://fail.com"]
        batch_file = _make_batch_file(tmp_path, entries)
        fake_results = [
            {"status": "error", "error": "HTTP error: 404", "index": 1, "input": entries[0]},
        ]

        with patch("main.run_batch") as mock_rb:
            mock_rb.return_value = fake_results
            runner.invoke(
                main,
                ["--batch", str(batch_file), "--output-dir", str(tmp_path)],
            )

        report = json.loads((tmp_path / "batch_report.json").read_text())
        item = report["results"][0]
        assert item["status"] == "error"
        assert "error" in item

    def test_batch_summary_printed_to_stderr(self, tmp_path):
        """Batch completion summary is printed (captured in result output)."""
        from main import main
        runner = CliRunner()
        entries = ["https://a.com"]
        batch_file = _make_batch_file(tmp_path, entries)
        fake_results = _make_fake_results(entries)

        with patch("main.run_batch") as mock_rb:
            mock_rb.return_value = fake_results
            result = runner.invoke(
                main,
                ["--batch", str(batch_file), "--output-dir", str(tmp_path)],
            )

        # CliRunner merges stderr into output by default
        output = result.output or ""
        assert "succeeded" in output.lower() or "complete" in output.lower()

    def test_batch_failed_summary_lists_failures(self, tmp_path):
        """Batch summary lists failed entries when there are failures."""
        from main import main
        runner = CliRunner()
        entries = ["https://ok.com", "https://fail.com"]
        batch_file = _make_batch_file(tmp_path, entries)
        fake_results = [
            {"status": "ok", "output": "/fake/ok.png", "index": 1, "input": entries[0]},
            {"status": "error", "error": "HTTP error: 404", "index": 2, "input": entries[1]},
        ]

        with patch("main.run_batch") as mock_rb:
            mock_rb.return_value = fake_results
            result = runner.invoke(
                main,
                ["--batch", str(batch_file), "--output-dir", str(tmp_path)],
            )

        output = result.output or ""
        assert "fail" in output.lower()

    def test_run_batch_called_with_correct_workers(self, tmp_path):
        """--workers N is passed correctly to run_batch."""
        from main import main
        runner = CliRunner()
        entries = ["https://a.com"]
        batch_file = _make_batch_file(tmp_path, entries)
        fake_results = _make_fake_results(entries)

        with patch("main.run_batch") as mock_rb:
            mock_rb.return_value = fake_results
            runner.invoke(
                main,
                ["--batch", str(batch_file), "--workers", "5", "--output-dir", str(tmp_path)],
            )

        mock_rb.assert_called_once()
        _, kwargs = mock_rb.call_args
        assert kwargs.get("workers") == 5 or mock_rb.call_args[0][3] == 5

    def test_default_workers_is_3(self, tmp_path):
        """Default --workers value is 3."""
        from main import main
        runner = CliRunner()
        entries = ["https://a.com"]
        batch_file = _make_batch_file(tmp_path, entries)
        fake_results = _make_fake_results(entries)

        with patch("main.run_batch") as mock_rb:
            mock_rb.return_value = fake_results
            runner.invoke(
                main,
                ["--batch", str(batch_file), "--output-dir", str(tmp_path)],
            )

        mock_rb.assert_called_once()
        # workers argument is positional arg index 3 or keyword
        call_args = mock_rb.call_args
        workers_passed = (
            call_args.kwargs.get("workers")
            if call_args.kwargs.get("workers") is not None
            else call_args.args[3] if len(call_args.args) > 3 else None
        )
        assert workers_passed == 3

    def test_output_dir_passed_to_run_batch(self, tmp_path):
        """--output-dir is passed as output_dir to run_batch."""
        from main import main
        runner = CliRunner()
        output_dir = tmp_path / "my_output"
        output_dir.mkdir()
        entries = ["https://a.com"]
        batch_file = _make_batch_file(tmp_path, entries)
        fake_results = _make_fake_results(entries)

        with patch("main.run_batch") as mock_rb:
            mock_rb.return_value = fake_results
            runner.invoke(
                main,
                ["--batch", str(batch_file), "--output-dir", str(output_dir)],
            )

        mock_rb.assert_called_once()
        call_args = mock_rb.call_args
        output_dir_passed = (
            call_args.kwargs.get("output_dir")
            if call_args.kwargs.get("output_dir") is not None
            else call_args.args[2] if len(call_args.args) > 2 else None
        )
        assert Path(str(output_dir_passed)) == output_dir

    def test_comments_and_blank_lines_skipped_in_batch(self, tmp_path):
        """Lines with # comments and blank lines are skipped in batch file."""
        from main import main
        runner = CliRunner()
        batch_file = tmp_path / "batch.txt"
        batch_file.write_text(
            "# comment\n\nhttps://a.com\n\n# another comment\nhttps://b.com\n"
        )
        fake_results = _make_fake_results(["https://a.com", "https://b.com"])

        with patch("main.run_batch") as mock_rb:
            mock_rb.return_value = fake_results
            result = runner.invoke(
                main,
                ["--batch", str(batch_file), "--output-dir", str(tmp_path)],
            )

        mock_rb.assert_called_once()
        # Only 2 real entries passed (comments and blanks skipped)
        entries_passed = mock_rb.call_args.args[0] if mock_rb.call_args.args else mock_rb.call_args.kwargs.get("entries")
        assert len(entries_passed) == 2
