"""
clipboard.py - macOS clipboard integration for image files.
"""

import platform
import subprocess
from pathlib import Path


def is_clipboard_supported() -> bool:
    """Return True if running on macOS (clipboard copy is supported)."""
    return platform.system() == "Darwin"


def copy_image_to_clipboard(image_path: Path) -> None:
    """Copy an image file to the macOS clipboard.

    Uses ``osascript`` to set the clipboard contents to a TIFF picture,
    which is universally pasteable on macOS.

    Args:
        image_path: Absolute or relative path to a PNG, WebP, or JPEG image.

    Raises:
        RuntimeError: If the platform is not macOS or the copy command fails.
        FileNotFoundError: If the image file does not exist.
    """
    if not is_clipboard_supported():
        raise RuntimeError("Clipboard copy is only supported on macOS.")

    image_path = Path(image_path).resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    script = (
        f'set the clipboard to '
        f'(read (POSIX file "{image_path}") as TIFF picture)'
    )
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Clipboard copy failed: {result.stderr.strip()}"
        )
