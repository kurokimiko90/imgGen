"""
tests/test_preset.py - TDD tests for preset functions in src/config.py (v2.4).

Tests are written FIRST (RED phase) before implementation exists.

Covers:
  - load_preset()
  - save_preset()
  - list_presets()
  - delete_preset()
  - _write_toml() internal helper
  - Round-trip save → load
"""

import textwrap
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# load_preset() tests
# ---------------------------------------------------------------------------

class TestLoadPreset:
    """load_preset() loads a named preset from config file."""

    def test_returns_empty_dict_for_nonexistent_preset(self, tmp_path):
        """Preset name not in file → returns {}."""
        from src.config import load_preset

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\ntheme = "dark"\n')
        result = load_preset("nonexistent", config_path=cfg)
        assert result == {}

    def test_returns_empty_dict_when_file_does_not_exist(self, tmp_path):
        """Config file missing → returns {}."""
        from src.config import load_preset

        missing = tmp_path / ".imggenrc"
        result = load_preset("my-preset", config_path=missing)
        assert result == {}

    def test_returns_preset_values_from_config_file(self, tmp_path):
        """Reads all key/value pairs from [preset.NAME] section."""
        from src.config import load_preset

        cfg = tmp_path / ".imggenrc"
        cfg.write_text(textwrap.dedent("""\
            [preset.weekly-ig]
            theme = "gradient"
            format = "story"
            provider = "claude"
            scale = 2
            webp = true
            brand_name = "@myhandle"
            watermark_position = "bottom-right"
        """))
        result = load_preset("weekly-ig", config_path=cfg)
        assert result == {
            "theme": "gradient",
            "format": "story",
            "provider": "claude",
            "scale": 2,
            "webp": True,
            "brand_name": "@myhandle",
            "watermark_position": "bottom-right",
        }

    def test_returns_empty_dict_for_empty_file(self, tmp_path):
        """Empty config file → returns {}."""
        from src.config import load_preset

        cfg = tmp_path / ".imggenrc"
        cfg.write_text("")
        result = load_preset("any", config_path=cfg)
        assert result == {}

    def test_only_loads_named_preset_not_other_presets(self, tmp_path):
        """Returns only the requested preset, ignores others."""
        from src.config import load_preset

        cfg = tmp_path / ".imggenrc"
        cfg.write_text(textwrap.dedent("""\
            [preset.alpha]
            theme = "dark"

            [preset.beta]
            theme = "light"
        """))
        result = load_preset("alpha", config_path=cfg)
        assert result == {"theme": "dark"}

    def test_returns_empty_dict_for_file_with_only_defaults_section(self, tmp_path):
        """File with [defaults] but no [preset.*] → returns {}."""
        from src.config import load_preset

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\ntheme = "light"\n')
        result = load_preset("my-preset", config_path=cfg)
        assert result == {}

    def test_returns_empty_dict_when_config_path_is_none_and_no_home_file(
        self, tmp_path, monkeypatch
    ):
        """With no config_path and no ~/.imggenrc, returns {}."""
        from src.config import load_preset

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        result = load_preset("missing")
        assert result == {}


# ---------------------------------------------------------------------------
# save_preset() tests
# ---------------------------------------------------------------------------

class TestSavePreset:
    """save_preset() persists a named preset to the config file."""

    def test_creates_config_file_if_not_exists(self, tmp_path):
        """Creates ~/.imggenrc when it does not exist."""
        from src.config import load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        assert not cfg.exists()
        save_preset("new-preset", {"theme": "dark"}, config_path=cfg)
        assert cfg.exists()

    def test_written_file_is_valid_toml(self, tmp_path):
        """Written file can be read back by tomllib."""
        import tomllib
        from src.config import save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("test", {"theme": "light", "scale": 1, "webp": False}, config_path=cfg)
        data = tomllib.loads(cfg.read_text())
        assert "preset" in data
        assert "test" in data["preset"]

    def test_saves_string_value(self, tmp_path):
        """String values are saved and loadable."""
        from src.config import load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("p", {"theme": "gradient"}, config_path=cfg)
        assert load_preset("p", config_path=cfg)["theme"] == "gradient"

    def test_saves_int_value(self, tmp_path):
        """Integer values are saved and loadable."""
        from src.config import load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("p", {"scale": 2}, config_path=cfg)
        assert load_preset("p", config_path=cfg)["scale"] == 2

    def test_saves_bool_true_value(self, tmp_path):
        """Boolean True is saved as TOML true."""
        from src.config import load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("p", {"webp": True}, config_path=cfg)
        assert load_preset("p", config_path=cfg)["webp"] is True

    def test_saves_bool_false_value(self, tmp_path):
        """Boolean False is saved as TOML false."""
        from src.config import load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("p", {"webp": False}, config_path=cfg)
        assert load_preset("p", config_path=cfg)["webp"] is False

    def test_saves_float_value(self, tmp_path):
        """Float values are saved and loadable."""
        from src.config import load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("p", {"watermark_opacity": 0.8}, config_path=cfg)
        result = load_preset("p", config_path=cfg)
        assert abs(result["watermark_opacity"] - 0.8) < 1e-9

    def test_adds_preset_section_to_existing_config(self, tmp_path):
        """Adds [preset.NAME] without destroying existing [defaults] section."""
        from src.config import load_config, load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\ntheme = "dark"\n')
        save_preset("my-preset", {"theme": "gradient"}, config_path=cfg)

        # Original defaults preserved
        defaults = load_config(config_path=cfg)
        assert defaults.get("theme") == "dark"

        # New preset saved
        preset = load_preset("my-preset", config_path=cfg)
        assert preset.get("theme") == "gradient"

    def test_overwrites_existing_preset_with_same_name(self, tmp_path):
        """Saving again with same name replaces the old values."""
        from src.config import load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("p", {"theme": "dark", "scale": 1}, config_path=cfg)
        save_preset("p", {"theme": "light"}, config_path=cfg)

        result = load_preset("p", config_path=cfg)
        assert result["theme"] == "light"
        # Old key not in new values should be gone
        assert "scale" not in result

    def test_preserves_other_presets_when_adding_new_one(self, tmp_path):
        """Adding a new preset does not destroy existing presets."""
        from src.config import load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("alpha", {"theme": "dark"}, config_path=cfg)
        save_preset("beta", {"theme": "light"}, config_path=cfg)

        alpha = load_preset("alpha", config_path=cfg)
        beta = load_preset("beta", config_path=cfg)
        assert alpha["theme"] == "dark"
        assert beta["theme"] == "light"

    def test_preserves_defaults_section_when_saving_preset(self, tmp_path):
        """[defaults] section survives save_preset()."""
        from src.config import load_config, save_preset

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\nprovider = "gemini"\nscale = 1\n')
        save_preset("p", {"theme": "gradient"}, config_path=cfg)

        defaults = load_config(config_path=cfg)
        assert defaults.get("provider") == "gemini"
        assert defaults.get("scale") == 1

    def test_does_not_save_none_values(self, tmp_path):
        """None values in the dict are skipped (not written to file)."""
        from src.config import load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("p", {"theme": "dark", "brand_name": None, "watermark": None}, config_path=cfg)
        result = load_preset("p", config_path=cfg)
        assert "brand_name" not in result
        assert "watermark" not in result
        assert result.get("theme") == "dark"


# ---------------------------------------------------------------------------
# list_presets() tests
# ---------------------------------------------------------------------------

class TestListPresets:
    """list_presets() returns all presets as a dict of dicts."""

    def test_returns_empty_dict_when_no_presets(self, tmp_path):
        """File with only [defaults], no [preset.*] → returns {}."""
        from src.config import list_presets

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\ntheme = "dark"\n')
        result = list_presets(config_path=cfg)
        assert result == {}

    def test_returns_empty_dict_when_file_missing(self, tmp_path):
        """Missing config file → returns {}."""
        from src.config import list_presets

        missing = tmp_path / ".imggenrc"
        result = list_presets(config_path=missing)
        assert result == {}

    def test_returns_all_preset_names(self, tmp_path):
        """Returns dict with all preset names as keys."""
        from src.config import list_presets

        cfg = tmp_path / ".imggenrc"
        cfg.write_text(textwrap.dedent("""\
            [preset.weekly-ig]
            theme = "gradient"

            [preset.dark-square]
            theme = "dark"
            format = "square"
        """))
        result = list_presets(config_path=cfg)
        assert set(result.keys()) == {"weekly-ig", "dark-square"}

    def test_returns_values_for_each_preset(self, tmp_path):
        """Each preset entry contains correct key/value pairs."""
        from src.config import list_presets

        cfg = tmp_path / ".imggenrc"
        cfg.write_text(textwrap.dedent("""\
            [preset.my-preset]
            theme = "light"
            scale = 1
            webp = true
        """))
        result = list_presets(config_path=cfg)
        assert result["my-preset"] == {"theme": "light", "scale": 1, "webp": True}

    def test_returns_empty_dict_for_empty_file(self, tmp_path):
        """Empty file → {}."""
        from src.config import list_presets

        cfg = tmp_path / ".imggenrc"
        cfg.write_text("")
        result = list_presets(config_path=cfg)
        assert result == {}


# ---------------------------------------------------------------------------
# delete_preset() tests
# ---------------------------------------------------------------------------

class TestDeletePreset:
    """delete_preset() removes a named preset from config."""

    def test_returns_false_if_preset_not_found(self, tmp_path):
        """Returns False when preset does not exist."""
        from src.config import delete_preset

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\ntheme = "dark"\n')
        assert delete_preset("nonexistent", config_path=cfg) is False

    def test_returns_false_if_file_missing(self, tmp_path):
        """Returns False when config file does not exist."""
        from src.config import delete_preset

        missing = tmp_path / ".imggenrc"
        assert delete_preset("any", config_path=missing) is False

    def test_returns_true_when_preset_deleted(self, tmp_path):
        """Returns True after successfully deleting a preset."""
        from src.config import delete_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("p", {"theme": "dark"}, config_path=cfg)
        assert delete_preset("p", config_path=cfg) is True

    def test_preset_no_longer_loadable_after_delete(self, tmp_path):
        """After deletion, load_preset returns {}."""
        from src.config import delete_preset, load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("p", {"theme": "dark"}, config_path=cfg)
        delete_preset("p", config_path=cfg)
        assert load_preset("p", config_path=cfg) == {}

    def test_preserves_other_presets_after_delete(self, tmp_path):
        """Deleting one preset leaves other presets intact."""
        from src.config import delete_preset, load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("alpha", {"theme": "dark"}, config_path=cfg)
        save_preset("beta", {"theme": "light"}, config_path=cfg)
        delete_preset("alpha", config_path=cfg)

        assert load_preset("alpha", config_path=cfg) == {}
        assert load_preset("beta", config_path=cfg) == {"theme": "light"}

    def test_preserves_defaults_section_after_delete(self, tmp_path):
        """[defaults] section is not affected by deleting a preset."""
        from src.config import delete_preset, load_config, save_preset

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\nprovider = "claude"\n')
        save_preset("p", {"theme": "dark"}, config_path=cfg)
        delete_preset("p", config_path=cfg)

        defaults = load_config(config_path=cfg)
        assert defaults.get("provider") == "claude"


# ---------------------------------------------------------------------------
# _write_toml() tests
# ---------------------------------------------------------------------------

class TestWriteToml:
    """_write_toml() serializes a nested dict to TOML string."""

    def test_writes_string_value(self):
        """String values are quoted in TOML output."""
        from src.config import _write_toml

        result = _write_toml({"defaults": {"theme": "dark"}})
        assert 'theme = "dark"' in result

    def test_writes_int_value(self):
        """Integer values are written without quotes."""
        from src.config import _write_toml

        result = _write_toml({"defaults": {"scale": 2}})
        assert "scale = 2" in result

    def test_writes_bool_true(self):
        """True is written as TOML 'true'."""
        from src.config import _write_toml

        result = _write_toml({"defaults": {"webp": True}})
        assert "webp = true" in result

    def test_writes_bool_false(self):
        """False is written as TOML 'false'."""
        from src.config import _write_toml

        result = _write_toml({"defaults": {"webp": False}})
        assert "webp = false" in result

    def test_writes_float_value(self):
        """Float values are written without quotes."""
        from src.config import _write_toml

        result = _write_toml({"defaults": {"opacity": 0.8}})
        assert "opacity = 0.8" in result

    def test_writes_section_header(self):
        """Section headers use [section] format."""
        from src.config import _write_toml

        result = _write_toml({"defaults": {"x": 1}})
        assert "[defaults]" in result

    def test_writes_nested_section_header(self):
        """Nested section [preset.NAME] is written correctly."""
        from src.config import _write_toml

        result = _write_toml({"preset": {"my-name": {"theme": "dark"}}})
        assert "[preset.my-name]" in result
        assert 'theme = "dark"' in result

    def test_output_is_valid_toml(self):
        """Output can be parsed back by tomllib."""
        import tomllib
        from src.config import _write_toml

        data = {
            "defaults": {"theme": "light", "scale": 1, "webp": False},
            "preset": {
                "test": {"theme": "gradient", "webp": True},
            },
        }
        result = _write_toml(data)
        parsed = tomllib.loads(result)
        assert parsed["defaults"]["theme"] == "light"
        assert parsed["preset"]["test"]["theme"] == "gradient"

    def test_empty_dict_produces_empty_or_whitespace_string(self):
        """Empty input produces empty or whitespace-only output."""
        from src.config import _write_toml

        result = _write_toml({})
        assert result.strip() == ""

    def test_section_with_no_keys_is_omitted_or_empty(self):
        """Section with empty dict emits just the header (or is skipped)."""
        from src.config import _write_toml

        result = _write_toml({"defaults": {}})
        # Either no output, or just the section header — it should still be parseable
        import tomllib
        parsed = tomllib.loads(result)
        assert "defaults" in parsed or parsed == {}


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------

class TestRoundTrip:
    """Round-trip: save_preset then load_preset returns same values."""

    def test_roundtrip_all_supported_types(self, tmp_path):
        """All supported value types survive a round-trip."""
        from src.config import load_preset, save_preset

        original = {
            "theme": "gradient",
            "format": "story",
            "provider": "claude",
            "scale": 2,
            "webp": True,
            "watermark_opacity": 0.75,
            "brand_name": "@myhandle",
            "watermark_position": "bottom-right",
        }
        cfg = tmp_path / ".imggenrc"
        save_preset("weekly-ig", original, config_path=cfg)
        loaded = load_preset("weekly-ig", config_path=cfg)
        assert loaded == original

    def test_roundtrip_multiple_presets(self, tmp_path):
        """Multiple presets all survive independently."""
        from src.config import load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        presets = {
            "p1": {"theme": "dark", "scale": 1},
            "p2": {"theme": "light", "webp": True},
            "p3": {"provider": "gemini", "format": "square"},
        }
        for name, values in presets.items():
            save_preset(name, values, config_path=cfg)

        for name, expected in presets.items():
            assert load_preset(name, config_path=cfg) == expected

    def test_roundtrip_with_defaults_section_intact(self, tmp_path):
        """Saving preset preserves existing [defaults] values after round-trip."""
        from src.config import load_config, load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\ntheme = "dark"\nscale = 1\n')

        save_preset("p", {"theme": "gradient", "webp": True}, config_path=cfg)

        defaults = load_config(config_path=cfg)
        assert defaults.get("theme") == "dark"
        assert defaults.get("scale") == 1

        preset = load_preset("p", config_path=cfg)
        assert preset == {"theme": "gradient", "webp": True}

    def test_overwrite_then_load_returns_updated_values(self, tmp_path):
        """Overwriting a preset and loading returns the updated values."""
        from src.config import load_preset, save_preset

        cfg = tmp_path / ".imggenrc"
        save_preset("p", {"theme": "dark", "scale": 1, "webp": False}, config_path=cfg)
        save_preset("p", {"theme": "light", "scale": 2, "webp": True}, config_path=cfg)

        result = load_preset("p", config_path=cfg)
        assert result == {"theme": "light", "scale": 2, "webp": True}


# ---------------------------------------------------------------------------
# Coverage gap tests
# ---------------------------------------------------------------------------

class TestCoverageGaps:
    """Tests targeting previously uncovered branches."""

    def test_parse_toml_full_invalid_toml_raises_value_error(self, tmp_path):
        """_parse_toml_full raises ValueError for malformed TOML."""
        from src.config import load_preset

        cfg = tmp_path / ".imggenrc"
        cfg.write_text("[[[ not valid toml\n")
        with pytest.raises(ValueError, match="[Ii]nvalid|TOML"):
            load_preset("any", config_path=cfg)

    def test_write_toml_with_top_level_scalar(self):
        """Top-level scalar values are written before sections."""
        import tomllib
        from src.config import _write_toml

        result = _write_toml({"top_key": "value", "defaults": {"x": 1}})
        parsed = tomllib.loads(result)
        assert parsed.get("top_key") == "value"
        assert parsed["defaults"]["x"] == 1

    def test_write_toml_skips_non_dict_in_second_pass(self):
        """Non-dict top-level values are handled correctly."""
        import tomllib
        from src.config import _write_toml

        result = _write_toml({"my_key": 42})
        parsed = tomllib.loads(result)
        assert parsed.get("my_key") == 42

    def test_write_toml_nested_section_with_empty_sub_dict(self):
        """Nested section with empty sub-dict produces valid TOML."""
        import tomllib
        from src.config import _write_toml

        result = _write_toml({"preset": {"empty": {}}})
        parsed = tomllib.loads(result)
        # Empty preset section is valid
        assert "preset" in parsed

    def test_write_toml_two_level_nesting_writes_all_sub_sections(self):
        """All sub-sections in a two-level nesting are written."""
        import tomllib
        from src.config import _write_toml

        data = {"preset": {"a": {"x": 1}, "b": {"y": 2}}}
        result = _write_toml(data)
        parsed = tomllib.loads(result)
        assert parsed["preset"]["a"]["x"] == 1
        assert parsed["preset"]["b"]["y"] == 2
