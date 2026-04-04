"""
tests/test_screenshotter.py - Unit tests for screenshotter module (v1.5 multi-format)

TDD: RED phase - these tests define expected behavior before implementation.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# FORMAT_DIMENSIONS tests
# ---------------------------------------------------------------------------

class TestFormatDimensions:
    def test_all_four_formats_exist(self):
        from src.screenshotter import FORMAT_DIMENSIONS
        assert set(FORMAT_DIMENSIONS.keys()) == {"story", "square", "landscape", "twitter"}

    def test_story_dimensions(self):
        from src.screenshotter import FORMAT_DIMENSIONS
        assert FORMAT_DIMENSIONS["story"] == (430, 764)

    def test_square_dimensions(self):
        from src.screenshotter import FORMAT_DIMENSIONS
        assert FORMAT_DIMENSIONS["square"] == (430, 430)

    def test_landscape_dimensions(self):
        from src.screenshotter import FORMAT_DIMENSIONS
        assert FORMAT_DIMENSIONS["landscape"] == (430, 242)

    def test_twitter_dimensions(self):
        from src.screenshotter import FORMAT_DIMENSIONS
        assert FORMAT_DIMENSIONS["twitter"] == (430, 215)

    def test_all_dimensions_are_positive_integers(self):
        from src.screenshotter import FORMAT_DIMENSIONS
        for fmt, (w, h) in FORMAT_DIMENSIONS.items():
            assert isinstance(w, int) and w > 0, f"{fmt} width must be positive int"
            assert isinstance(h, int) and h > 0, f"{fmt} height must be positive int"


# ---------------------------------------------------------------------------
# take_screenshot signature tests
# ---------------------------------------------------------------------------

class TestTakeScreenshotSignature:
    """Verify the public API signature supports new parameters."""

    def test_accepts_format_parameter(self, tmp_path):
        """take_screenshot should accept a format kwarg without error at call site."""
        import inspect
        from src.screenshotter import take_screenshot
        sig = inspect.signature(take_screenshot)
        params = sig.parameters
        assert "format" in params, "take_screenshot must accept 'format' parameter"

    def test_accepts_scale_parameter(self, tmp_path):
        import inspect
        from src.screenshotter import take_screenshot
        sig = inspect.signature(take_screenshot)
        params = sig.parameters
        assert "scale" in params, "take_screenshot must accept 'scale' parameter"

    def test_format_default_is_story(self):
        import inspect
        from src.screenshotter import take_screenshot
        sig = inspect.signature(take_screenshot)
        assert sig.parameters["format"].default == "story"

    def test_scale_default_is_2(self):
        import inspect
        from src.screenshotter import take_screenshot
        sig = inspect.signature(take_screenshot)
        assert sig.parameters["scale"].default == 2


# ---------------------------------------------------------------------------
# Viewport / clip correctness tests (mocked Playwright)
# ---------------------------------------------------------------------------

def _make_playwright_mocks():
    """
    Build a nested mock tree that mimics the playwright async_api surface.

    Returns:
        (mock_async_playwright_callable, mock_browser, mock_browser_context, mock_page)

    The async_playwright mock is a plain MagicMock callable that returns an
    async context manager.  When entered it yields mock_playwright_instance
    whose .chromium.launch() returns mock_browser.  mock_browser.new_context()
    returns mock_browser_context, and mock_browser_context.new_page() returns
    mock_page.
    """
    mock_page = AsyncMock()

    mock_browser_context = AsyncMock()
    mock_browser_context.new_page = AsyncMock(return_value=mock_page)

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_browser_context)
    mock_browser.close = AsyncMock()

    mock_chromium = AsyncMock()
    mock_chromium.launch = AsyncMock(return_value=mock_browser)

    mock_playwright_instance = MagicMock()
    mock_playwright_instance.chromium = mock_chromium

    # The CM that 'async with async_playwright() as p' uses
    mock_cm = AsyncMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_playwright_instance)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    # async_playwright itself: a plain callable returning the CM
    mock_async_playwright_callable = MagicMock(return_value=mock_cm)

    return mock_async_playwright_callable, mock_browser, mock_browser_context, mock_page


class TestTakeScreenshotViewport:
    """Confirm correct viewport dimensions and device_scale_factor are used."""

    def _run_take_screenshot(self, html, path, **kwargs):
        """Helper: patch playwright and run take_screenshot synchronously."""
        mock_ap, mock_browser, mock_browser_context, mock_page = _make_playwright_mocks()

        # Make the output file appear to exist so the post-check passes
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

        with patch("src.screenshotter.async_playwright", mock_ap):
            from src.screenshotter import take_screenshot
            take_screenshot(html, path, **kwargs)

        # Return browser and browser_context so tests can inspect call_args
        return mock_browser, mock_browser_context, mock_page

    # -- story (default) --
    def test_story_viewport_width_height(self, tmp_path):
        out = tmp_path / "out.png"
        mock_browser, _, _ = self._run_take_screenshot("<html></html>", out, format="story")
        call_kwargs = mock_browser.new_context.call_args[1]
        assert call_kwargs["viewport"]["width"] == 430
        assert call_kwargs["viewport"]["height"] == 764

    def test_story_clip_dimensions(self, tmp_path):
        out = tmp_path / "out.png"
        _, _, mock_page = self._run_take_screenshot("<html></html>", out, format="story")
        clip = mock_page.screenshot.call_args[1]["clip"]
        assert clip["width"] == 430
        assert clip["height"] == 764

    # -- square --
    def test_square_viewport(self, tmp_path):
        out = tmp_path / "out.png"
        mock_browser, _, mock_page = self._run_take_screenshot("<html></html>", out, format="square")
        vp = mock_browser.new_context.call_args[1]["viewport"]
        clip = mock_page.screenshot.call_args[1]["clip"]
        assert vp["width"] == 430 and vp["height"] == 430
        assert clip["width"] == 430 and clip["height"] == 430

    # -- landscape --
    def test_landscape_viewport(self, tmp_path):
        out = tmp_path / "out.png"
        mock_browser, _, mock_page = self._run_take_screenshot("<html></html>", out, format="landscape")
        vp = mock_browser.new_context.call_args[1]["viewport"]
        clip = mock_page.screenshot.call_args[1]["clip"]
        assert vp["width"] == 430 and vp["height"] == 242
        assert clip["width"] == 430 and clip["height"] == 242

    # -- twitter --
    def test_twitter_viewport(self, tmp_path):
        out = tmp_path / "out.png"
        mock_browser, _, mock_page = self._run_take_screenshot("<html></html>", out, format="twitter")
        vp = mock_browser.new_context.call_args[1]["viewport"]
        clip = mock_page.screenshot.call_args[1]["clip"]
        assert vp["width"] == 430 and vp["height"] == 215
        assert clip["width"] == 430 and clip["height"] == 215

    # -- scale=1 --
    def test_scale_1_device_scale_factor(self, tmp_path):
        out = tmp_path / "out.png"
        mock_browser, _, _ = self._run_take_screenshot("<html></html>", out, scale=1)
        dsf = mock_browser.new_context.call_args[1]["device_scale_factor"]
        assert dsf == 1

    # -- scale=2 (default) --
    def test_scale_2_device_scale_factor(self, tmp_path):
        out = tmp_path / "out.png"
        mock_browser, _, _ = self._run_take_screenshot("<html></html>", out, scale=2)
        dsf = mock_browser.new_context.call_args[1]["device_scale_factor"]
        assert dsf == 2

    def test_default_scale_is_retina(self, tmp_path):
        """Calling without scale kwarg should default to 2x."""
        out = tmp_path / "out.png"
        mock_browser, _, _ = self._run_take_screenshot("<html></html>", out)
        dsf = mock_browser.new_context.call_args[1]["device_scale_factor"]
        assert dsf == 2

    def test_default_format_matches_story(self, tmp_path):
        """Calling without format kwarg should default to story (1080x1920)."""
        out = tmp_path / "out.png"
        mock_browser, _, _ = self._run_take_screenshot("<html></html>", out)
        vp = mock_browser.new_context.call_args[1]["viewport"]
        assert vp["width"] == 430 and vp["height"] == 764

    # -- invalid format --
    def test_invalid_format_raises_value_error(self, tmp_path):
        out = tmp_path / "out.png"
        out.touch()
        mock_ap, _, _, _ = _make_playwright_mocks()
        with patch("src.screenshotter.async_playwright", mock_ap):
            from src.screenshotter import take_screenshot
            with pytest.raises((ValueError, RuntimeError)):
                take_screenshot("<html></html>", out, format="panorama")

    # -- webp screenshot type --
    def test_webp_output_path_uses_webp_extension(self, tmp_path):
        """When output path ends in .webp the screenshot type should be webp."""
        out = tmp_path / "out.webp"
        out.touch()
        mock_ap, _, _, mock_page = _make_playwright_mocks()
        with patch("src.screenshotter.async_playwright", mock_ap):
            from src.screenshotter import take_screenshot
            take_screenshot("<html></html>", out)
        call_kwargs = mock_page.screenshot.call_args[1]
        assert call_kwargs.get("type") == "webp"

    def test_png_output_path_uses_png_type(self, tmp_path):
        out = tmp_path / "out.png"
        out.touch()
        mock_ap, _, _, mock_page = _make_playwright_mocks()
        with patch("src.screenshotter.async_playwright", mock_ap):
            from src.screenshotter import take_screenshot
            take_screenshot("<html></html>", out)
        call_kwargs = mock_page.screenshot.call_args[1]
        assert call_kwargs.get("type") == "png"
