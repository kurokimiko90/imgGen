"""
scripts/design_review_loop.py

Automated design review loop:
    screenshot → Claude CLI visual analysis → CSS patch → repeat (max 5 iterations)
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.renderer import render_card
from src.screenshotter import take_screenshot

PROMPTS_DIR = PROJECT_ROOT / "prompts"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
OUTPUT_DIR = PROJECT_ROOT / "output"

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Issue:
    severity: Literal["CRITICAL", "MAJOR", "MINOR"]
    description: str


@dataclass
class ReviewResult:
    score: int
    issues: list[Issue]
    css_patches: dict[str, str]
    done: bool
    rationale: str
    iteration: int


@dataclass
class LoopSummary:
    theme: str
    total_iterations: int
    final_score: int
    done: bool
    final_screenshot: Path
    report_path: Path
    history: list[ReviewResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pure functions
# ---------------------------------------------------------------------------


def generate_screenshot(theme: str, output_path: "str | Path") -> Path:
    """Render a card for *theme* and take a screenshot to *output_path*.

    Uses a minimal data dict so the template renders without real article data.
    Returns the output path.
    """
    output_path = Path(output_path)
    dummy_data = {
        "title": "台灣半導體掌控全球供應鏈",
        "key_points": [
            {"text": "台積電先進製程技術持續領先，AI 晶片需求激增帶動訂單排到 2025 年底"},
            {"text": "地緣政治風險與電力供應問題是業界最大隱憂"},
            {"text": "政府推動分散製造基地政策，在日本熊本、美國亞利桑那興建新廠"},
            {"text": "台灣佔全球晶圓代工市場逾 60%，供應鏈集中風險引發各國關注"},
        ],
        "source": "design_review_loop",
        "theme_suggestion": theme,
    }
    html = render_card(dummy_data, theme=theme, format="story")
    take_screenshot(html, output_path, format="story")
    return output_path


def build_prompt(
    template_path: "str | Path",
    iteration: int,
    css_var_list: list[str],
    prompt_template_path: "str | Path | None" = None,
) -> str:
    """Build the Claude review prompt by injecting context into the prompt template."""
    template_path = Path(template_path)
    if prompt_template_path is None:
        prompt_template_path = PROMPTS_DIR / "design_review.txt"
    prompt_template_path = Path(prompt_template_path)

    template_source = template_path.read_text(encoding="utf-8")
    css_var_str = "\n".join(css_var_list) if css_var_list else "(none)"
    prompt_template = prompt_template_path.read_text(encoding="utf-8")

    return (
        prompt_template
        .replace("{iteration}", str(iteration))
        .replace("{css_var_list}", css_var_str)
        .replace("{template_source}", template_source)
    )


def _compress_image_for_review(image_path: Path) -> bytes:
    """Use PIL to compress the PNG and return compressed bytes (no API cost)."""
    from PIL import Image

    img = Image.open(image_path)
    # Reduce size: max 1200×800 for vision analysis
    img.thumbnail((1200, 800), Image.Resampling.LANCZOS)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        # Save with compression: PNG compression level 9 (max)
        img.save(str(tmp_path), "PNG", optimize=True)
        data = tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)
    return data


def call_claude_cli(
    image_path: "str | Path",
    prompt: str,
    timeout: int = 60,
) -> str:
    """Call the Claude CLI with an embedded base64 image and return stdout.

    The image is compressed with tinify before base64 encoding to stay within
    token limits.

    Raises:
        TimeoutError: If the subprocess exceeds *timeout* seconds.
        RuntimeError: If the subprocess exits with a non-zero return code.
    """
    image_path = Path(image_path)
    compressed_bytes = _compress_image_for_review(image_path)
    image_b64 = base64.b64encode(compressed_bytes).decode()

    image_block = f"![screenshot](data:image/png;base64,{image_b64})"
    full_prompt = f"{image_block}\n\n{prompt}"

    try:
        result = subprocess.run(
            ["claude", "-p", "-"],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(f"Claude CLI timed out after {timeout}s") from exc

    if result.returncode != 0:
        raise RuntimeError(
            f"Claude CLI exited with code {result.returncode}: {result.stderr}"
        )

    return result.stdout


def parse_review(raw_output: str, iteration: int) -> ReviewResult:
    """Extract and validate a ReviewResult from raw Claude CLI output.

    The output may contain extra text around the JSON block.

    Raises:
        ValueError: If the JSON is missing required fields.
        json.JSONDecodeError: If no valid JSON can be found.
    """
    # Extract JSON — find the outermost { ... } block
    match = re.search(r"\{.*\}", raw_output, re.DOTALL)
    if not match:
        raise json.JSONDecodeError("No JSON object found", raw_output, 0)

    data = json.loads(match.group())

    if "score" not in data:
        raise ValueError("Missing required field 'score' in review JSON")

    issues = [
        Issue(severity=i["severity"], description=i["description"])
        for i in data.get("issues", [])
    ]

    has_critical = any(i.severity == "CRITICAL" for i in issues)
    score = int(data["score"])
    # Override done: must be False if any CRITICAL issue exists
    done = (score >= 8) and (not has_critical)

    return ReviewResult(
        score=score,
        issues=issues,
        css_patches=data.get("css_patches", {}),
        done=done,
        rationale=data.get("rationale", ""),
        iteration=iteration,
    )


def apply_patches(
    template_path: "str | Path",
    patches: dict[str, str],
    backup_suffix: str = ".bak",
) -> list[str]:
    """Apply CSS patches to *template_path* in-place.

    Only CSS custom property patches (``--var-name``) are applied.
    ``selector >>> property`` format patches are skipped because global regex
    replacement without proper scope is unsafe and can corrupt the template.

    Creates a backup at ``template_path + backup_suffix`` before modifying.
    Returns the list of patch keys that were successfully applied.
    """
    template_path = Path(template_path)
    original = template_path.read_text(encoding="utf-8")

    backup_path = Path(str(template_path) + backup_suffix)
    backup_path.write_text(original, encoding="utf-8")

    content = original
    applied: list[str] = []

    for key, new_value in patches.items():
        if not key.startswith("--"):
            # Skip selector-based patches — too risky without scoped AST parsing
            continue

        pattern = rf"({re.escape(key)}:\s*)[^;]+(;)"
        replacement = rf"\g<1>{new_value}\g<2>"
        new_content, count = re.subn(pattern, replacement, content)

        if count > 0:
            content = new_content
            applied.append(key)

    template_path.write_text(content, encoding="utf-8")
    return applied


# ---------------------------------------------------------------------------
# Extract CSS vars from template
# ---------------------------------------------------------------------------


def _extract_css_vars(template_path: Path) -> list[str]:
    """Return a list of CSS custom property declarations found in the template."""
    content = template_path.read_text(encoding="utf-8")
    matches = re.findall(r"(--[\w-]+:\s*[^;]+;)", content)
    return matches


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def run(
    theme: str,
    template_path: "str | Path",
    max_iter: int = 5,
    output_dir: "str | Path | None" = None,
    claude_timeout: int = 60,
) -> LoopSummary:
    """Run the design review loop and return a LoopSummary."""
    template_path = Path(template_path)
    output_dir = Path(output_dir) if output_dir else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    history: list[ReviewResult] = []
    final_screenshot: Path = output_dir / "review_iter_1.png"

    for iteration in range(1, max_iter + 1):
        screenshot_path = output_dir / f"review_iter_{iteration}.png"

        # ① Screenshot
        final_screenshot = generate_screenshot(theme, screenshot_path)

        # ② Build prompt
        css_vars = _extract_css_vars(template_path)
        prompt = build_prompt(template_path, iteration, css_vars)

        # ③ Call Claude CLI
        raw = call_claude_cli(final_screenshot, prompt, timeout=claude_timeout * 3)

        # ④ Parse
        result = parse_review(raw, iteration)
        history.append(result)

        # Terminal output
        critical_count = sum(1 for i in result.issues if i.severity == "CRITICAL")
        major_count = sum(1 for i in result.issues if i.severity == "MAJOR")
        minor_count = sum(1 for i in result.issues if i.severity == "MINOR")
        patch_count = len(result.css_patches)
        status = "done=True" if result.done else f"→ applying {patch_count} patches"
        print(
            f"[Iter {iteration}/{max_iter}] score={result.score}"
            f"  CRITICAL:{critical_count} MAJOR:{major_count} MINOR:{minor_count}"
            f"  {status}"
        )
        print(f'           "{result.rationale}"')

        # ⑤ Done?
        if result.done:
            break

        # ⑥ Apply patches（若分數下降則 rollback 並跳出）
        prev_score = history[-2].score if len(history) >= 2 else None
        backup_suffix = f".bak_{iteration}"
        applied = apply_patches(template_path, result.css_patches, backup_suffix=backup_suffix)
        patch_count = len(applied)

        if prev_score is not None and result.score < prev_score:
            backup_path = Path(str(template_path) + backup_suffix)
            if backup_path.exists():
                template_path.write_text(backup_path.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"           ⚠ 分數下降（{prev_score}→{result.score}），已 rollback，停止迭代")
            break

    final_result = history[-1]
    date_str = datetime.now().strftime("%Y%m%d")
    report_path = output_dir / f"design_review_{theme}_{date_str}.json"
    report_data = {
        "theme": theme,
        "total_iterations": len(history),
        "final_score": final_result.score,
        "done": final_result.done,
        "history": [
            {
                "iteration": r.iteration,
                "score": r.score,
                "done": r.done,
                "rationale": r.rationale,
                "issues": [{"severity": i.severity, "description": i.description} for i in r.issues],
                "css_patches": r.css_patches,
            }
            for r in history
        ],
    }
    report_path.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")

    if final_result.done:
        print(f"\n✓ 完成（{len(history)} 次迭代）")
    else:
        print(f"\n✗ 達到最大迭代次數（{max_iter} 次），未達標準")

    print(f"  最終截圖: {final_screenshot}")
    print(f"  報告:     {report_path}")

    return LoopSummary(
        theme=theme,
        total_iterations=len(history),
        final_score=final_result.score,
        done=final_result.done,
        final_screenshot=final_screenshot,
        report_path=report_path,
        history=history,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Design review loop for image cards")
    parser.add_argument("--theme", default="dark", choices=["dark", "light", "gradient"])
    parser.add_argument("--max-iter", type=int, default=5)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument(
        "--template",
        type=Path,
        default=TEMPLATES_DIR / "dark_card.html",
    )
    args = parser.parse_args()

    run(
        theme=args.theme,
        template_path=args.template,
        max_iter=args.max_iter,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
