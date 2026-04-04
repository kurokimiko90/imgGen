"""
src/preflight.py - Pre-flight check for content before publishing.

Validates content against platform-specific limits and requirements.
Returns a list of warning strings (empty list = all clear).
"""

from pathlib import Path

from src.content import Content


def preflight_check(content: Content, platforms: list[str]) -> list[str]:
    """Validate *content* against publishing rules for each platform.

    Returns a list of warning strings. An empty list means no issues.
    Warnings prefixed with ``[ERROR]`` are blocking; others are ``[WARNING]``.
    """
    warnings: list[str] = []
    platform_set = {p.lower() for p in platforms}

    # R5 — all platforms: empty title
    if not content.title.strip():
        warnings.append("[ERROR] 標題為空")

    # R6 — all platforms: empty body
    if not content.body.strip():
        warnings.append("[ERROR] 內文為空")

    # R1 — x: body length > 280
    if "x" in platform_set and len(content.body) > 280:
        warnings.append(f"[WARNING] X 字數超限（{len(content.body)} / 280）")

    # R2 — threads: body length > 500
    if "threads" in platform_set and len(content.body) > 500:
        warnings.append(f"[WARNING] Threads 字數超限（{len(content.body)} / 500）")

    # R3 — instagram: no image
    if "instagram" in platform_set and content.image_path is None:
        warnings.append("[ERROR] IG 需要圖片，目前無附圖")

    # R4 — instagram: image path doesn't exist on disk
    elif "instagram" in platform_set and content.image_path is not None:
        if not Path(content.image_path).exists():
            warnings.append("[ERROR] IG 圖片路徑不存在")

    # R7 — linkedin: body length > 3000
    if "linkedin" in platform_set and len(content.body) > 3000:
        warnings.append(f"[WARNING] LinkedIn 字數超限（{len(content.body)} / 3000）")

    return warnings
