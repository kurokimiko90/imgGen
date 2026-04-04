"""
tests/test_export_html.py - Tests for HTML export endpoint.

TDD: RED phase first.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from web.api import app
    return TestClient(app)


class TestExportHtmlEndpoint:
    """Test GET /api/export/html/{gen_id}"""

    @patch("web.api.get_generation_by_id")
    @patch("web.api.render_and_capture")
    def test_returns_html_content(self, mock_render, mock_get_gen, client):
        from src.renderer import render_card

        extracted = {
            "title": "Test Article",
            "key_points": [
                {"text": "Point 1"},
                {"text": "Point 2"},
                {"text": "Point 3"},
            ],
            "source": "https://example.com",
            "theme_suggestion": "dark",
        }
        mock_get_gen.return_value = {
            "id": 1,
            "theme": "dark",
            "format": "story",
            "extracted_data": json.dumps(extracted),
        }

        resp = client.get("/api/export/html/1")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "content-disposition" in resp.headers
        assert "imggen_1.html" in resp.headers["content-disposition"]

    @patch("web.api.get_generation_by_id")
    def test_404_for_missing_generation(self, mock_get_gen, client):
        mock_get_gen.return_value = None

        resp = client.get("/api/export/html/99999")
        assert resp.status_code == 404

    @patch("web.api.get_generation_by_id")
    def test_400_for_no_extracted_data(self, mock_get_gen, client):
        mock_get_gen.return_value = {
            "id": 1,
            "theme": "dark",
            "format": "story",
            "extracted_data": None,
        }

        resp = client.get("/api/export/html/1")
        assert resp.status_code == 400


class TestGenerateWithExtractionConfig:
    """Test that /api/generate accepts extraction_config."""

    def test_generate_request_accepts_extraction_config(self):
        from web.api import GenerateRequest

        req = GenerateRequest(
            text="Test article content",
            extraction_config={
                "language": "en",
                "tone": "casual",
                "max_points": 4,
                "min_points": 2,
                "title_max_chars": 20,
                "point_max_chars": 80,
                "custom_instructions": "Be brief",
            },
        )
        assert req.extraction_config is not None
        assert req.extraction_config.language == "en"

    def test_generate_request_extraction_config_optional(self):
        from web.api import GenerateRequest

        req = GenerateRequest(text="Test article content")
        assert req.extraction_config is None
