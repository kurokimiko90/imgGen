"""Tests for LevelUpConfig and AccountConfig (added to src/config.py)."""

import pytest
from pathlib import Path
from src.config import LevelUpConfig, AccountConfig


SAMPLE_TOML = b"""
[account.A]
name = "AI Automation"
platforms = ["threads", "x"]
publish_time = "12:30"
color_mood = "dark_tech"
prompt_file = "prompts/account_a.txt"
tone = "tech humor"

[account.B]
name = "PMP Career"
platforms = ["threads", "linkedin"]
publish_time = "07:30"
color_mood = "clean_light"
prompt_file = "prompts/account_b.txt"
tone = "professional but tired"

[account.C]
name = "Soccer English"
platforms = ["threads", "x", "instagram"]
publish_time = "20:00"
color_mood = "bold_contrast"
prompt_file = "prompts/account_c.txt"
tone = "fan passion"
"""


@pytest.fixture
def accounts_toml(tmp_path) -> str:
    """Create a temporary accounts.toml file and return its path string."""
    toml_file = tmp_path / "accounts.toml"
    toml_file.write_bytes(SAMPLE_TOML)
    return str(toml_file)


class TestLevelUpConfig:
    def test_loads_all_three_accounts(self, accounts_toml):
        """LevelUpConfig should load all three accounts from TOML."""
        cfg = LevelUpConfig(config_path=accounts_toml)
        accounts = cfg.list_accounts()
        assert set(accounts.keys()) == {"A", "B", "C"}

    def test_get_account_returns_account_config(self, accounts_toml):
        """get_account('A') should return an AccountConfig with correct fields."""
        cfg = LevelUpConfig(config_path=accounts_toml)
        account_a = cfg.get_account("A")
        assert isinstance(account_a, AccountConfig)
        assert account_a.name == "AI Automation"
        assert account_a.platforms == ["threads", "x"]
        assert account_a.publish_time == "12:30"
        assert account_a.color_mood == "dark_tech"
        assert account_a.prompt_file == "prompts/account_a.txt"
        assert account_a.tone == "tech humor"

    def test_get_account_b_correct_platforms(self, accounts_toml):
        """Account B should have linkedin in its platforms."""
        cfg = LevelUpConfig(config_path=accounts_toml)
        account_b = cfg.get_account("B")
        assert "linkedin" in account_b.platforms

    def test_get_account_c_has_instagram(self, accounts_toml):
        """Account C should include instagram."""
        cfg = LevelUpConfig(config_path=accounts_toml)
        account_c = cfg.get_account("C")
        assert "instagram" in account_c.platforms

    def test_missing_config_raises_file_not_found(self, tmp_path):
        """LevelUpConfig should raise FileNotFoundError when file is absent."""
        missing_path = str(tmp_path / "nonexistent.toml")
        with pytest.raises(FileNotFoundError, match="Config not found"):
            LevelUpConfig(config_path=missing_path)

    def test_get_unknown_account_raises_value_error(self, accounts_toml):
        """get_account() with unknown key should raise ValueError."""
        cfg = LevelUpConfig(config_path=accounts_toml)
        with pytest.raises(ValueError, match="Unknown account type"):
            cfg.get_account("Z")

    def test_list_accounts_returns_copy(self, accounts_toml):
        """list_accounts() should return a copy, not the internal dict."""
        cfg = LevelUpConfig(config_path=accounts_toml)
        accounts = cfg.list_accounts()
        accounts["X"] = None  # mutate the copy
        assert "X" not in cfg.list_accounts()

    def test_account_config_is_dataclass(self, accounts_toml):
        """AccountConfig should expose all expected fields."""
        cfg = LevelUpConfig(config_path=accounts_toml)
        account = cfg.get_account("C")
        assert hasattr(account, 'name')
        assert hasattr(account, 'platforms')
        assert hasattr(account, 'publish_time')
        assert hasattr(account, 'color_mood')
        assert hasattr(account, 'prompt_file')
        assert hasattr(account, 'tone')
