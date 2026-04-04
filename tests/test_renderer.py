"""
tests/test_renderer.py - Unit tests for renderer module (v1.5 multi-format)

TDD: RED phase.
"""

import pytest
from unittest.mock import patch, MagicMock


SAMPLE_DATA = {
    "title": "Test Article",
    "key_points": [
        {"emoji": "🔑", "text": "First point"},
        {"emoji": "💡", "text": "Second point"},
    ],
    "source": "https://example.com",
    "theme_suggestion": "dark",
}


class TestRenderCardSignature:
    def test_accepts_format_parameter(self):
        import inspect
        from src.renderer import render_card
        sig = inspect.signature(render_card)
        assert "format" in sig.parameters, "render_card must accept 'format' parameter"

    def test_format_default_is_story(self):
        import inspect
        from src.renderer import render_card
        sig = inspect.signature(render_card)
        assert sig.parameters["format"].default == "story"


class TestRenderCardFormatPassthrough:
    """Verify format is passed to the Jinja2 template as a variable."""

    def _render(self, theme="dark", fmt="story"):
        from src.renderer import render_card
        return render_card(SAMPLE_DATA, theme=theme, format=fmt)

    def test_render_with_story_format_succeeds(self):
        html = self._render(fmt="story")
        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_with_square_format_succeeds(self):
        html = self._render(fmt="square")
        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_with_landscape_format_succeeds(self):
        html = self._render(fmt="landscape")
        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_with_twitter_format_succeeds(self):
        html = self._render(fmt="twitter")
        assert isinstance(html, str)
        assert len(html) > 0

    def test_format_variable_present_in_rendered_html(self):
        """Templates receive 'format' so CSS classes or data-attrs can use it."""
        html = self._render(fmt="landscape")
        # The template should output the format name somewhere (e.g., data-format or class)
        assert "landscape" in html

    def test_story_format_variable_present(self):
        html = self._render(fmt="story")
        assert "story" in html

    def test_square_format_variable_present(self):
        html = self._render(fmt="square")
        assert "square" in html

    def test_twitter_format_variable_present(self):
        html = self._render(fmt="twitter")
        assert "twitter" in html


class TestRenderCardBackwardCompatibility:
    """Ensure existing call signature still works."""

    def test_render_without_format_uses_story_default(self):
        from src.renderer import render_card
        html = render_card(SAMPLE_DATA, theme="dark")
        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_dark_theme_still_works(self):
        from src.renderer import render_card
        html = render_card(SAMPLE_DATA, theme="dark", format="story")
        assert "dark" in html or len(html) > 100  # basic sanity

    def test_render_light_theme_with_format(self):
        from src.renderer import render_card
        html = render_card(SAMPLE_DATA, theme="light", format="square")
        assert isinstance(html, str)

    def test_render_gradient_theme_with_format(self):
        from src.renderer import render_card
        html = render_card(SAMPLE_DATA, theme="gradient", format="landscape")
        assert isinstance(html, str)

    def test_invalid_theme_still_raises_value_error(self):
        from src.renderer import render_card
        with pytest.raises(ValueError):
            render_card(SAMPLE_DATA, theme="neon", format="story")


class TestRenderCardAllThemesAllFormats:
    """Cross-product: every theme x every format must render successfully."""

    @pytest.mark.parametrize("theme", ["dark", "light", "gradient"])
    @pytest.mark.parametrize("fmt", ["story", "square", "landscape", "twitter"])
    def test_cross_product(self, theme, fmt):
        from src.renderer import render_card
        html = render_card(SAMPLE_DATA, theme=theme, format=fmt)
        assert isinstance(html, str) and len(html) > 50
