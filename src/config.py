"""
src/config.py - Config file support for imgGen (v2.4) + LevelUp multi-account config.

Loads user defaults from TOML config files so CLI flags don't need
to be typed every time.

Priority order (highest to lowest):
  1. Explicit --config PATH supplied on CLI
  2. ./.imggenrc  (local project override)
  3. ~/.imggenrc  (user home default)
  4. Built-in hardcoded defaults (in main.py)

v2.4 additions: preset system (load_preset, save_preset, list_presets,
delete_preset, _write_toml).

LevelUp additions: AccountConfig, LevelUpConfig for multi-account management.
"""

import tomllib
from pathlib import Path
from dataclasses import dataclass

_CONFIG_FILENAME = ".imggenrc"


def _parse_toml_file(path: Path) -> dict:
    """Read a TOML file and return the [defaults] section, or {} if absent.

    Raises:
        ValueError: If the file exists but contains invalid TOML.
    """
    try:
        raw = path.read_bytes()
    except OSError:
        return {}

    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Invalid TOML in config file '{path}': {exc}") from exc

    return dict(data.get("defaults", {}))


def _parse_toml_full(path: Path) -> dict:
    """Read a TOML file and return the full parsed dict, or {} if absent.

    Raises:
        ValueError: If the file exists but contains invalid TOML.
    """
    try:
        raw = path.read_bytes()
    except OSError:
        return {}

    try:
        return tomllib.loads(raw.decode("utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Invalid TOML in config file '{path}': {exc}") from exc


def _write_toml(data: dict) -> str:
    """Serialize a nested dict to TOML string.

    Supports str/int/float/bool values and one level of [section] nesting.
    The top-level dict may contain:
      - scalar values (written before any section headers)
      - nested dicts (written as [section] or [section.key] headers)

    For the preset use-case, the structure is:
      {
        "defaults": {"key": value, ...},
        "preset": {
          "name1": {"key": value, ...},
          "name2": {"key": value, ...},
        },
      }
    """
    def _format_value(v) -> str:
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, str):
            # Escape backslashes and double-quotes inside the string
            escaped = v.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        if isinstance(v, float):
            return repr(v)
        return str(v)

    lines: list[str] = []

    # First pass: top-level scalar values (rare, but handle them)
    for key, value in data.items():
        if not isinstance(value, dict):
            lines.append(f"{key} = {_format_value(value)}")

    # Second pass: nested sections
    for section, section_value in data.items():
        if not isinstance(section_value, dict):
            continue

        # Detect whether the values are dicts themselves (two-level nesting)
        # e.g. {"preset": {"name1": {...}, "name2": {...}}}
        has_nested = any(isinstance(v, dict) for v in section_value.values())

        if not has_nested:
            # Simple [section] with scalar values
            if lines:
                lines.append("")
            lines.append(f"[{section}]")
            for key, value in section_value.items():
                lines.append(f"{key} = {_format_value(value)}")
        else:
            # Two-level nesting: [section.name]
            for sub_name, sub_values in section_value.items():
                if lines:
                    lines.append("")
                lines.append(f"[{section}.{sub_name}]")
                if isinstance(sub_values, dict):
                    for key, value in sub_values.items():
                        lines.append(f"{key} = {_format_value(value)}")

    return "\n".join(lines) + ("\n" if lines else "")


def _resolve_config_path(config_path: Path | None) -> Path:
    """Return the config path to use for preset operations.

    When config_path is None, defaults to ~/.imggenrc.
    """
    if config_path is not None:
        return Path(config_path)
    return Path.home() / _CONFIG_FILENAME


def load_config(config_path: Path | None = None) -> dict:
    """Load config from file and return merged [defaults] values.

    Priority: explicit path > ./.imggenrc > ~/.imggenrc > empty dict.
    If a file does not exist or has no [defaults] section, it contributes
    nothing to the result (no error is raised).

    Args:
        config_path: Optional explicit path to a config file. When supplied,
            auto-discovery is skipped and only this file is used.

    Returns:
        A dict of config key/value pairs from the [defaults] section.

    Raises:
        ValueError: If any located config file contains invalid TOML.
    """
    if config_path is not None:
        return _parse_toml_file(Path(config_path))

    # Auto-discovery: start with home, overlay local (local wins on conflicts)
    home_cfg = Path.home() / _CONFIG_FILENAME
    local_cfg = Path.cwd() / _CONFIG_FILENAME

    merged: dict = {}
    merged.update(_parse_toml_file(home_cfg))
    merged.update(_parse_toml_file(local_cfg))
    return merged


def get_default(config: dict, key: str, fallback):
    """Return config[key] if present, else fallback.

    Uses explicit key presence check so falsy values (False, 0, "")
    are returned correctly rather than being replaced by the fallback.

    Args:
        config: Config dict returned by load_config().
        key: Config key name (e.g. 'theme', 'scale').
        fallback: Value to return when key is not present in config.

    Returns:
        The config value for key, or fallback if absent.
    """
    if key in config:
        return config[key]
    return fallback


def load_preset(name: str, config_path: Path | None = None) -> dict:
    """Load a named preset from config. Returns {} if preset doesn't exist.

    Args:
        name: The preset name (key under [preset.*]).
        config_path: Path to config file. Defaults to ~/.imggenrc.

    Returns:
        Dict of preset values, or {} if not found.
    """
    path = _resolve_config_path(config_path)
    data = _parse_toml_full(path)
    presets = data.get("preset", {})
    return dict(presets.get(name, {}))


def save_preset(name: str, values: dict, config_path: Path | None = None) -> None:
    """Save a named preset to config file. Creates file if it doesn't exist.

    Only non-None values are saved.

    Args:
        name: The preset name.
        values: Dict of option_name → value. None values are skipped.
        config_path: Path to config file. Defaults to ~/.imggenrc.
    """
    path = _resolve_config_path(config_path)

    # Read existing full config structure
    existing = _parse_toml_full(path)

    # Ensure preset section exists
    existing_presets: dict = dict(existing.get("preset", {}))

    # Filter out None values
    clean_values = {k: v for k, v in values.items() if v is not None}

    # Replace (not merge) the named preset
    existing_presets[name] = clean_values

    # Build updated structure, preserving all non-preset sections
    updated: dict = {}
    for key, val in existing.items():
        if key != "preset":
            updated[key] = val
    updated["preset"] = existing_presets

    # Write to file
    toml_str = _write_toml(updated)
    path.write_text(toml_str, encoding="utf-8")


def list_presets(config_path: Path | None = None) -> dict[str, dict]:
    """Return all presets as {name: {key: value}} dict.

    Args:
        config_path: Path to config file. Defaults to ~/.imggenrc.

    Returns:
        Dict of preset name → preset values dict.
    """
    path = _resolve_config_path(config_path)
    data = _parse_toml_full(path)
    raw_presets = data.get("preset", {})
    return {name: dict(vals) for name, vals in raw_presets.items()}


def delete_preset(name: str, config_path: Path | None = None) -> bool:
    """Delete a named preset. Returns True if deleted, False if not found.

    Args:
        name: The preset name to delete.
        config_path: Path to config file. Defaults to ~/.imggenrc.

    Returns:
        True if the preset was found and deleted, False otherwise.
    """
    path = _resolve_config_path(config_path)
    existing = _parse_toml_full(path)

    presets: dict = dict(existing.get("preset", {}))
    if name not in presets:
        return False

    new_presets = {k: v for k, v in presets.items() if k != name}

    # Build updated structure
    updated: dict = {}
    for key, val in existing.items():
        if key != "preset":
            updated[key] = val
    if new_presets:
        updated["preset"] = new_presets

    toml_str = _write_toml(updated)
    path.write_text(toml_str, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# LevelUp multi-account configuration
# ---------------------------------------------------------------------------

@dataclass
class AccountConfig:
    """Configuration for a single publishing account."""

    name: str
    platforms: list[str]   # e.g. ["threads", "x", "instagram"]
    publish_time: str       # "HH:MM" format
    color_mood: str         # e.g. "dark_tech" | "warm_earth" | "clean_light"
    prompt_file: str        # e.g. "prompts/account_a.txt"
    tone: str               # Account style description


class LevelUpConfig:
    """Load LevelUp multi-account configuration from accounts.toml.

    Default config path is ~/.imggen/accounts.toml.
    """

    def __init__(self, config_path: str = "~/.imggen/accounts.toml"):
        self.config_path = Path(config_path).expanduser()
        self._accounts: dict[str, AccountConfig] = {}
        self._load()

    def _load(self) -> None:
        """Load and parse accounts.toml, populating self._accounts."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")

        with open(self.config_path, 'rb') as f:
            config = tomllib.load(f)

        for account_id, account_data in config.get('account', {}).items():
            self._accounts[account_id] = AccountConfig(**account_data)

    def get_account(self, account_type: str) -> AccountConfig:
        """Retrieve account config by type identifier (A, B, or C).

        Args:
            account_type: The account identifier string.

        Returns:
            The matching AccountConfig.

        Raises:
            ValueError: If no account with that type exists.
        """
        if account_type not in self._accounts:
            raise ValueError(f"Unknown account type: {account_type}")
        return self._accounts[account_type]

    def list_accounts(self) -> dict[str, AccountConfig]:
        """Return a copy of all configured accounts keyed by type."""
        return self._accounts.copy()

    def save_account(self, account_type: str, updates: dict) -> AccountConfig:
        """Update one account's settings and write back to accounts.toml.

        Only provided fields in *updates* are changed; others are preserved.

        Args:
            account_type: The account identifier (A, B, C).
            updates: Dict with any subset of AccountConfig fields to update.
                     Allowed keys: name, platforms, publish_time, color_mood,
                                   tone, prompt_file.

        Returns:
            The updated AccountConfig.

        Raises:
            ValueError: If account_type is unknown.
        """
        if account_type not in self._accounts:
            raise ValueError(f"Unknown account type: {account_type}")

        current = self._accounts[account_type]
        allowed_fields = {"name", "platforms", "publish_time", "color_mood", "tone", "prompt_file"}
        filtered = {k: v for k, v in updates.items() if k in allowed_fields and v is not None}

        # Build new AccountConfig by merging current with filtered updates
        from dataclasses import asdict, replace as dc_replace
        updated = dc_replace(current, **filtered)
        self._accounts[account_type] = updated

        # Write updated config back to TOML
        self._save()

        return updated

    def _save(self) -> None:
        """Write the current accounts to accounts.toml using _write_toml."""
        account_data: dict = {}
        for acct_id, acct in self._accounts.items():
            account_data[acct_id] = {
                "name": acct.name,
                "platforms": acct.platforms,
                "publish_time": acct.publish_time,
                "color_mood": acct.color_mood,
                "prompt_file": acct.prompt_file,
                "tone": acct.tone,
            }

        # Build TOML manually for the [account.X] structure
        lines: list[str] = []
        for acct_id, fields in account_data.items():
            if lines:
                lines.append("")
            lines.append(f"[account.{acct_id}]")
            for key, value in fields.items():
                if isinstance(value, list):
                    items = ", ".join(f'"{v}"' for v in value)
                    lines.append(f'{key} = [{items}]')
                elif isinstance(value, bool):
                    lines.append(f'{key} = {"true" if value else "false"}')
                elif isinstance(value, str):
                    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
                    lines.append(f'{key} = "{escaped}"')
                else:
                    lines.append(f'{key} = {value}')

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
