"""
tests/test_main_watermark.py - CLI integration tests for watermark options (v1.8).

RED phase: written before implementation.
"""

import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest
from click.testing import CliRunner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mocks():
    mock_data = {
        "title": "Test Title",
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


ARTICLE_TEXT = "This is a long enough article text for testing purposes."


@pytest.fixture
def png_file(tmp_path):
    """Minimal 1×1 PNG file."""
    png_bytes = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x00, 0x02, 0x00, 0x01, 0xE2, 0x21, 0xBC,
        0x33, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
        0x44, 0xAE, 0x42, 0x60, 0x82,
    ])
    p = tmp_path / "logo.png"
    p.write_bytes(png_bytes)
    return p


# ---------------------------------------------------------------------------
# CLI help / option presence
# ---------------------------------------------------------------------------

class TestWatermarkCLIHelp:
    """New CLI options appear in --help output."""

    def test_watermark_option_in_help(self):
        from main import main
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert "--watermark" in result.output

    def test_watermark_position_option_in_help(self):
        from main import main
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert "--watermark-position" in result.output

    def test_watermark_opacity_option_in_help(self):
        from main import main
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert "--watermark-opacity" in result.output

    def test_brand_name_option_in_help(self):
        from main import main
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert "--brand-name" in result.output


# ---------------------------------------------------------------------------
# --watermark flag passes path / data URI to render_card
# ---------------------------------------------------------------------------

class TestWatermarkFileOption:
    """--watermark FILE reads the file and passes base64 data URI to render_card."""

    def test_watermark_flag_passes_data_uri_to_render_card(self, png_file):
        from main import main
        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--watermark", str(png_file),
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_kwargs = mock_render.call_args[1]
        assert "watermark_data" in call_kwargs
        assert call_kwargs["watermark_data"].startswith("data:image/png;base64,")

    def test_watermark_flag_does_not_pass_raw_path(self, png_file):
        """render_card must receive data URI, not the file path string."""
        from main import main
        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--watermark", str(png_file),
            ])
        assert result.exit_code == 0
        call_kwargs = mock_render.call_args[1]
        # Must not be the raw file path
        assert call_kwargs["watermark_data"] != str(png_file)

    def test_missing_watermark_file_exits_nonzero(self, tmp_path):
        """--watermark with a nonexistent file should fail (click.Path(exists=True))."""
        from main import main
        runner = CliRunner()
        result = runner.invoke(main, [
            "--text", ARTICLE_TEXT,
            "--watermark", str(tmp_path / "nonexistent.png"),
        ])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# --brand-name flag
# ---------------------------------------------------------------------------

class TestBrandNameOption:
    """--brand-name TEXT passes brand_name to render_card."""

    def test_brand_name_passed_to_render_card(self):
        from main import main
        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--brand-name", "@user",
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("brand_name") == "@user"

    def test_brand_name_with_at_symbol(self):
        from main import main
        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--brand-name", "@myhandle",
            ])
        assert result.exit_code == 0
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("brand_name") == "@myhandle"


# ---------------------------------------------------------------------------
# --watermark-opacity flag
# ---------------------------------------------------------------------------

class TestWatermarkOpacityOption:
    """--watermark-opacity FLOAT passes float to render_card."""

    def test_opacity_05_passes_as_float(self):
        from main import main
        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--brand-name", "@x",
                "--watermark-opacity", "0.5",
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("watermark_opacity") == pytest.approx(0.5)

    def test_opacity_10_passes_as_float(self):
        from main import main
        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--brand-name", "@x",
                "--watermark-opacity", "1.0",
            ])
        assert result.exit_code == 0
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("watermark_opacity") == pytest.approx(1.0)

    def test_opacity_is_float_type(self):
        from main import main
        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--brand-name", "@x",
                "--watermark-opacity", "0.3",
            ])
        assert result.exit_code == 0
        call_kwargs = mock_render.call_args[1]
        assert isinstance(call_kwargs.get("watermark_opacity"), float)


# ---------------------------------------------------------------------------
# --watermark-position flag
# ---------------------------------------------------------------------------

class TestWatermarkPositionOption:
    """--watermark-position CHOICE passes position string to render_card."""

    @pytest.mark.parametrize("position", ["top-left", "top-right", "bottom-left", "bottom-right"])
    def test_position_passed_to_render_card(self, position):
        from main import main
        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--brand-name", "@x",
                "--watermark-position", position,
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("watermark_position") == position


# ---------------------------------------------------------------------------
# No watermark args → render_card called without watermark kwargs (or with None)
# ---------------------------------------------------------------------------

class TestNoWatermarkArgs:
    """When no watermark flags are given, render_card gets None/default values."""

    def test_no_watermark_data_when_not_specified(self):
        from main import main
        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, ["--text", ARTICLE_TEXT])
        assert result.exit_code == 0
        call_kwargs = mock_render.call_args[1]
        # watermark_data must be None or absent
        assert call_kwargs.get("watermark_data") is None

    def test_no_brand_name_when_not_specified(self):
        from main import main
        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, ["--text", ARTICLE_TEXT])
        assert result.exit_code == 0
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("brand_name") is None


# ---------------------------------------------------------------------------
# Config file integration
# ---------------------------------------------------------------------------

class TestWatermarkConfig:
    """Config file brand_name / watermark settings are honoured."""

    def test_brand_name_from_config_used_when_no_cli_flag(self, tmp_path):
        from main import main

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\nbrand_name = "@cfg"\n')

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("brand_name") == "@cfg"

    def test_cli_brand_name_overrides_config(self, tmp_path):
        from main import main

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\nbrand_name = "@cfg"\n')

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
                "--brand-name", "@cli",
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("brand_name") == "@cli"

    def test_watermark_position_from_config(self, tmp_path):
        from main import main

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\nwatermark_position = "top-left"\nbrand_name = "@x"\n')

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("watermark_position") == "top-left"

    def test_watermark_opacity_from_config(self, tmp_path):
        from main import main

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\nwatermark_opacity = 0.5\nbrand_name = "@x"\n')

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("watermark_opacity") == pytest.approx(0.5)

    def test_watermark_file_from_config(self, tmp_path, png_file):
        from main import main

        cfg = tmp_path / ".imggenrc"
        cfg.write_text(f'[defaults]\nwatermark = "{png_file}"\n')

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("watermark_data") is not None
        assert call_kwargs["watermark_data"].startswith("data:image/")
