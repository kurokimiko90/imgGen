"""
tests/test_main_preset.py - TDD tests for preset CLI integration in main.py (v2.4).

Tests are written FIRST (RED phase) before implementation exists.

Covers:
  - --preset flag on the main command
  - imggen preset save / load / list / delete subcommands
  - Priority: CLI flags > preset values > config [defaults] > built-in defaults
"""

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

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
# --preset flag exists in help
# ---------------------------------------------------------------------------

class TestPresetFlagHelp:
    """--preset option and preset subcommand appear in help."""

    def test_preset_flag_appears_in_main_help(self):
        """--preset NAME appears in main command --help output."""
        from main import main

        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert "--preset" in result.output, (
            f"--preset not found in help:\n{result.output}"
        )

    def test_preset_subcommand_appears_in_main_help(self):
        """'preset' subcommand group is listed in main --help."""
        from main import main

        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert "preset" in result.output.lower(), (
            f"'preset' subcommand not in help:\n{result.output}"
        )

    def test_preset_save_appears_in_preset_help(self):
        """'save' appears in 'preset --help'."""
        from main import main

        runner = CliRunner()
        result = runner.invoke(main, ["preset", "--help"])
        assert result.exit_code == 0, f"Exit code: {result.exit_code}\n{result.output}"
        assert "save" in result.output

    def test_preset_list_appears_in_preset_help(self):
        """'list' appears in 'preset --help'."""
        from main import main

        runner = CliRunner()
        result = runner.invoke(main, ["preset", "--help"])
        assert "list" in result.output

    def test_preset_delete_appears_in_preset_help(self):
        """'delete' appears in 'preset --help'."""
        from main import main

        runner = CliRunner()
        result = runner.invoke(main, ["preset", "--help"])
        assert "delete" in result.output

    def test_preset_load_appears_in_preset_help(self):
        """'load' (show) appears in 'preset --help'."""
        from main import main

        runner = CliRunner()
        result = runner.invoke(main, ["preset", "--help"])
        assert "load" in result.output


# ---------------------------------------------------------------------------
# --preset NAME applies preset values
# ---------------------------------------------------------------------------

class TestPresetFlagAppliesValues:
    """--preset NAME applies saved preset values for unset CLI options."""

    def test_preset_flag_applies_theme_from_preset(self, tmp_path):
        """--preset NAME uses theme from preset when --theme not given."""
        from main import main
        from src.config import save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("my-preset", {"theme": "gradient", "format": "story"}, config_path=cfg)

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
                "--preset", "my-preset",
            ])
        assert result.exit_code == 0, f"Exit:\n{result.output}\n{result.exception}"
        call_args = mock_render.call_args
        theme_used = call_args[1].get("theme") if call_args[1] else call_args[0][1]
        assert theme_used == "gradient", f"Expected gradient, got: {theme_used}"

    def test_explicit_cli_theme_overrides_preset_theme(self, tmp_path):
        """Explicit --theme dark overrides preset theme=gradient."""
        from main import main
        from src.config import save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("my-preset", {"theme": "gradient"}, config_path=cfg)

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
                "--preset", "my-preset",
                "--theme", "dark",
            ])
        assert result.exit_code == 0, f"Exit:\n{result.output}\n{result.exception}"
        call_args = mock_render.call_args
        theme_used = call_args[1].get("theme") if call_args[1] else call_args[0][1]
        assert theme_used == "dark", f"Expected dark (CLI wins), got: {theme_used}"

    def test_preset_applies_format_when_not_set(self, tmp_path):
        """Preset format is applied when --format is not given."""
        from main import main
        from src.config import save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("my-preset", {"format": "square"}, config_path=cfg)

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
                "--preset", "my-preset",
            ])
        assert result.exit_code == 0, f"Exit:\n{result.output}\n{result.exception}"
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("format") == "square", (
            f"Expected format=square from preset, got: {mock_render.call_args}"
        )

    def test_preset_applies_provider_when_not_set(self, tmp_path):
        """Preset provider is used when --provider is not given."""
        from main import main
        from src.config import save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("p", {"provider": "gemini"}, config_path=cfg)

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
                "--preset", "p",
            ])
        assert result.exit_code == 0, f"Exit:\n{result.output}\n{result.exception}"
        call_kwargs = mock_extract.call_args[1]
        assert call_kwargs.get("provider") == "gemini", (
            f"Expected provider=gemini from preset, got: {mock_extract.call_args}"
        )

    def test_preset_applies_brand_name_when_not_set(self, tmp_path):
        """Preset brand_name is applied when --brand-name is not given."""
        from main import main
        from src.config import save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("p", {"brand_name": "@myhandle"}, config_path=cfg)

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
                "--preset", "p",
            ])
        assert result.exit_code == 0, f"Exit:\n{result.output}\n{result.exception}"
        call_kwargs = mock_render.call_args[1]
        assert call_kwargs.get("brand_name") == "@myhandle", (
            f"Expected brand_name=@myhandle from preset, got: {mock_render.call_args}"
        )

    def test_unknown_preset_raises_error(self, tmp_path):
        """--preset with nonexistent name produces an error."""
        from main import main

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\ntheme = "dark"\n')

        runner = CliRunner()
        result = runner.invoke(main, [
            "--text", ARTICLE_TEXT,
            "--config", str(cfg),
            "--preset", "no-such-preset",
        ])
        assert result.exit_code != 0, "Expected non-zero exit for unknown preset"
        assert "no-such-preset" in result.output.lower() or \
               "not found" in result.output.lower() or \
               "unknown" in result.output.lower() or \
               (result.exception is not None), (
            f"Expected error mentioning preset name:\n{result.output}"
        )

    def test_preset_config_defaults_priority(self, tmp_path):
        """Priority: CLI > preset > config defaults.

        Setup: config default theme=dark, preset theme=gradient, no CLI --theme.
        Expected: gradient (preset wins over config default).
        """
        from main import main
        from src.config import save_preset

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\ntheme = "dark"\n')
        save_preset("p", {"theme": "gradient"}, config_path=cfg)

        mock_extract, mock_render, mock_screenshot = _make_mocks()
        runner = CliRunner()
        with patch("src.extractor.extract_key_points", mock_extract), \
             patch("src.renderer.render_card", mock_render), \
             patch("src.screenshotter.take_screenshot", mock_screenshot):
            result = runner.invoke(main, [
                "--text", ARTICLE_TEXT,
                "--config", str(cfg),
                "--preset", "p",
            ])
        assert result.exit_code == 0, f"Exit:\n{result.output}\n{result.exception}"
        call_args = mock_render.call_args
        theme_used = call_args[1].get("theme") if call_args[1] else call_args[0][1]
        assert theme_used == "gradient", (
            f"Expected gradient (preset > config default), got: {theme_used}"
        )


# ---------------------------------------------------------------------------
# preset list subcommand
# ---------------------------------------------------------------------------

class TestPresetListSubcommand:
    """imggen preset list shows saved presets."""

    def test_list_with_no_presets_prints_message(self, tmp_path):
        """When no presets exist, prints a 'no presets' message."""
        from main import main

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\ntheme = "dark"\n')

        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(cfg), "preset", "list"])
        assert result.exit_code == 0, f"Exit:\n{result.output}"
        assert "no preset" in result.output.lower(), (
            f"Expected 'no presets' message, got:\n{result.output}"
        )

    def test_list_with_no_config_file_prints_message(self, tmp_path):
        """Missing config file → 'no presets' message."""
        from main import main

        missing = tmp_path / ".imggenrc"
        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(missing), "preset", "list"])
        assert result.exit_code == 0
        assert "no preset" in result.output.lower()

    def test_list_shows_saved_preset_names(self, tmp_path):
        """Saved preset names appear in list output."""
        from main import main
        from src.config import save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("weekly-ig", {"theme": "gradient", "format": "story"}, config_path=cfg)
        save_preset("dark-square", {"theme": "dark", "format": "square"}, config_path=cfg)

        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(cfg), "preset", "list"])
        assert result.exit_code == 0, f"Exit:\n{result.output}"
        assert "weekly-ig" in result.output
        assert "dark-square" in result.output

    def test_list_shows_key_parameters(self, tmp_path):
        """List output shows key parameters for each preset."""
        from main import main
        from src.config import save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("p", {"theme": "gradient", "format": "story"}, config_path=cfg)

        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(cfg), "preset", "list"])
        assert result.exit_code == 0
        # Should show some values
        assert "gradient" in result.output or "story" in result.output


# ---------------------------------------------------------------------------
# preset save subcommand
# ---------------------------------------------------------------------------

class TestPresetSaveSubcommand:
    """imggen preset save NAME --option VALUE ... saves a preset."""

    def test_preset_save_creates_preset(self, tmp_path):
        """preset save NAME --theme X saves the preset."""
        from main import main
        from src.config import load_preset

        cfg = tmp_path / ".imggenrc"
        runner = CliRunner()
        result = runner.invoke(main, [
            "--config", str(cfg),
            "preset", "save", "my-preset",
            "--theme", "gradient",
            "--format", "story",
        ])
        assert result.exit_code == 0, f"Exit:\n{result.output}\n{result.exception}"
        saved = load_preset("my-preset", config_path=cfg)
        assert saved.get("theme") == "gradient"
        assert saved.get("format") == "story"

    def test_preset_save_confirms_save(self, tmp_path):
        """preset save prints confirmation message."""
        from main import main

        cfg = tmp_path / ".imggenrc"
        runner = CliRunner()
        result = runner.invoke(main, [
            "--config", str(cfg),
            "preset", "save", "p",
            "--theme", "dark",
        ])
        assert result.exit_code == 0
        assert "saved" in result.output.lower() or "preset" in result.output.lower(), (
            f"Expected confirmation, got:\n{result.output}"
        )

    def test_preset_save_with_multiple_options(self, tmp_path):
        """preset save stores all provided options."""
        from main import main
        from src.config import load_preset

        cfg = tmp_path / ".imggenrc"
        runner = CliRunner()
        result = runner.invoke(main, [
            "--config", str(cfg),
            "preset", "save", "full",
            "--theme", "gradient",
            "--format", "square",
            "--provider", "gemini",
            "--scale", "1",
            "--brand-name", "@test",
        ])
        assert result.exit_code == 0, f"Exit:\n{result.output}\n{result.exception}"
        saved = load_preset("full", config_path=cfg)
        assert saved.get("theme") == "gradient"
        assert saved.get("format") == "square"
        assert saved.get("provider") == "gemini"
        assert saved.get("scale") == 1
        assert saved.get("brand_name") == "@test"


# ---------------------------------------------------------------------------
# preset load (show) subcommand
# ---------------------------------------------------------------------------

class TestPresetLoadSubcommand:
    """imggen preset load NAME prints the preset values."""

    def test_preset_load_prints_toml_output(self, tmp_path):
        """preset load NAME prints key=value pairs."""
        from main import main
        from src.config import save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("p", {"theme": "gradient", "scale": 2}, config_path=cfg)

        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(cfg), "preset", "load", "p"])
        assert result.exit_code == 0, f"Exit:\n{result.output}"
        assert "gradient" in result.output
        assert "theme" in result.output

    def test_preset_load_nonexistent_shows_error(self, tmp_path):
        """preset load NAME for missing preset shows error."""
        from main import main

        cfg = tmp_path / ".imggenrc"
        cfg.write_text("")

        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(cfg), "preset", "load", "missing"])
        assert result.exit_code != 0 or "not found" in result.output.lower() or \
               "no preset" in result.output.lower() or "missing" in result.output.lower(), (
            f"Expected error for missing preset:\n{result.output}"
        )


# ---------------------------------------------------------------------------
# preset delete subcommand
# ---------------------------------------------------------------------------

class TestPresetDeleteSubcommand:
    """imggen preset delete NAME removes a saved preset."""

    def test_preset_delete_removes_preset(self, tmp_path):
        """preset delete NAME removes the preset."""
        from main import main
        from src.config import load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("p", {"theme": "dark"}, config_path=cfg)

        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(cfg), "preset", "delete", "p"])
        assert result.exit_code == 0, f"Exit:\n{result.output}\n{result.exception}"
        assert load_preset("p", config_path=cfg) == {}

    def test_preset_delete_confirms_deletion(self, tmp_path):
        """preset delete NAME prints confirmation."""
        from main import main
        from src.config import save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("p", {"theme": "dark"}, config_path=cfg)

        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(cfg), "preset", "delete", "p"])
        assert result.exit_code == 0
        assert "delet" in result.output.lower() or "removed" in result.output.lower() or \
               "p" in result.output, (
            f"Expected deletion confirmation:\n{result.output}"
        )

    def test_preset_delete_nonexistent_shows_error(self, tmp_path):
        """preset delete NAME for missing preset shows error message."""
        from main import main

        cfg = tmp_path / ".imggenrc"
        cfg.write_text("")

        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(cfg), "preset", "delete", "nonexistent"])
        # Should either non-zero exit OR show an error message
        output_lower = result.output.lower()
        assert result.exit_code != 0 or \
               "not found" in output_lower or \
               "no preset" in output_lower or \
               "nonexistent" in output_lower, (
            f"Expected error for nonexistent preset:\n{result.output}"
        )

    def test_preset_delete_preserves_other_presets(self, tmp_path):
        """Deleting one preset does not affect others."""
        from main import main
        from src.config import load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("alpha", {"theme": "dark"}, config_path=cfg)
        save_preset("beta", {"theme": "light"}, config_path=cfg)

        runner = CliRunner()
        runner.invoke(main, ["--config", str(cfg), "preset", "delete", "alpha"])

        assert load_preset("beta", config_path=cfg) == {"theme": "light"}
        assert load_preset("alpha", config_path=cfg) == {}


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestPresetEdgeCases:
    """Edge cases for preset system."""

    def test_preset_name_with_hyphens(self, tmp_path):
        """Preset names with hyphens work correctly."""
        from main import main
        from src.config import load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("my-weekly-ig", {"theme": "gradient"}, config_path=cfg)
        assert load_preset("my-weekly-ig", config_path=cfg) == {"theme": "gradient"}

    def test_preset_without_config_uses_home_imggenrc(self, tmp_path, monkeypatch):
        """When --config not given, preset subcommands use ~/.imggenrc."""
        from main import main
        from src.config import save_preset

        home_cfg = tmp_path / ".imggenrc"
        save_preset("home-preset", {"theme": "light"}, config_path=home_cfg)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, ["preset", "list"])
        assert result.exit_code == 0
        assert "home-preset" in result.output

    def test_preset_save_does_not_save_options_with_none_value(self, tmp_path):
        """Options not provided to preset save are not stored."""
        from main import main
        from src.config import load_preset

        cfg = tmp_path / ".imggenrc"
        runner = CliRunner()
        result = runner.invoke(main, [
            "--config", str(cfg),
            "preset", "save", "minimal",
            "--theme", "dark",
        ])
        assert result.exit_code == 0, f"Exit:\n{result.output}\n{result.exception}"
        saved = load_preset("minimal", config_path=cfg)
        # Only theme should be saved, not provider/format/etc. with None
        assert saved.get("theme") == "dark"
        assert "provider" not in saved or saved.get("provider") is not None

    def test_preset_save_with_webp_flag(self, tmp_path):
        """preset save --webp stores webp=True."""
        from main import main
        from src.config import load_preset

        cfg = tmp_path / ".imggenrc"
        runner = CliRunner()
        result = runner.invoke(main, [
            "--config", str(cfg),
            "preset", "save", "webp-preset",
            "--webp",
        ])
        assert result.exit_code == 0, f"Exit:\n{result.output}\n{result.exception}"
        saved = load_preset("webp-preset", config_path=cfg)
        assert saved.get("webp") is True

    def test_preset_save_with_watermark_position(self, tmp_path):
        """preset save --watermark-position stores the value."""
        from main import main
        from src.config import load_preset

        cfg = tmp_path / ".imggenrc"
        runner = CliRunner()
        result = runner.invoke(main, [
            "--config", str(cfg),
            "preset", "save", "wm-preset",
            "--watermark-position", "top-left",
        ])
        assert result.exit_code == 0, f"Exit:\n{result.output}\n{result.exception}"
        saved = load_preset("wm-preset", config_path=cfg)
        assert saved.get("watermark_position") == "top-left"

    def test_preset_save_with_watermark_opacity(self, tmp_path):
        """preset save --watermark-opacity stores the value."""
        from main import main
        from src.config import load_preset

        cfg = tmp_path / ".imggenrc"
        runner = CliRunner()
        result = runner.invoke(main, [
            "--config", str(cfg),
            "preset", "save", "opacity-preset",
            "--watermark-opacity", "0.5",
        ])
        assert result.exit_code == 0, f"Exit:\n{result.output}\n{result.exception}"
        saved = load_preset("opacity-preset", config_path=cfg)
        assert abs(saved.get("watermark_opacity") - 0.5) < 1e-9

    def test_preset_load_shows_bool_value(self, tmp_path):
        """preset load prints bool values as 'true'/'false'."""
        from main import main
        from src.config import save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("booltest", {"webp": True, "scale": 2}, config_path=cfg)

        runner = CliRunner()
        result = runner.invoke(main, ["--config", str(cfg), "preset", "load", "booltest"])
        assert result.exit_code == 0, f"Exit:\n{result.output}"
        assert "true" in result.output or "webp" in result.output
