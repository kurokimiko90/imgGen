"""
tests/test_extraction_config.py - Tests for ExtractionConfig and prompt templating.

TDD: RED phase first.
"""

import pytest


class TestExtractionConfig:
    """Test the ExtractionConfig dataclass."""

    def test_default_values(self):
        from src.extractor import ExtractionConfig

        config = ExtractionConfig()
        assert config.language == "zh-TW"
        assert config.tone == "professional"
        assert config.max_points == 5
        assert config.min_points == 3
        assert config.title_max_chars == 15
        assert config.point_max_chars == 50
        assert config.custom_instructions == ""

    def test_custom_values(self):
        from src.extractor import ExtractionConfig

        config = ExtractionConfig(
            language="en",
            tone="casual",
            max_points=8,
            min_points=2,
            title_max_chars=30,
            point_max_chars=100,
            custom_instructions="Focus on data",
        )
        assert config.language == "en"
        assert config.tone == "casual"
        assert config.max_points == 8

    def test_is_frozen(self):
        from src.extractor import ExtractionConfig

        config = ExtractionConfig()
        with pytest.raises(AttributeError):
            config.language = "en"


class TestBuildSystemPrompt:
    """Test the _build_system_prompt template function."""

    def test_default_prompt_contains_chinese(self):
        from src.extractor import ExtractionConfig, _build_system_prompt

        prompt = _build_system_prompt(ExtractionConfig())
        assert "繁體中文" in prompt
        assert "15" in prompt  # title_max_chars
        assert "3" in prompt   # min_points
        assert "5" in prompt   # max_points

    def test_english_prompt(self):
        from src.extractor import ExtractionConfig, _build_system_prompt

        config = ExtractionConfig(language="en", title_max_chars=20)
        prompt = _build_system_prompt(config)
        assert "English" in prompt
        assert "20" in prompt

    def test_custom_instructions_included(self):
        from src.extractor import ExtractionConfig, _build_system_prompt

        config = ExtractionConfig(custom_instructions="Include statistics")
        prompt = _build_system_prompt(config)
        assert "Include statistics" in prompt

    def test_custom_instructions_omitted_when_empty(self):
        from src.extractor import ExtractionConfig, _build_system_prompt

        config = ExtractionConfig(custom_instructions="")
        prompt = _build_system_prompt(config)
        assert "附加要求" not in prompt

    def test_tone_description(self):
        from src.extractor import ExtractionConfig, _build_system_prompt

        for tone in ("professional", "casual", "academic", "marketing"):
            config = ExtractionConfig(tone=tone)
            prompt = _build_system_prompt(config)
            assert len(prompt) > 100  # sanity check — prompt is non-trivial

    def test_japanese_language(self):
        from src.extractor import ExtractionConfig, _build_system_prompt

        config = ExtractionConfig(language="ja")
        prompt = _build_system_prompt(config)
        assert "日本語" in prompt


class TestExtractKeyPointsWithConfig:
    """Test that extract_key_points accepts config parameter."""

    def test_signature_accepts_config(self):
        import inspect
        from src.extractor import extract_key_points

        sig = inspect.signature(extract_key_points)
        assert "config" in sig.parameters

    def test_config_none_uses_defaults(self):
        """config=None should behave like the original hardcoded prompt."""
        import inspect
        from src.extractor import extract_key_points

        sig = inspect.signature(extract_key_points)
        param = sig.parameters["config"]
        assert param.default is None


class TestValidateExtractedDataWithConfig:
    """Test that validation uses config's min/max points."""

    def test_validates_with_custom_range(self):
        from src.extractor import ExtractionConfig, _validate_extracted_data

        config = ExtractionConfig(min_points=1, max_points=8)
        # 1 point should be valid with this config
        data = {
            "title": "Test",
            "key_points": [{"text": "Only one point"}],
            "source": "",
            "theme_suggestion": "dark",
        }
        # Should NOT raise
        _validate_extracted_data(data, config=config)

    def test_default_rejects_single_point(self):
        from src.extractor import _validate_extracted_data

        data = {
            "title": "Test",
            "key_points": [{"text": "Only one point"}],
            "source": "",
            "theme_suggestion": "dark",
        }
        with pytest.raises(ValueError, match="key_points"):
            _validate_extracted_data(data)

    def test_custom_config_rejects_too_many(self):
        from src.extractor import ExtractionConfig, _validate_extracted_data

        config = ExtractionConfig(min_points=1, max_points=2)
        data = {
            "title": "Test",
            "key_points": [{"text": "a"}, {"text": "b"}, {"text": "c"}],
            "source": "",
            "theme_suggestion": "dark",
        }
        with pytest.raises(ValueError, match="key_points"):
            _validate_extracted_data(data, config=config)


class TestPipelineOptionsExtractionConfig:
    """Test that PipelineOptions includes extraction_config field."""

    def test_has_extraction_config_field(self):
        from src.pipeline import PipelineOptions
        from src.extractor import ExtractionConfig

        config = ExtractionConfig(language="en")
        opts = PipelineOptions(extraction_config=config)
        assert opts.extraction_config is not None
        assert opts.extraction_config.language == "en"

    def test_extraction_config_defaults_none(self):
        from src.pipeline import PipelineOptions

        opts = PipelineOptions()
        assert opts.extraction_config is None
