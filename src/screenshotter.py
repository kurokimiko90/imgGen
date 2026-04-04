"""
screenshotter.py - Playwright screenshot module

Takes screenshots of HTML content using Playwright with Chromium.
Supports multiple output formats and resolution scales.
"""

import asyncio
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:  # pragma: no cover - optional at import time; checked at runtime
    async_playwright = None  # type: ignore[assignment]


FORMAT_DIMENSIONS: dict[str, tuple[int, int]] = {
    "story": (430, 764),
    "square": (430, 430),
    "landscape": (430, 242),
    "twitter": (430, 215),
}

# Keep legacy constants for any external callers that may reference them.
VIEWPORT_WIDTH = FORMAT_DIMENSIONS["story"][0]
VIEWPORT_HEIGHT = FORMAT_DIMENSIONS["story"][1]
DEVICE_SCALE_FACTOR = 2


async def _take_screenshot_async(
    html_content: str,
    output_path: Path,
    width: int,
    height: int,
    scale: int,
) -> None:
    """
    Async implementation of screenshot capture.

    Args:
        html_content: Full HTML string to render
        output_path: Absolute path where the image will be saved
        width: Viewport width in pixels
        height: Viewport height in pixels
        scale: Device scale factor (1 or 2)
    """
    # Determine image type from the output path extension
    ext = output_path.suffix.lower()
    image_type = "webp" if ext == ".webp" else "png"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=scale,
            )
            page = await context.new_page()

            # Set content directly - more reliable than file:// URLs
            await page.set_content(html_content, wait_until="networkidle")

            # Ensure fonts and images have loaded
            # 850ms: covers up to 5-point stagger (5×0.08s delay + 0.32s duration = 0.72s) plus buffer
            await page.wait_for_timeout(850)

            await page.screenshot(
                path=str(output_path),
                type=image_type,
                clip={
                    "x": 0,
                    "y": 0,
                    "width": width,
                    "height": height,
                },
            )
        finally:
            await browser.close()


def take_screenshot(
    html_content: str,
    output_path: "str | Path",
    format: str = "story",
    scale: int = 2,
) -> Path:
    """
    Take a screenshot of HTML content and save as PNG or WebP.

    Args:
        html_content: Full HTML string to render
        output_path: Path where the image will be saved
        format: Output format name - one of 'story', 'square', 'landscape', 'twitter'
        scale: Device pixel ratio - 1 for standard, 2 for Retina

    Returns:
        Path to the saved image file

    Raises:
        ValueError: If format is not a recognised format name
        RuntimeError: If screenshot capture fails
        OSError: If output directory cannot be created

    Note:
        Uses asyncio.run() internally. Will raise RuntimeError if called from
        within an already-running event loop (e.g., inside an async test or
        async web framework). In that case, await _take_screenshot_async directly.
    """
    if format not in FORMAT_DIMENSIONS:
        raise ValueError(
            f"Invalid format '{format}'. Must be one of: {', '.join(sorted(FORMAT_DIMENSIONS))}"
        )

    width, height = FORMAT_DIMENSIONS[format]
    output_path = Path(output_path).resolve()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        asyncio.run(
            _take_screenshot_async(html_content, output_path, width, height, scale)
        )
    except Exception as e:
        raise RuntimeError(
            f"Failed to capture screenshot: {e}\n"
            "Ensure Playwright Chromium is installed: playwright install chromium"
        ) from e

    if not output_path.exists():
        raise RuntimeError(f"Screenshot was not created at: {output_path}")

    return output_path
