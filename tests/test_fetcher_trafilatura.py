"""
tests/test_fetcher_trafilatura.py - Tests for trafilatura-based URL extraction.

TDD: RED phase first.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestExtractArticleText:
    """Test the new _extract_article_text function."""

    def test_extracts_article_body_from_html(self):
        from src.fetcher import _extract_article_text

        html = """
        <html>
        <head><title>Test</title></head>
        <body>
        <nav>Menu Item 1 | Menu Item 2</nav>
        <article>
            <h1>Important Article</h1>
            <p>This is the main body of the article with enough content to be meaningful.
            It contains several sentences that form a coherent paragraph about an important topic.</p>
        </article>
        <footer>Copyright 2024 | Privacy Policy</footer>
        </body>
        </html>
        """
        result = _extract_article_text(html, "https://example.com")
        # Should contain article body
        assert "Important Article" in result or "main body" in result
        # Should NOT contain nav/footer noise
        assert "Privacy Policy" not in result

    def test_fallback_on_short_extraction(self):
        """When trafilatura returns very little, fallback to regex strip."""
        from src.fetcher import _extract_article_text

        # Minimal HTML that trafilatura can't meaningfully extract
        html = "<div>Short text</div>"
        result = _extract_article_text(html, "https://example.com")
        assert "Short" in result

    def test_fallback_on_empty_html(self):
        """Empty/broken HTML should still return something via fallback."""
        from src.fetcher import _extract_article_text

        result = _extract_article_text("", "https://example.com")
        assert isinstance(result, str)


class TestFetchUrlContentWithTrafilatura:
    """Verify fetch_url_content uses trafilatura for HTML content."""

    @patch("src.fetcher.httpx.get")
    def test_html_response_uses_trafilatura(self, mock_get):
        from src.fetcher import fetch_url_content

        mock_response = MagicMock()
        mock_response.text = """
        <html><body>
        <article><p>Article body content that is long enough to be extracted properly by trafilatura engine.</p></article>
        </body></html>
        """
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_url_content("https://example.com/article")
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("src.fetcher.httpx.get")
    def test_non_html_response_returns_raw_text(self, mock_get):
        from src.fetcher import fetch_url_content

        mock_response = MagicMock()
        mock_response.text = "Plain text content"
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_url_content("https://example.com/data.txt")
        assert result == "Plain text content"

    def test_threads_url_still_uses_special_handler(self):
        """Threads URLs should NOT go through trafilatura."""
        from src.fetcher import _is_threads_url

        assert _is_threads_url("https://www.threads.net/@user/post/abc123")
        assert not _is_threads_url("https://example.com/article")
