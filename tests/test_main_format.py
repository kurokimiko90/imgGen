"""
tests/test_main_format.py - Unit tests for main.py v1.5 multi-format options.

TDD: RED phase.
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# _resolve_output_path tests
# ---------------------------------------------------------------------------

class TestResolveOutputPath:
    """Test the filename-generation logic with format and webp flag."""

    def _call(self, output=None, theme="dark", card_format="story", webp=False):
        from main import _resolve_output_path
        return _resolve_output_path(output, theme, card_format=card_format, webp=webp)

    def test_auto_name_includes_format_story(self):
        path = self._call(theme="dark", card_format="story")
        assert "story" in path.name

    def test_auto_name_includes_format_square(self):
        path = self._call(theme="dark", card_format="square")
        assert "square" in path.name

    def test_auto_name_includes_format_landscape(self):
        path = self._call(theme="light", card_format="landscape")
        assert "landscape" in path.name

    def test_auto_name_includes_format_twitter(self):
        path = self._call(theme="gradient", card_format="twitter")
        assert "twitter" in path.name

    def test_auto_name_png_extension_by_default(self):
        path = self._call(theme="dark", card_format="story", webp=False)
        assert path.suffix == ".png"

    def test_auto_name_webp_extension_when_webp_true(self):
        path = self._call(theme="dark", card_format="story", webp=True)
        assert path.suffix == ".webp"

    def test_auto_name_includes_theme(self):
        path = self._call(theme="light", card_format="square")
        assert "light" in path.name

    def test_custom_output_path_respected(self, tmp_path):
        custom = str(tmp_path / "mycard.png")
        path = self._call(output=custom, theme="dark", card_format="square")
        assert path == Path(custom)

    def test_custom_output_no_suffix_gets_png(self, tmp_path):
        custom = str(tmp_path / "mycard")
        path = self._call(output=custom, theme="dark", card_format="story", webp=False)
        assert path.suffix == ".png"

    def test_custom_output_no_suffix_gets_webp_when_webp_true(self, tmp_path):
        custom = str(tmp_path / "mycard")
        path = self._call(output=custom, theme="dark", card_format="story", webp=True)
        assert path.suffix == ".webp"

    def test_filename_pattern_matches_expected(self):
        """Filename should follow: card_{theme}_{timestamp}_{format}.{ext}"""
        import re
        path = self._call(theme="dark", card_format="square", webp=False)
        # e.g. card_dark_20260328_120000_square.png
        assert re.search(r"card_dark_\d{8}_\d{6}_square\.png", path.name), (
            f"Expected pattern card_dark_<timestamp>_square.png, got: {path.name}"
        )


# ---------------------------------------------------------------------------
# CLI option tests via Click test runner
# ---------------------------------------------------------------------------

class TestCLIFormatOption:
    """Test that --format, --scale, --webp options exist and are passed through."""

    def _make_mocks(self):
        mock_data = {
            "title": "Test",
            "key_points": [{"emoji": "✅", "text": "Point 1"}],
            "source": "src",
            "theme_suggestion": "dark",
        }
        mock_extract = MagicMock(return_value=mock_data)
        mock_render = MagicMock(return_value="<html></html>")
        mock_screenshot_path = MagicMock(spec=Path)
        mock_screenshot_path.__str__ = MagicMock(return_value="/fake/output.png")
        mock_screenshot_path.stat.return_value.st_size = 1024 * 50
        mock_screenshot = MagicMock(return_value=mock_screenshot_path)
        return mock_extract, mock_render, mock_screenshot

    def test_format_option_exists(self):
        from main import main
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert "--format" in result.output

    def test_scale_option_exists(self):
        from main import main
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert "--scale" in result.output

    def test_webp_option_exists(self):
        from main import main
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert "--webp" in result.output

    def test_format_choices_in_help(self):
        from main import main
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert "story" in result.output
        assert "square" in result.output
        assert "landscape" in result.output
        assert "twitter" in result.output

    def test_invalid_format_rejected_by_cli(self):
        from main import main
        runner = CliRunner()
        result = runner.invoke(main, ["--text", "some article text here", "--format", "panorama"])
        assert result.exit_code != 0

    def test_render_card_called_with_format(self):
        from main import main
        mock_extract, mock_render, mock_screenshot = self._make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", "This is a long enough article text for testing purposes.",
                "--format", "square",
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}"
        assert mock_render.called, "render_card was never called"
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("format") == "square", (
            f"render_card was not called with format='square'. kwargs={call_kwargs}"
        )

    def test_take_screenshot_called_with_format_and_scale(self):
        from main import main
        mock_extract, mock_render, mock_screenshot = self._make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", "This is a long enough article text for testing purposes.",
                "--format", "landscape",
                "--scale", "1",
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}"
        assert mock_screenshot.called, "take_screenshot was never called"
        call_kwargs = mock_screenshot.call_args[1]
        assert call_kwargs.get("format") == "landscape"
        assert call_kwargs.get("scale") == 1

    def test_default_format_is_story(self):
        from main import main
        mock_extract, mock_render, mock_screenshot = self._make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", "This is a long enough article text for testing purposes.",
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}"
        assert mock_render.called, "render_card was never called"
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("format", "story") == "story"

    def test_webp_flag_affects_output_extension(self):
        from main import main
        mock_extract, mock_render, mock_screenshot = self._make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", "This is a long enough article text for testing purposes.",
                "--webp",
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}"
        assert mock_screenshot.called, "take_screenshot was never called"
        called_path = mock_screenshot.call_args[0][1]
        assert Path(str(called_path)).suffix == ".webp"

    def test_scale_1_passed_as_int(self):
        """Click returns scale as string from Choice; main.py must convert to int."""
        from main import main
        mock_extract, mock_render, mock_screenshot = self._make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", "This is a long enough article text for testing purposes.",
                "--scale", "1",
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}"
        assert mock_screenshot.called, "take_screenshot was never called"
        scale_val = mock_screenshot.call_args[1].get("scale")
        assert isinstance(scale_val, int), f"scale must be int, got {type(scale_val)}"
        assert scale_val == 1
