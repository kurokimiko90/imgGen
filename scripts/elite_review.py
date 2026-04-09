"""
scripts/elite_review.py — Elite 2-agent review system.

Runs content + visual review in parallel, aggregates scores,
and records learnings to SQLite.

Usage:
    # Review a specific content by ID
    python scripts/elite_review.py --content-id 42

    # Review all DRAFT content for an account
    python scripts/elite_review.py --account A

    # Dry run (print scores, don't save)
    python scripts/elite_review.py --account A --dry-run
"""

import asyncio
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import click

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import LevelUpConfig
from src.content import Content, ContentStatus
from src.db import ContentDAO
from src.learning import LearningDAO

PROMPTS_DIR = PROJECT_ROOT / "prompts" / "agents"
DEFAULT_DB_PATH = Path("~/.imggen/history.db").expanduser()
DEFAULT_CONFIG_PATH = Path("~/.imggen/accounts.toml").expanduser()

# Weights: visual 50%, content 50%
WEIGHTS = {"content": 0.50, "visual": 0.50}

# Pass threshold
PASS_THRESHOLD = 7.5


@dataclass
class AgentResult:
    """Result from a single review agent."""
    agent: str
    score: float
    issues: list[dict]
    suggestions: list[str]
    best_element: str
    passed: bool
    css_patches: Optional[dict] = None
    raw: Optional[str] = None


@dataclass
class ReviewVerdict:
    """Aggregated review result."""
    content_id: str
    content_score: float
    visual_score: float
    weighted_score: float
    passed: bool
    has_critical: bool
    results: list[AgentResult]


# ---------------------------------------------------------------------------
# Account config helpers
# ---------------------------------------------------------------------------

ACCOUNT_PERSONAS = {
    "A": {"persona": "AI 自動化 — 崩潰但繼續幹的工程師", "audience": "AI practitioners, dev founders"},
    "B": {"persona": "PMP 職涯 — 穩重專業的管理顧問", "audience": "項目經理, 職場人"},
    "C": {"persona": "足球英語 — 熱情的球迷解說員", "audience": "足球迷, 英語學習者"},
}


def _build_learnings_injection(learning_dao: LearningDAO, account_type: str) -> str:
    """Build a short learnings injection block (max ~200 tokens)."""
    patterns = learning_dao.get_top_patterns(account_type, limit=3)
    failures = learning_dao.get_top_failures(account_type, limit=2)

    if not patterns and not failures:
        return ""

    lines = ["[LEARNED FROM PAST REVIEWS]"]
    if patterns:
        lines.append("DO:")
        for p in patterns:
            lines.append(f"- {p.rule} (confidence: {p.confidence}, n={p.sample_count})")
    if failures:
        lines.append("AVOID:")
        for f in failures:
            lines.append(f"- {f.rule} (avg_score: {f.avg_score})")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Agent execution
# ---------------------------------------------------------------------------


def _call_claude_cli(prompt: str, model: str = "haiku", timeout: int = 60) -> str:
    """Call Claude CLI and return raw text."""
    claude_cli = shutil.which("claude")
    if not claude_cli:
        raise RuntimeError("claude CLI not found")

    result = subprocess.run(
        [claude_cli, "-p", "--output-format", "text", "--model", model],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _parse_agent_result(raw: str, agent_name: str) -> dict:
    """Extract JSON from agent response."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"[{agent_name}] No JSON in response: {raw[:200]}")
    return json.loads(match.group())


async def run_content_review(
    content: Content,
    learning_dao: LearningDAO,
    model: str = "haiku",
) -> AgentResult:
    """Run the content reviewer agent."""
    template = (PROMPTS_DIR / "content_reviewer.txt").read_text(encoding="utf-8")
    persona_info = ACCOUNT_PERSONAS.get(content.account_type.value, {})
    learnings = _build_learnings_injection(learning_dao, content.account_type.value)

    prompt = (
        template
        .replace("{account_type}", content.account_type.value)
        .replace("{account_persona}", persona_info.get("persona", ""))
        .replace("{account_audience}", persona_info.get("audience", ""))
        .replace("{title}", content.title)
        .replace("{body}", content.body)
        .replace("{content_type}", content.content_type.value)
        .replace("{learnings_injection}", learnings)
    )

    loop = asyncio.get_event_loop()
    raw = await loop.run_in_executor(None, _call_claude_cli, prompt, model)
    data = _parse_agent_result(raw, "content")

    return AgentResult(
        agent="content",
        score=float(data.get("score", 0)),
        issues=data.get("issues", []),
        suggestions=data.get("suggestions", []),
        best_element=data.get("best_element", ""),
        passed=data.get("pass", False),
        raw=raw,
    )


async def run_visual_review(
    content: Content,
    screenshot_path: Optional[str],
    learning_dao: LearningDAO,
    model: str = "haiku",
) -> AgentResult:
    """Run the visual reviewer agent.

    If no screenshot exists, returns a neutral score (7.0) to avoid blocking.
    """
    if not screenshot_path or not Path(screenshot_path).exists():
        return AgentResult(
            agent="visual",
            score=7.0,
            issues=[{"severity": "MINOR", "description": "No screenshot available for review"}],
            suggestions=[],
            best_element="N/A",
            passed=True,
        )

    template = (PROMPTS_DIR / "visual_reviewer.txt").read_text(encoding="utf-8")
    learnings = _build_learnings_injection(learning_dao, content.account_type.value)

    prompt = (
        template
        .replace("{account_type}", content.account_type.value)
        .replace("{theme}", content.theme)
        .replace("{format}", content.format)
        .replace("{learnings_injection}", learnings)
    )

    # Add screenshot as base64
    import base64
    from scripts.design_review_loop import _compress_image_for_review

    img_bytes = _compress_image_for_review(Path(screenshot_path))
    img_b64 = base64.b64encode(img_bytes).decode()
    full_prompt = f"![screenshot](data:image/png;base64,{img_b64})\n\n{prompt}"

    loop = asyncio.get_event_loop()
    raw = await loop.run_in_executor(None, _call_claude_cli, full_prompt, model)
    data = _parse_agent_result(raw, "visual")

    return AgentResult(
        agent="visual",
        score=float(data.get("score", 0)),
        issues=data.get("issues", []),
        suggestions=data.get("suggestions", []),
        best_element=data.get("best_element", ""),
        passed=data.get("pass", False),
        css_patches=data.get("css_patches"),
        raw=raw,
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


async def elite_review(
    content: Content,
    learning_dao: LearningDAO,
    screenshot_path: Optional[str] = None,
    model: str = "haiku",
) -> ReviewVerdict:
    """Run 2-agent parallel review and return aggregated verdict."""

    # Run both agents in parallel
    content_result, visual_result = await asyncio.gather(
        run_content_review(content, learning_dao, model=model),
        run_visual_review(content, screenshot_path, learning_dao, model=model),
    )

    # Weighted score
    weighted = (
        content_result.score * WEIGHTS["content"]
        + visual_result.score * WEIGHTS["visual"]
    )

    # Check for critical issues
    all_issues = content_result.issues + visual_result.issues
    has_critical = any(
        i.get("severity") == "CRITICAL" for i in all_issues
    )

    passed = weighted >= PASS_THRESHOLD and not has_critical

    return ReviewVerdict(
        content_id=content.id,
        content_score=content_result.score,
        visual_score=visual_result.score,
        weighted_score=round(weighted, 2),
        passed=passed,
        has_critical=has_critical,
        results=[content_result, visual_result],
    )


# ---------------------------------------------------------------------------
# Learning loop (pure SQL aggregation, no LLM)
# ---------------------------------------------------------------------------


def record_learnings(
    verdict: ReviewVerdict,
    content: Content,
    learning_dao: LearningDAO,
) -> None:
    """Extract patterns from this review and save to DB.

    Uses simple heuristics, NOT an LLM call:
    - High content score + specific attributes → design/copy pattern
    - Low score + critical issues → failure pattern
    """
    account = content.account_type.value

    # Save review scores
    learning_dao.record_review(content.id, {
        "content": verdict.content_score,
        "visual": verdict.visual_score,
        "weighted": verdict.weighted_score,
    })

    # Extract patterns from high scores (>= 8)
    if verdict.content_score >= 8:
        # Record what worked
        for r in verdict.results:
            if r.best_element and r.best_element != "N/A":
                learning_dao.upsert_pattern(
                    account, "copy" if r.agent == "content" else "design",
                    r.best_element, verdict.weighted_score,
                )

    if verdict.visual_score >= 8:
        learning_dao.upsert_pattern(
            account, "design",
            f"theme={content.theme} format={content.format} scored 8+",
            verdict.visual_score,
        )

    # Record failures (< 6)
    if verdict.weighted_score < 6:
        for r in verdict.results:
            critical_issues = [
                i for i in r.issues
                if i.get("severity") in ("CRITICAL", "MAJOR")
            ]
            for issue in critical_issues[:2]:  # Max 2 failures per review
                learning_dao.upsert_pattern(
                    account, "failure",
                    issue.get("description", "unknown issue"),
                    verdict.weighted_score,
                )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.command()
@click.option("--content-id", default=None, help="Review specific content by ID")
@click.option("--account", default=None, type=click.Choice(["A", "B", "C"]))
@click.option("--dry-run", is_flag=True, help="Print scores without saving")
@click.option("--model", default="haiku", type=click.Choice(["haiku", "sonnet", "opus"]))
@click.option("--db-path", default=str(DEFAULT_DB_PATH))
def main(content_id, account, dry_run, model, db_path):
    """Run elite 2-agent review on content."""
    dao = ContentDAO(db_path)
    learning_dao = LearningDAO(db_path)

    # Collect content to review
    contents: list[Content] = []
    if content_id:
        c = dao.find_by_id(content_id)
        if not c:
            print(f"Content {content_id} not found")
            return
        contents = [c]
    elif account:
        contents = dao.find_by_status(ContentStatus.DRAFT, account_type=account)
    else:
        contents = dao.find_by_status(ContentStatus.DRAFT)

    if not contents:
        print("No content to review.")
        return

    print(f"Reviewing {len(contents)} items (model={model})...\n")

    async def _run():
        for content in contents:
            try:
                verdict = await elite_review(
                    content, learning_dao,
                    screenshot_path=content.image_path,
                    model=model,
                )

                status = "✅ PASS" if verdict.passed else "❌ FAIL"
                print(
                    f"[{content.account_type.value}] {content.title[:40]}"
                    f"  {status}  weighted={verdict.weighted_score}"
                    f"  (content={verdict.content_score}, visual={verdict.visual_score})"
                )

                if verdict.has_critical:
                    print("  ⚠️  CRITICAL issues found")

                for r in verdict.results:
                    for issue in r.issues:
                        sev = issue.get("severity", "?")
                        desc = issue.get("description", "")
                        print(f"  [{r.agent}] {sev}: {desc}")

                if not dry_run:
                    record_learnings(verdict, content, learning_dao)
                    # Auto-transition: PASS → PENDING_REVIEW, FAIL stays DRAFT
                    if verdict.passed and content.status == ContentStatus.DRAFT:
                        content.transition_to(ContentStatus.PENDING_REVIEW)
                        dao.update(content)
                        print(f"  → Status: PENDING_REVIEW")

                print()

            except Exception as exc:
                print(f"[{content.account_type.value}] ERROR: {exc}\n")

    asyncio.run(_run())


if __name__ == "__main__":
    main()
