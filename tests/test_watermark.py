"""
tests/test_watermark.py - TDD tests for watermark / personal branding (v1.8).

RED phase: all tests written before implementation.
"""

import base64
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_data():
    return {
        "title": "Test Article",
        "key_points": [
            {"emoji": "🔑", "text": "First point"},
            {"emoji": "💡", "text": "Second point"},
        ],
        "source": "https://example.com",
        "theme_suggestion": "dark",
    }


@pytest.fixture
def png_file(tmp_path):
    """Minimal valid 1×1 PNG (67 bytes)."""
    png_bytes = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk length + type
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # 8-bit RGB
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x00, 0x02, 0x00, 0x01, 0xE2, 0x21, 0xBC,
        0x33, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
        0x44, 0xAE, 0x42, 0x60, 0x82,
    ])
    p = tmp_path / "logo.png"
    p.write_bytes(png_bytes)
    return p


@pytest.fixture
def svg_file(tmp_path):
    svg_content = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40"/></svg>'
    p = tmp_path / "logo.svg"
    p.write_text(svg_content, encoding="utf-8")
    return p


@pytest.fixture
def jpeg_file(tmp_path):
    """Minimal JPEG-like bytes (enough for our extension-based detection)."""
    # Just a file with .jpg extension and some bytes
    p = tmp_path / "logo.jpg"
    p.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 10)
    return p


# ---------------------------------------------------------------------------
# load_watermark_data tests
# ---------------------------------------------------------------------------

class TestLoadWatermarkData:
    """Unit tests for load_watermark_data()."""

    def test_returns_string(self, png_file):
        from src.renderer import load_watermark_data
        result = load_watermark_data(png_file)
        assert isinstance(result, str)

    def test_returns_data_uri_prefix(self, png_file):
        from src.renderer import load_watermark_data
        result = load_watermark_data(png_file)
        assert result.startswith("data:image/")

    def test_png_mime_type(self, png_file):
        from src.renderer import load_watermark_data
        result = load_watermark_data(png_file)
        assert result.startswith("data:image/png;base64,")

    def test_svg_mime_type(self, svg_file):
        from src.renderer import load_watermark_data
        result = load_watermark_data(svg_file)
        assert result.startswith("data:image/svg+xml;base64,")

    def test_jpeg_mime_type_jpg_extension(self, jpeg_file):
        from src.renderer import load_watermark_data
        result = load_watermark_data(jpeg_file)
        assert result.startswith("data:image/jpeg;base64,")

    def test_jpeg_mime_type_jpeg_extension(self, tmp_path):
        from src.renderer import load_watermark_data
        p = tmp_path / "photo.jpeg"
        p.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 10)
        result = load_watermark_data(p)
        assert result.startswith("data:image/jpeg;base64,")

    def test_unknown_extension_raises_value_error(self, tmp_path):
        from src.renderer import load_watermark_data
        p = tmp_path / "logo.bmp"
        p.write_bytes(b"BM" + b"\x00" * 20)
        with pytest.raises(ValueError, match="Unsupported watermark file type"):
            load_watermark_data(p)

    def test_base64_content_is_correct(self, png_file):
        from src.renderer import load_watermark_data
        result = load_watermark_data(png_file)
        prefix = "data:image/png;base64,"
        encoded_part = result[len(prefix):]
        # Must be decodable base64
        decoded = base64.b64decode(encoded_part)
        assert decoded == png_file.read_bytes()

    def test_raises_file_not_found_for_missing_file(self, tmp_path):
        from src.renderer import load_watermark_data
        missing = tmp_path / "nonexistent.png"
        with pytest.raises(FileNotFoundError):
            load_watermark_data(missing)

    def test_accepts_path_object(self, png_file):
        from src.renderer import load_watermark_data
        # Path object (not string)
        result = load_watermark_data(Path(png_file))
        assert result.startswith("data:image/png;base64,")

    def test_accepts_string_path(self, png_file):
        from src.renderer import load_watermark_data
        result = load_watermark_data(str(png_file))
        assert result.startswith("data:image/png;base64,")


# ---------------------------------------------------------------------------
# render_card watermark parameter tests
# ---------------------------------------------------------------------------

class TestRenderCardWatermarkSignature:
    """render_card() must accept the new watermark keyword arguments."""

    def test_accepts_watermark_data_kwarg(self, sample_data):
        import inspect
        from src.renderer import render_card
        sig = inspect.signature(render_card)
        assert "watermark_data" in sig.parameters

    def test_accepts_watermark_position_kwarg(self, sample_data):
        import inspect
        from src.renderer import render_card
        sig = inspect.signature(render_card)
        assert "watermark_position" in sig.parameters

    def test_accepts_watermark_opacity_kwarg(self, sample_data):
        import inspect
        from src.renderer import render_card
        sig = inspect.signature(render_card)
        assert "watermark_opacity" in sig.parameters

    def test_accepts_brand_name_kwarg(self, sample_data):
        import inspect
        from src.renderer import render_card
        sig = inspect.signature(render_card)
        assert "brand_name" in sig.parameters

    def test_watermark_data_default_is_none(self):
        import inspect
        from src.renderer import render_card
        sig = inspect.signature(render_card)
        assert sig.parameters["watermark_data"].default is None

    def test_watermark_position_default_is_bottom_right(self):
        import inspect
        from src.renderer import render_card
        sig = inspect.signature(render_card)
        assert sig.parameters["watermark_position"].default == "bottom-right"

    def test_watermark_opacity_default_is_0_8(self):
        import inspect
        from src.renderer import render_card
        sig = inspect.signature(render_card)
        assert sig.parameters["watermark_opacity"].default == 0.8

    def test_brand_name_default_is_none(self):
        import inspect
        from src.renderer import render_card
        sig = inspect.signature(render_card)
        assert sig.parameters["brand_name"].default is None


class TestRenderCardNoWatermark:
    """When no watermark args are given, the overlay div element is not rendered."""

    @pytest.mark.parametrize("theme", ["dark", "light", "gradient"])
    def test_no_watermark_overlay_div_in_output(self, sample_data, theme):
        from src.renderer import render_card
        html = render_card(sample_data, theme=theme)
        # The div element must not be present (CSS class in <style> is fine)
        assert 'class="watermark-overlay' not in html

    def test_backward_compat_no_extra_args(self, sample_data):
        from src.renderer import render_card
        html = render_card(sample_data, theme="dark", format="story")
        assert isinstance(html, str) and len(html) > 100
        assert 'class="watermark-overlay' not in html


class TestRenderCardWithWatermarkData:
    """Watermark image data URI is injected into the HTML."""

    FAKE_DATA_URI = "data:image/png;base64,abc123"

    @pytest.mark.parametrize("theme", ["dark", "light", "gradient"])
    def test_watermark_overlay_class_present(self, sample_data, theme):
        from src.renderer import render_card
        html = render_card(sample_data, theme=theme, watermark_data=self.FAKE_DATA_URI)
        assert 'class="watermark-overlay' in html

    @pytest.mark.parametrize("theme", ["dark", "light", "gradient"])
    def test_watermark_img_src_present(self, sample_data, theme):
        from src.renderer import render_card
        html = render_card(sample_data, theme=theme, watermark_data=self.FAKE_DATA_URI)
        assert self.FAKE_DATA_URI in html

    @pytest.mark.parametrize("theme", ["dark", "light", "gradient"])
    def test_watermark_img_tag_present(self, sample_data, theme):
        from src.renderer import render_card
        html = render_card(sample_data, theme=theme, watermark_data=self.FAKE_DATA_URI)
        assert "<img" in html
        assert "watermark-img" in html


class TestRenderCardWithBrandName:
    """Brand name text is injected into the HTML."""

    @pytest.mark.parametrize("theme", ["dark", "light", "gradient"])
    def test_brand_name_text_present(self, sample_data, theme):
        from src.renderer import render_card
        html = render_card(sample_data, theme=theme, brand_name="@test")
        assert "@test" in html

    @pytest.mark.parametrize("theme", ["dark", "light", "gradient"])
    def test_watermark_overlay_class_present_with_brand_name(self, sample_data, theme):
        from src.renderer import render_card
        html = render_card(sample_data, theme=theme, brand_name="@myhandle")
        assert 'class="watermark-overlay' in html

    @pytest.mark.parametrize("theme", ["dark", "light", "gradient"])
    def test_watermark_text_class_present(self, sample_data, theme):
        from src.renderer import render_card
        html = render_card(sample_data, theme=theme, brand_name="@user")
        assert "watermark-text" in html

    def test_brand_name_with_special_chars(self, sample_data):
        """HTML escaping should not break rendering."""
        from src.renderer import render_card
        html = render_card(sample_data, theme="dark", brand_name="@user_name")
        assert "@user_name" in html


class TestRenderCardWatermarkPosition:
    """Position variant CSS class is applied to the overlay div."""

    @pytest.mark.parametrize("position,expected_class", [
        ("top-left", "watermark-top-left"),
        ("top-right", "watermark-top-right"),
        ("bottom-left", "watermark-bottom-left"),
        ("bottom-right", "watermark-bottom-right"),
    ])
    def test_position_class_in_html(self, sample_data, position, expected_class):
        from src.renderer import render_card
        html = render_card(
            sample_data,
            theme="dark",
            watermark_data="data:image/png;base64,abc",
            watermark_position=position,
        )
        assert expected_class in html

    def test_default_position_is_bottom_right(self, sample_data):
        from src.renderer import render_card
        html = render_card(
            sample_data,
            theme="dark",
            watermark_data="data:image/png;base64,abc",
        )
        assert "watermark-bottom-right" in html


class TestRenderCardWatermarkOpacity:
    """Opacity value is rendered into the style attribute."""

    @pytest.mark.parametrize("opacity", [0.0, 0.5, 0.8, 1.0])
    def test_opacity_in_style_attr(self, sample_data, opacity):
        from src.renderer import render_card
        html = render_card(
            sample_data,
            theme="dark",
            watermark_data="data:image/png;base64,abc",
            watermark_opacity=opacity,
        )
        assert f"opacity: {opacity}" in html or f"opacity:{opacity}" in html

    def test_opacity_applied_to_brand_name_as_well(self, sample_data):
        from src.renderer import render_card
        html = render_card(
            sample_data,
            theme="dark",
            brand_name="@test",
            watermark_opacity=0.5,
        )
        assert "0.5" in html


class TestRenderCardBothWatermarks:
    """When both watermark_data and brand_name are set, both appear."""

    @pytest.mark.parametrize("theme", ["dark", "light", "gradient"])
    def test_both_present(self, sample_data, theme):
        from src.renderer import render_card
        html = render_card(
            sample_data,
            theme=theme,
            watermark_data="data:image/png;base64,abc",
            brand_name="@combo",
        )
        assert "watermark-img" in html
        assert "@combo" in html
        assert 'class="watermark-overlay' in html


class TestRenderCardWatermarkCSS:
    """Watermark CSS classes are defined in the style block."""

    @pytest.mark.parametrize("theme", ["dark", "light", "gradient"])
    def test_watermark_overlay_css_defined(self, sample_data, theme):
        from src.renderer import render_card
        # CSS must be defined regardless of whether watermark is used
        html = render_card(sample_data, theme=theme, brand_name="@x")
        assert ".watermark-overlay" in html

    @pytest.mark.parametrize("theme", ["dark", "light", "gradient"])
    def test_position_absolute_in_css(self, sample_data, theme):
        from src.renderer import render_card
        html = render_card(sample_data, theme=theme, brand_name="@x")
        assert "position: absolute" in html or "position:absolute" in html
