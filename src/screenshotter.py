"""
screenshotter.py - Playwright screenshot module

Takes screenshots of HTML content using Playwright with Chromium.
Outputs 1080x1920px PNG images at 2x device scale (retina quality).
"""

import asyncio
from pathlib import Path


VIEWPORT_WIDTH = 1080
VIEWPORT_HEIGHT = 1920
DEVICE_SCALE_FACTOR = 2


async def _take_screenshot_async(html_content: str, output_path: Path) -> None:
    """
    Async implementation of screenshot capture.

    Args:
        html_content: Full HTML string to render
        output_path: Absolute path where PNG will be saved
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
                device_scale_factor=DEVICE_SCALE_FACTOR,
            )
            page = await context.new_page()

            # Set content directly - more reliable than file:// URLs
            await page.set_content(html_content, wait_until="networkidle")

            # Ensure fonts and images have loaded
            await page.wait_for_timeout(500)

            await page.screenshot(
                path=str(output_path),
                type="png",
                clip={
                    "x": 0,
                    "y": 0,
                    "width": VIEWPORT_WIDTH,
                    "height": VIEWPORT_HEIGHT,
                },
            )
        finally:
            await browser.close()


def take_screenshot(html_content: str, output_path: str | Path) -> Path:
    """
    Take a screenshot of HTML content and save as PNG.

    Args:
        html_content: Full HTML string to render
        output_path: Path where PNG will be saved

    Returns:
        Path to the saved PNG file

    Raises:
        RuntimeError: If screenshot capture fails
        OSError: If output directory cannot be created
    """
    output_path = Path(output_path).resolve()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        asyncio.run(_take_screenshot_async(html_content, output_path))
    except Exception as e:
        raise RuntimeError(
            f"Failed to capture screenshot: {e}\n"
            "Ensure Playwright Chromium is installed: playwright install chromium"
        ) from e

    if not output_path.exists():
        raise RuntimeError(f"Screenshot was not created at: {output_path}")

    return output_path
