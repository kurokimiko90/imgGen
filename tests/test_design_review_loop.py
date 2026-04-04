"""
tests/test_design_review_loop.py

TDD tests for design_review_loop.py — all tests written before implementation.
"""

import json
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------

VALID_RAW_JSON = json.dumps(
    {
        "score": 7,
        "issues": [
            {"severity": "MAJOR", "description": "低對比度文字"},
            {"severity": "MINOR", "description": "邊距稍寬"},
        ],
        "css_patches": {
            "--color-text": "#ffffff",
            ".hero-card >>> padding": "24px",
        },
        "done": False,
        "rationale": "文字對比度不足，需提升",
    }
)

VALID_RAW_CRITICAL = json.dumps(
    {
        "score": 5,
        "issues": [{"severity": "CRITICAL", "description": "背景幾乎全黑"}],
        "css_patches": {},
        "done": False,
        "rationale": "背景色缺失",
    }
)

VALID_RAW_DONE = json.dumps(
    {
        "score": 9,
        "issues": [{"severity": "MINOR", "description": "微調字重"}],
        "css_patches": {},
        "done": True,
        "rationale": "整體比例良好",
    }
)


# ---------------------------------------------------------------------------
# TestGenerateScreenshot
# ---------------------------------------------------------------------------


class TestGenerateScreenshot:
    def test_returns_path_that_exists(self, tmp_path):
        from scripts.design_review_loop import generate_screenshot

        out = tmp_path / "iter_1.png"
        with (
            patch(
                "scripts.design_review_loop.render_card",
                return_value="<html></html>",
            ),
            patch(
                "scripts.design_review_loop.take_screenshot",
                return_value=out,
            ) as mock_shot,
        ):
            mock_shot.return_value = out
            out.write_bytes(b"fake-png")
            result = generate_screenshot("dark", out)

        assert result == out
        assert result.exists()

    def test_overwrites_existing_file(self, tmp_path):
        from scripts.design_review_loop import generate_screenshot

        out = tmp_path / "iter_1.png"
        out.write_bytes(b"old-content")

        with (
            patch(
                "scripts.design_review_loop.render_card",
                return_value="<html></html>",
            ),
            patch(
                "scripts.design_review_loop.take_screenshot",
                side_effect=lambda html, path, **kw: path,
            ),
        ):
            result = generate_screenshot("dark", out)

        assert result == out


# ---------------------------------------------------------------------------
# TestBuildPrompt
# ---------------------------------------------------------------------------


class TestBuildPrompt:
    @pytest.fixture
    def prompt_file(self, tmp_path):
        p = tmp_path / "design_review.txt"
        p.write_text(
            textwrap.dedent(
                """\
                [CONTEXT] iteration {iteration}
                [CSS VARIABLES AVAILABLE]
                {css_var_list}
                [TEMPLATE SOURCE]
                {template_source}
                """
            )
        )
        return p

    @pytest.fixture
    def template_file(self, tmp_path):
        t = tmp_path / "dark_card.html"
        t.write_text("<html><!-- dark_card --></html>")
        return t

    def test_contains_iteration_number(self, prompt_file, template_file):
        from scripts.design_review_loop import build_prompt

        result = build_prompt(template_file, 3, ["--color-bg: #000"], prompt_file)
        assert "3" in result

    def test_contains_template_source(self, prompt_file, template_file):
        from scripts.design_review_loop import build_prompt

        result = build_prompt(template_file, 1, [], prompt_file)
        assert "dark_card" in result

    def test_contains_css_var_list(self, prompt_file, template_file):
        from scripts.design_review_loop import build_prompt

        css_vars = ["--color-bg: #111", "--font-size-title: 48px"]
        result = build_prompt(template_file, 1, css_vars, prompt_file)
        assert "--color-bg" in result
        assert "--font-size-title" in result


# ---------------------------------------------------------------------------
# TestCallClaudeCli
# ---------------------------------------------------------------------------


FAKE_COMPRESSED = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64  # fake compressed bytes


class TestCallClaudeCli:
    def test_returns_string_output(self, tmp_path):
        from scripts.design_review_loop import call_claude_cli

        img = tmp_path / "img.png"
        img.write_bytes(b"\x89PNG")

        mock_result = MagicMock()
        mock_result.stdout = VALID_RAW_JSON
        mock_result.returncode = 0

        with (
            patch(
                "scripts.design_review_loop._compress_image_for_review",
                return_value=FAKE_COMPRESSED,
            ),
            patch("subprocess.run", return_value=mock_result),
        ):
            output = call_claude_cli(img, "some prompt", timeout=10)

        assert isinstance(output, str)
        assert output == VALID_RAW_JSON

    def test_raises_on_timeout(self, tmp_path):
        from scripts.design_review_loop import call_claude_cli

        img = tmp_path / "img.png"
        img.write_bytes(b"\x89PNG")

        with (
            patch(
                "scripts.design_review_loop._compress_image_for_review",
                return_value=FAKE_COMPRESSED,
            ),
            patch(
                "subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 10)
            ),
        ):
            with pytest.raises(TimeoutError):
                call_claude_cli(img, "prompt", timeout=10)

    def test_raises_on_nonzero_exit(self, tmp_path):
        from scripts.design_review_loop import call_claude_cli

        img = tmp_path / "img.png"
        img.write_bytes(b"\x89PNG")

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "error"
        mock_result.returncode = 1

        with (
            patch(
                "scripts.design_review_loop._compress_image_for_review",
                return_value=FAKE_COMPRESSED,
            ),
            patch("subprocess.run", return_value=mock_result),
        ):
            with pytest.raises(RuntimeError):
                call_claude_cli(img, "prompt", timeout=10)


# ---------------------------------------------------------------------------
# TestParseReview
# ---------------------------------------------------------------------------


class TestParseReview:
    def test_parses_valid_json(self):
        from scripts.design_review_loop import parse_review

        result = parse_review(VALID_RAW_JSON, iteration=1)
        assert result.score == 7
        assert len(result.issues) == 2
        assert result.issues[0].severity == "MAJOR"
        assert result.done is False
        assert result.iteration == 1

    def test_extracts_json_from_noisy_output(self):
        from scripts.design_review_loop import parse_review

        noisy = f"Sure! Here is the review:\n\n{VALID_RAW_JSON}\n\nHope that helps."
        result = parse_review(noisy, iteration=2)
        assert result.score == 7
        assert result.iteration == 2

    def test_raises_on_missing_score(self):
        from scripts.design_review_loop import parse_review

        bad = json.dumps({"issues": [], "css_patches": {}, "done": False, "rationale": "ok"})
        with pytest.raises(ValueError, match="score"):
            parse_review(bad, iteration=1)

    def test_done_is_false_when_critical_exists(self):
        from scripts.design_review_loop import parse_review

        # Even if the JSON says done=True but has CRITICAL, parser should override
        raw = json.dumps(
            {
                "score": 9,
                "issues": [{"severity": "CRITICAL", "description": "fatal issue"}],
                "css_patches": {},
                "done": True,
                "rationale": "has critical",
            }
        )
        result = parse_review(raw, iteration=1)
        assert result.done is False


# ---------------------------------------------------------------------------
# TestApplyPatches
# ---------------------------------------------------------------------------


class TestApplyPatches:
    @pytest.fixture
    def template_file(self, tmp_path):
        t = tmp_path / "dark_card.html"
        t.write_text(
            textwrap.dedent(
                """\
                <style>
                  :root {
                    --color-bg: #111111;
                    --color-text: #aaaaaa;
                    --font-size-title: 40px;
                  }
                  .hero-card { padding: 16px; }
                  .row-item { margin: 8px; }
                </style>
                """
            )
        )
        return t

    def test_applies_css_var_patch(self, template_file):
        from scripts.design_review_loop import apply_patches

        patches = {"--color-text": "#ffffff"}
        apply_patches(template_file, patches, backup_suffix=".bak_1")
        content = template_file.read_text()
        assert "--color-text: #ffffff;" in content

    def test_applies_multiple_patches(self, template_file):
        from scripts.design_review_loop import apply_patches

        patches = {
            "--color-bg": "#000000",
            "--font-size-title": "48px",
        }
        apply_patches(template_file, patches, backup_suffix=".bak_1")
        content = template_file.read_text()
        assert "--color-bg: #000000;" in content
        assert "--font-size-title: 48px;" in content

    def test_skips_selector_patches(self, template_file):
        from scripts.design_review_loop import apply_patches

        patches = {
            "--color-bg": "#000000",
            ".hero-card >>> padding": "99px",  # should be skipped
            "* >>> margin": "26px",            # dangerous — must be skipped
        }
        applied = apply_patches(template_file, patches, backup_suffix=".bak_1")
        content = template_file.read_text()
        assert "--color-bg: #000000;" in content
        assert ".hero-card >>> padding" not in applied
        assert "* >>> margin" not in applied
        assert "99px" not in content
        assert "26px" not in content

    def test_preserves_unrelated_css(self, template_file):
        from scripts.design_review_loop import apply_patches

        patches = {"--color-bg": "#000000"}
        apply_patches(template_file, patches, backup_suffix=".bak_1")
        content = template_file.read_text()
        assert "--color-text: #aaaaaa;" in content
        assert ".hero-card { padding: 16px; }" in content

    def test_creates_backup_file(self, template_file):
        from scripts.design_review_loop import apply_patches

        apply_patches(template_file, {"--color-bg": "#000"}, backup_suffix=".bak_1")
        backup = Path(str(template_file) + ".bak_1")
        assert backup.exists()
        assert "--color-bg: #111111;" in backup.read_text()

    def test_returns_list_of_applied_patches(self, template_file):
        from scripts.design_review_loop import apply_patches

        patches = {"--color-bg": "#000000", "--color-text": "#ffffff"}
        applied = apply_patches(template_file, patches, backup_suffix=".bak_1")
        assert isinstance(applied, list)
        assert len(applied) == 2


# ---------------------------------------------------------------------------
# TestRunLoop
# ---------------------------------------------------------------------------


class TestRunLoop:
    """Tests for the main run() orchestration loop."""

    def _make_review_result(self, score, done, iteration, critical=False):
        from scripts.design_review_loop import Issue, ReviewResult

        issues = [Issue("CRITICAL", "fatal")] if critical else []
        return ReviewResult(
            score=score,
            issues=issues,
            css_patches={"--color-bg": "#000"},
            done=done,
            rationale="test rationale",
            iteration=iteration,
        )

    def test_stops_at_max_iterations(self, tmp_path):
        from scripts.design_review_loop import run

        template = tmp_path / "dark_card.html"
        template.write_text("<style>:root { --color-bg: #111; }</style>")

        iteration_counter = {"n": 0}

        def fake_generate(theme, output_path):
            output_path.write_bytes(b"\x89PNG")
            return output_path

        def fake_call_claude(image_path, prompt, timeout):
            iteration_counter["n"] += 1
            return VALID_RAW_JSON  # score=7, done=False always

        with (
            patch("scripts.design_review_loop.generate_screenshot", side_effect=fake_generate),
            patch("scripts.design_review_loop.call_claude_cli", side_effect=fake_call_claude),
            patch("scripts.design_review_loop.build_prompt", return_value="prompt"),
        ):
            summary = run("dark", template, max_iter=3, output_dir=tmp_path)

        assert summary.total_iterations == 3
        assert iteration_counter["n"] == 3

    def test_stops_early_when_done_true(self, tmp_path):
        from scripts.design_review_loop import run

        template = tmp_path / "dark_card.html"
        template.write_text("<style>:root { --color-bg: #111; }</style>")

        call_count = {"n": 0}

        done_json = VALID_RAW_DONE  # score=9, done=True

        def fake_generate(theme, output_path):
            output_path.write_bytes(b"\x89PNG")
            return output_path

        def fake_call_claude(image_path, prompt, timeout):
            call_count["n"] += 1
            if call_count["n"] == 2:
                return done_json
            return VALID_RAW_JSON

        with (
            patch("scripts.design_review_loop.generate_screenshot", side_effect=fake_generate),
            patch("scripts.design_review_loop.call_claude_cli", side_effect=fake_call_claude),
            patch("scripts.design_review_loop.build_prompt", return_value="prompt"),
        ):
            summary = run("dark", template, max_iter=5, output_dir=tmp_path)

        assert summary.total_iterations == 2
        assert summary.done is True

    def test_applies_patches_each_iteration(self, tmp_path):
        from scripts.design_review_loop import run

        template = tmp_path / "dark_card.html"
        template.write_text("<style>:root { --color-bg: #111; }</style>")

        patches_applied = []

        original_apply = None

        def fake_generate(theme, output_path):
            output_path.write_bytes(b"\x89PNG")
            return output_path

        def fake_call_claude(image_path, prompt, timeout):
            return VALID_RAW_JSON  # css_patches: {"--color-text": ..., ".hero-card >>> padding": ...}

        def fake_apply(template_path, patches, backup_suffix):
            patches_applied.append(patches)
            return list(patches.keys())

        with (
            patch("scripts.design_review_loop.generate_screenshot", side_effect=fake_generate),
            patch("scripts.design_review_loop.call_claude_cli", side_effect=fake_call_claude),
            patch("scripts.design_review_loop.build_prompt", return_value="prompt"),
            patch("scripts.design_review_loop.apply_patches", side_effect=fake_apply),
        ):
            run("dark", template, max_iter=2, output_dir=tmp_path)

        assert len(patches_applied) == 2

    def test_returns_loop_summary(self, tmp_path):
        from scripts.design_review_loop import LoopSummary, run

        template = tmp_path / "dark_card.html"
        template.write_text("<style>:root { --color-bg: #111; }</style>")

        def fake_generate(theme, output_path):
            output_path.write_bytes(b"\x89PNG")
            return output_path

        with (
            patch("scripts.design_review_loop.generate_screenshot", side_effect=fake_generate),
            patch("scripts.design_review_loop.call_claude_cli", return_value=VALID_RAW_DONE),
            patch("scripts.design_review_loop.build_prompt", return_value="prompt"),
        ):
            summary = run("dark", template, max_iter=5, output_dir=tmp_path)

        assert isinstance(summary, LoopSummary)
        assert summary.theme == "dark"
        assert summary.final_score == 9
        assert summary.done is True
        assert summary.report_path.exists()
        assert isinstance(summary.history, list)
        assert len(summary.history) >= 1
