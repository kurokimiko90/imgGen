"""
tests/test_main_config.py - TDD tests for config file integration in main.py (v1.6).

Tests are written FIRST (RED phase) before implementation exists.
"""

import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

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


# ---------------------------------------------------------------------------
# --config flag tests
# ---------------------------------------------------------------------------

class TestConfigCLIFlag:
    """The --config flag exists and loads from the specified file."""

    def test_config_option_exists_in_help(self):
        """--config flag appears in --help output."""
        from main import main
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert "--config" in result.output

    def test_config_flag_loads_theme_from_file(self, tmp_path):
        """--config FILE loads theme value from that file."""
        from main import main

        cfg = tmp_path / "myrc.toml"
        cfg.write_text('[defaults]\ntheme = "gradient"\n')

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
        # render_card should have been called with theme="gradient"
        call_args = mock_render.call_args
        theme_used = call_args[1].get("theme") if call_args[1] else call_args[0][1]
        assert theme_used == "gradient", (
            f"Expected theme=gradient from config, got: {mock_render.call_args}"
        )

    def test_config_flag_loads_provider_from_file(self, tmp_path):
        """--config FILE loads provider value that is forwarded to extractor."""
        from main import main

        cfg = tmp_path / "myrc.toml"
        cfg.write_text('[defaults]\nprovider = "gemini"\n')

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
        call_kwargs = mock_extract.call_args[1]
        assert call_kwargs.get("provider") == "gemini", (
            f"Expected provider=gemini, got: {mock_extract.call_args}"
        )

    def test_config_flag_loads_format_from_file(self, tmp_path):
        """--config FILE loads format value passed to render_card."""
        from main import main

        cfg = tmp_path / "myrc.toml"
        cfg.write_text('[defaults]\nformat = "square"\n')

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
        assert call_kwargs.get("format") == "square", (
            f"Expected format=square from config, got: {mock_render.call_args}"
        )

    def test_config_flag_loads_scale_from_file(self, tmp_path):
        """--config FILE loads scale value passed to take_screenshot."""
        from main import main

        cfg = tmp_path / "myrc.toml"
        cfg.write_text('[defaults]\nscale = 1\n')

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
        call_kwargs = mock_screenshot.call_args[1]
        assert call_kwargs.get("scale") == 1, (
            f"Expected scale=1 from config, got: {mock_screenshot.call_args}"
        )

    def test_config_flag_loads_webp_from_file(self, tmp_path):
        """--config FILE with webp=true sets WebP output."""
        from main import main

        cfg = tmp_path / "myrc.toml"
        cfg.write_text('[defaults]\nwebp = true\n')

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
        # The path passed to take_screenshot should have .webp extension
        called_path = mock_screenshot.call_args[0][1]
        assert Path(str(called_path)).suffix == ".webp", (
            f"Expected .webp output from config, got: {called_path}"
        )


# ---------------------------------------------------------------------------
# CLI flag overrides config tests
# ---------------------------------------------------------------------------

class TestCLIOverridesConfig:
    """Explicit CLI flags override config file values."""

    def test_explicit_theme_overrides_config_theme(self, tmp_path):
        """--theme cli flag wins over config theme."""
        from main import main

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\ntheme = "light"\n')

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
                "--theme", "dark",
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_args = mock_render.call_args
        theme_used = call_args[1].get("theme") if call_args[1] else call_args[0][1]
        assert theme_used == "dark", (
            f"Expected theme=dark from CLI, got: {mock_render.call_args}"
        )

    def test_explicit_format_overrides_config_format(self, tmp_path):
        """--format cli flag wins over config format."""
        from main import main

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\nformat = "square"\n')

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
                "--format", "landscape",
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("format") == "landscape", (
            f"Expected format=landscape from CLI, got: {mock_render.call_args}"
        )

    def test_explicit_provider_overrides_config_provider(self, tmp_path):
        """--provider cli flag wins over config provider."""
        from main import main

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\nprovider = "gemini"\n')

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
                "--provider", "gpt",
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_kwargs = mock_extract.call_args[1]
        assert call_kwargs.get("provider") == "gpt", (
            f"Expected provider=gpt from CLI, got: {mock_extract.call_args}"
        )

    def test_explicit_scale_overrides_config_scale(self, tmp_path):
        """--scale cli flag wins over config scale."""
        from main import main

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\nscale = 1\n')

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
                "--scale", "2",
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_kwargs = mock_screenshot.call_args[1]
        assert call_kwargs.get("scale") == 2, (
            f"Expected scale=2 from CLI, got: {mock_screenshot.call_args}"
        )

    def test_explicit_webp_flag_overrides_config_webp_false(self, tmp_path):
        """--webp cli flag enables WebP even if config has webp=false."""
        from main import main

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\nwebp = false\n')

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
                "--webp",
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        called_path = mock_screenshot.call_args[0][1]
        assert Path(str(called_path)).suffix == ".webp"


# ---------------------------------------------------------------------------
# Default fallback tests
# ---------------------------------------------------------------------------

class TestBuiltinDefaultsWhenNoConfig:
    """When no config file is present, built-in defaults are used."""

    def test_theme_defaults_to_dark_without_config(self):
        """Without config, theme defaults to 'dark'."""
        from main import main

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()

        # Point home and cwd to dirs with no .imggenrc
        import tempfile, os
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            with patch("pathlib.Path.home", return_value=td_path), \
                 patch("pathlib.Path.cwd", return_value=td_path), \
                 patch("src.extractor.extract_key_points", mock_extract), \
                 patch("src.renderer.render_card", mock_render), \
                 patch("src.screenshotter.take_screenshot", mock_screenshot):
                result = runner.invoke(main, [
                    "--text", ARTICLE_TEXT,
                ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_args = mock_render.call_args
        theme_used = call_args[1].get("theme") if call_args[1] else call_args[0][1]
        assert theme_used == "dark", f"Expected default theme=dark, got: {theme_used}"

    def test_provider_defaults_to_cli_without_config(self):
        """Without config, provider defaults to 'cli'."""
        from main import main

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()

        import tempfile
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            with patch("pathlib.Path.home", return_value=td_path), \
                 patch("pathlib.Path.cwd", return_value=td_path), \
                 patch("src.extractor.extract_key_points", mock_extract), \
                 patch("src.renderer.render_card", mock_render), \
                 patch("src.screenshotter.take_screenshot", mock_screenshot):
                result = runner.invoke(main, [
                    "--text", ARTICLE_TEXT,
                ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_kwargs = mock_extract.call_args[1]
        assert call_kwargs.get("provider") == "cli"

    def test_format_defaults_to_story_without_config(self):
        """Without config, format defaults to 'story'."""
        from main import main

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()

        import tempfile
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            with patch("pathlib.Path.home", return_value=td_path), \
                 patch("pathlib.Path.cwd", return_value=td_path), \
                 patch("src.extractor.extract_key_points", mock_extract), \
                 patch("src.renderer.render_card", mock_render), \
                 patch("src.screenshotter.take_screenshot", mock_screenshot):
                result = runner.invoke(main, [
                    "--text", ARTICLE_TEXT,
                ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("format") == "story"

    def test_scale_defaults_to_2_without_config(self):
        """Without config, scale defaults to 2."""
        from main import main

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()

        import tempfile
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            with patch("pathlib.Path.home", return_value=td_path), \
                 patch("pathlib.Path.cwd", return_value=td_path), \
                 patch("src.extractor.extract_key_points", mock_extract), \
                 patch("src.renderer.render_card", mock_render), \
                 patch("src.screenshotter.take_screenshot", mock_screenshot):
                result = runner.invoke(main, [
                    "--text", ARTICLE_TEXT,
                ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        call_kwargs = mock_screenshot.call_args[1]
        assert call_kwargs.get("scale") == 2


# ---------------------------------------------------------------------------
# output_dir config key tests
# ---------------------------------------------------------------------------

class TestOutputDirConfig:
    """output_dir config key changes the base output directory."""

    def test_output_dir_from_config_used_as_base_dir(self, tmp_path):
        """When output_dir is set in config, generated output path uses that dir."""
        from main import main

        out_dir = tmp_path / "custom_output"
        out_dir.mkdir()

        cfg = tmp_path / ".imggenrc"
        cfg.write_text(f'[defaults]\noutput_dir = "{out_dir}"\n')

        mock_extract, mock_render, mock_screenshot = _make_mocks()

        # Capture the path passed to take_screenshot
        captured_paths = []
        def capture_screenshot(html, path, **kwargs):
            captured_paths.append(path)
            return mock_screenshot.return_value

        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", capture_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
            ])
        assert result.exit_code == 0, f"CLI error: {result.output}\n{result.exception}"
        assert len(captured_paths) == 1
        assert str(out_dir) in str(captured_paths[0]), (
            f"Expected output path under {out_dir}, got: {captured_paths[0]}"
        )
