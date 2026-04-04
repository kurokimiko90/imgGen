"""
tests/test_config.py - TDD tests for src/config.py (v1.6 Config File Support).

Tests are written FIRST (RED phase) before implementation exists.
"""

import pytest
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import patch


# ---------------------------------------------------------------------------
# load_config() tests
# ---------------------------------------------------------------------------

class TestLoadConfigNoFile:
    """load_config() returns empty dict when no config file is found."""

    def test_returns_empty_dict_when_no_file_and_no_path(self, tmp_path):
        """With no ~/.imggenrc and no ./.imggenrc, returns {}."""
        from src.config import load_config

        with patch("pathlib.Path.home", return_value=tmp_path), \
             patch("pathlib.Path.cwd", return_value=tmp_path):
            result = load_config()
        assert result == {}

    def test_returns_empty_dict_when_explicit_path_does_not_exist(self, tmp_path):
        """Explicit path that doesn't exist → returns {}."""
        from src.config import load_config

        nonexistent = tmp_path / "missing.toml"
        result = load_config(config_path=nonexistent)
        assert result == {}

    def test_return_type_is_dict(self, tmp_path):
        """Always returns a dict, never None."""
        from src.config import load_config

        with patch("pathlib.Path.home", return_value=tmp_path), \
             patch("pathlib.Path.cwd", return_value=tmp_path):
            result = load_config()
        assert isinstance(result, dict)


class TestLoadConfigFromExplicitPath:
    """load_config(config_path=...) reads from the given path."""

    def test_reads_toml_from_given_path(self, tmp_path):
        """Reads [defaults] section from a TOML file."""
        from src.config import load_config

        cfg = tmp_path / "myconfig.toml"
        cfg.write_text('[defaults]\ntheme = "light"\n')
        result = load_config(config_path=cfg)
        assert result.get("theme") == "light"

    def test_reads_all_supported_keys(self, tmp_path):
        """All documented keys are parsed from TOML."""
        from src.config import load_config

        cfg = tmp_path / ".imggenrc"
        cfg.write_text(textwrap.dedent("""\
            [defaults]
            theme = "gradient"
            provider = "gemini"
            format = "square"
            scale = 1
            webp = true
            output_dir = "/tmp/cards"
        """))
        result = load_config(config_path=cfg)
        assert result == {
            "theme": "gradient",
            "provider": "gemini",
            "format": "square",
            "scale": 1,
            "webp": True,
            "output_dir": "/tmp/cards",
        }

    def test_returns_only_defaults_section_values(self, tmp_path):
        """Keys outside [defaults] are not returned."""
        from src.config import load_config

        cfg = tmp_path / ".imggenrc"
        cfg.write_text(textwrap.dedent("""\
            [defaults]
            theme = "dark"

            [other]
            foo = "bar"
        """))
        result = load_config(config_path=cfg)
        assert "foo" not in result
        assert result.get("theme") == "dark"

    def test_returns_empty_dict_if_no_defaults_section(self, tmp_path):
        """File exists but has no [defaults] section → returns {}."""
        from src.config import load_config

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[other]\nfoo = "bar"\n')
        result = load_config(config_path=cfg)
        assert result == {}

    def test_returns_empty_dict_for_empty_file(self, tmp_path):
        """Empty file → returns {}."""
        from src.config import load_config

        cfg = tmp_path / ".imggenrc"
        cfg.write_text("")
        result = load_config(config_path=cfg)
        assert result == {}

    def test_partial_keys_only_returns_present_keys(self, tmp_path):
        """Only specified keys are returned; absent keys not added."""
        from src.config import load_config

        cfg = tmp_path / ".imggenrc"
        cfg.write_text('[defaults]\ntheme = "light"\n')
        result = load_config(config_path=cfg)
        assert "provider" not in result
        assert "format" not in result
        assert result.get("theme") == "light"

    def test_invalid_toml_raises_value_error(self, tmp_path):
        """Malformed TOML raises ValueError."""
        from src.config import load_config

        cfg = tmp_path / ".imggenrc"
        cfg.write_text("[[[ not valid toml\n")
        with pytest.raises(ValueError, match="[Ii]nvalid|[Pp]arse|TOML"):
            load_config(config_path=cfg)


class TestLoadConfigAutoDiscovery:
    """load_config() auto-discovers ~/.imggenrc and ./.imggenrc."""

    def test_discovers_home_imggenrc(self, tmp_path):
        """Reads ~/.imggenrc when it exists."""
        from src.config import load_config

        home_cfg = tmp_path / ".imggenrc"
        home_cfg.write_text('[defaults]\ntheme = "light"\n')

        cwd = tmp_path / "work"
        cwd.mkdir()

        with patch("pathlib.Path.home", return_value=tmp_path), \
             patch("pathlib.Path.cwd", return_value=cwd):
            result = load_config()
        assert result.get("theme") == "light"

    def test_discovers_local_imggenrc(self, tmp_path):
        """Reads ./.imggenrc when it exists."""
        from src.config import load_config

        home_dir = tmp_path / "home"
        home_dir.mkdir()
        cwd = tmp_path / "project"
        cwd.mkdir()

        local_cfg = cwd / ".imggenrc"
        local_cfg.write_text('[defaults]\ntheme = "gradient"\n')

        with patch("pathlib.Path.home", return_value=home_dir), \
             patch("pathlib.Path.cwd", return_value=cwd):
            result = load_config()
        assert result.get("theme") == "gradient"

    def test_local_imggenrc_overrides_home_imggenrc(self, tmp_path):
        """Local .imggenrc takes precedence over home ~/.imggenrc."""
        from src.config import load_config

        home_dir = tmp_path / "home"
        home_dir.mkdir()
        home_cfg = home_dir / ".imggenrc"
        home_cfg.write_text('[defaults]\ntheme = "dark"\nprovider = "claude"\n')

        cwd = tmp_path / "project"
        cwd.mkdir()
        local_cfg = cwd / ".imggenrc"
        local_cfg.write_text('[defaults]\ntheme = "light"\n')

        with patch("pathlib.Path.home", return_value=home_dir), \
             patch("pathlib.Path.cwd", return_value=cwd):
            result = load_config()

        # Local overrides home for shared keys
        assert result.get("theme") == "light"
        # Home provides keys not in local
        assert result.get("provider") == "claude"

    def test_explicit_config_path_overrides_auto_discovery(self, tmp_path):
        """Explicit config_path wins over auto-discovered files."""
        from src.config import load_config

        home_dir = tmp_path / "home"
        home_dir.mkdir()
        home_cfg = home_dir / ".imggenrc"
        home_cfg.write_text('[defaults]\ntheme = "dark"\n')

        cwd = tmp_path / "project"
        cwd.mkdir()
        local_cfg = cwd / ".imggenrc"
        local_cfg.write_text('[defaults]\ntheme = "gradient"\n')

        explicit_cfg = tmp_path / "explicit.toml"
        explicit_cfg.write_text('[defaults]\ntheme = "light"\n')

        with patch("pathlib.Path.home", return_value=home_dir), \
             patch("pathlib.Path.cwd", return_value=cwd):
            result = load_config(config_path=explicit_cfg)

        assert result.get("theme") == "light"

    def test_both_home_and_local_missing_returns_empty(self, tmp_path):
        """Neither home nor local config exist → returns {}."""
        from src.config import load_config

        home_dir = tmp_path / "home"
        home_dir.mkdir()
        cwd = tmp_path / "project"
        cwd.mkdir()

        with patch("pathlib.Path.home", return_value=home_dir), \
             patch("pathlib.Path.cwd", return_value=cwd):
            result = load_config()
        assert result == {}


# ---------------------------------------------------------------------------
# get_default() tests
# ---------------------------------------------------------------------------

class TestGetDefault:
    """get_default() retrieves values from a config dict with fallback."""

    def test_returns_config_value_when_present(self):
        """Returns the value from config when key exists."""
        from src.config import get_default

        config = {"theme": "light", "scale": 1}
        assert get_default(config, "theme", "dark") == "light"
        assert get_default(config, "scale", 2) == 1

    def test_returns_fallback_when_key_not_in_config(self):
        """Returns fallback when key is absent."""
        from src.config import get_default

        config = {}
        assert get_default(config, "theme", "dark") == "dark"
        assert get_default(config, "scale", 2) == 2

    def test_returns_fallback_when_config_is_empty(self):
        """Empty config dict → always returns fallback."""
        from src.config import get_default

        assert get_default({}, "provider", "claude") == "claude"

    def test_returns_false_boolean_from_config(self):
        """Config value of False is returned (not overridden by fallback)."""
        from src.config import get_default

        config = {"webp": False}
        assert get_default(config, "webp", True) is False

    def test_returns_true_boolean_from_config(self):
        """Config value of True is returned."""
        from src.config import get_default

        config = {"webp": True}
        assert get_default(config, "webp", False) is True

    def test_returns_zero_int_from_config(self):
        """Config value of 0 is returned (falsy but valid)."""
        from src.config import get_default

        config = {"scale": 0}
        assert get_default(config, "scale", 2) == 0

    def test_returns_empty_string_from_config(self):
        """Config value of empty string is returned."""
        from src.config import get_default

        config = {"output_dir": ""}
        assert get_default(config, "output_dir", "/default") == ""

    def test_fallback_can_be_none(self):
        """Fallback of None is valid."""
        from src.config import get_default

        assert get_default({}, "theme", None) is None
