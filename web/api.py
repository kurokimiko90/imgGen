"""
web/api.py - FastAPI backend for imgGen Web UI.

Exposes the existing pipeline, caption, history, digest, batch, watch,
and preset modules via a REST + SSE API.
"""

import asyncio
import json
import os
import sys
import tempfile
from dataclasses import replace as dc_replace
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from src.pipeline import PipelineOptions, run_pipeline, render_and_capture, extract
from src.extractor import ExtractionConfig
from src.history import (
    list_generations,
    search_generations,
    get_stats,
    record_generation,
    get_generation_by_id,
    update_generation,
)
from src.caption import generate_captions
from src.config import list_presets, save_preset, load_preset, delete_preset
from src.digest import generate_digest
from src.renderer import VALID_THEMES, VALID_FORMATS
from src.content import Content, ContentStatus
from src.db import ContentDAO
from src.preflight import preflight_check
from src.scheduler import calculate_scheduled_time

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="imgGen API", version="4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ExtractionConfigRequest(BaseModel):
    language: str = "zh-TW"
    tone: str = "professional"
    max_points: int = Field(5, ge=1, le=10)
    min_points: int = Field(3, ge=1, le=10)
    title_max_chars: int = Field(15, ge=5, le=100)
    point_max_chars: int = Field(50, ge=10, le=500)
    custom_instructions: str = Field("", max_length=500)

    @model_validator(mode="after")
    def check_min_le_max(self) -> "ExtractionConfigRequest":
        if self.min_points > self.max_points:
            raise ValueError("min_points must be <= max_points")
        return self


class GenerateRequest(BaseModel):
    text: str | None = None
    url: str | None = None
    theme: str = "dark"
    format: str = "story"
    formats: list[str] | None = None
    provider: str = "cli"
    scale: int = 2
    webp: bool = False
    watermark_position: str = "bottom-right"
    watermark_opacity: float = 0.8
    brand_name: str | None = None
    thread: bool = False
    mode: str = "card"  # "card", "article", or "smart"
    color_mood: str | None = None  # smart mode only
    social: bool = False  # social mode: add hook field per point
    extraction_config: ExtractionConfigRequest | None = None


class CaptionRequest(BaseModel):
    platforms: list[str]
    provider: str = "claude"
    data: dict[str, Any]


class DigestRequest(BaseModel):
    days: int = 7
    theme: str = "dark"
    provider: str = "cli"


class PresetSaveRequest(BaseModel):
    name: str
    values: dict[str, Any]


class ReRenderRequest(BaseModel):
    history_id: int | None = None
    extracted_data: dict[str, Any]
    theme: str = "dark"
    format: str = "story"
    scale: int = 2
    webp: bool = False
    brand_name: str | None = None
    watermark_position: str = "bottom-right"
    watermark_opacity: float = 0.8


# ---------------------------------------------------------------------------
# LevelUp Content Review API models
# ---------------------------------------------------------------------------

class ContentDetail(BaseModel):
    """Unified response type for all Review/Scheduling/Curation pages."""
    id: str
    account_type: str
    status: str
    content_type: str | None
    title: str
    body: str
    reasoning: str
    image_url: str | None
    source_url: str | None
    source: str | None
    scheduled_time: str | None
    created_at: str
    updated_at: str
    preflight_warnings: list[str] = []
    account_name: str = ""
    platforms: list[str] = []


class ApproveRequest(BaseModel):
    publish_time: str | None = None


class RejectRequest(BaseModel):
    reason: str | None = None


class EditRequest(BaseModel):
    title: str | None = None
    body: str | None = None


class BatchActionRequest(BaseModel):
    ids: list[str]
    action: str  # "approve" | "reject"
    reason: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(**kwargs: Any) -> dict[str, Any]:
    return {"ok": True, **kwargs}


def _content_to_detail(content: Content, account_name: str = "", platforms: list[str] | None = None) -> ContentDetail:
    """Convert Content dataclass to ContentDetail Pydantic model."""
    image_url = None
    if content.image_path:
        fname = Path(content.image_path).name
        if fname:
            image_url = f"/output/{fname}"

    # Get source from reasoning (backward compat)
    source = None
    if content.reasoning and "source:" in content.reasoning.lower():
        source = content.reasoning.split(":")[-1].strip()

    return ContentDetail(
        id=content.id,
        account_type=content.account_type.value,
        status=content.status.value,
        content_type=content.content_type.value if content.content_type else None,
        title=content.title,
        body=content.body,
        reasoning=content.reasoning,
        image_url=image_url,
        source_url=content.source_url,
        source=source,
        scheduled_time=content.scheduled_time.isoformat() if content.scheduled_time else None,
        created_at=content.created_at.isoformat(),
        updated_at=content.updated_at.isoformat(),
        account_name=account_name,
        platforms=platforms or [],
    )


def _err(msg: str, status: int = 400) -> HTTPException:
    return HTTPException(status_code=status, detail=msg)


def _resolve_text(req: GenerateRequest) -> str:
    """Get article text from request (text or url)."""
    if req.text:
        return req.text
    if req.url:
        from src.fetcher import fetch_url_content
        return fetch_url_content(req.url)
    raise _err("Either 'text' or 'url' is required.")


def _parse_extracted_data(raw: str | None) -> dict[str, Any] | None:
    """Parse the extracted_data JSON string from DB, return None if absent."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def _to_extraction_config(
    req_config: ExtractionConfigRequest | None,
    mode: str = "card",
    social: bool = False,
) -> ExtractionConfig:
    """Convert API request model to dataclass."""
    if req_config is None:
        cfg = ExtractionConfig()
    else:
        cfg = ExtractionConfig(**req_config.model_dump())
    return dc_replace(cfg, mode=mode, social_mode=social)


def _build_output_path(theme: str, fmt: str, webp: bool) -> Path:
    ext = ".webp" if webp else ".png"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return OUTPUT_DIR / f"card_{theme}_{timestamp}_{fmt}{ext}"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/api/generate")
async def api_generate(req: GenerateRequest):
    """Generate a single image card."""
    try:
        article_text = _resolve_text(req)
    except HTTPException:
        raise
    except Exception as e:
        raise _err(f"Failed to fetch content: {e}")

    options = PipelineOptions(
        theme=req.theme,
        format=req.format,
        provider=req.provider,
        scale=req.scale,
        webp=req.webp,
        watermark_position=req.watermark_position,
        watermark_opacity=req.watermark_opacity,
        brand_name=req.brand_name,
        mode=req.mode,
        color_mood=req.color_mood,
        extraction_config=_to_extraction_config(req.extraction_config, mode=req.mode, social=req.social),
    )
    output_path = _build_output_path(req.theme, req.format, req.webp)

    loop = asyncio.get_running_loop()
    try:
        data, final_path = await loop.run_in_executor(
            None, run_pipeline, article_text, options, output_path
        )
    except Exception as e:
        raise _err(f"Pipeline failed: {e}", 500)

    file_size = final_path.stat().st_size if final_path.exists() else None

    history_id = record_generation(
        title=data.get("title", ""),
        theme=req.theme,
        format=req.format,
        provider=req.provider,
        output_path=str(final_path),
        file_size=file_size,
        key_points_count=len(data.get("key_points", [])),
        source=data.get("source"),
        url=req.url,
        extracted_data=json.dumps(data, ensure_ascii=False),
    )

    image_url = f"/output/{final_path.name}"
    return _ok(
        image_url=image_url,
        title=data.get("title", ""),
        points_count=len(data.get("key_points", [])),
        file_size=file_size,
        extracted_data=data,
        history_id=history_id,
    )


@app.post("/api/generate/multi")
async def api_generate_multi(req: GenerateRequest):
    """Generate cards in multiple formats."""
    formats = req.formats or [req.format]
    try:
        article_text = _resolve_text(req)
    except HTTPException:
        raise
    except Exception as e:
        raise _err(f"Failed to fetch content: {e}")

    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(
        None, extract, article_text, req.provider,
        _to_extraction_config(req.extraction_config),
    )

    images = []
    for fmt in formats:
        options = PipelineOptions(
            theme=req.theme,
            format=fmt,
            provider=req.provider,
            scale=req.scale,
            webp=req.webp,
            watermark_position=req.watermark_position,
            watermark_opacity=req.watermark_opacity,
            brand_name=req.brand_name,
            extraction_config=_to_extraction_config(req.extraction_config, mode=req.mode, social=req.social),
        )
        output_path = _build_output_path(req.theme, fmt, req.webp)
        final_path = await loop.run_in_executor(
            None, render_and_capture, data, options, output_path
        )
        file_size = final_path.stat().st_size if final_path.exists() else None

        record_generation(
            title=data.get("title", ""),
            theme=req.theme,
            format=fmt,
            provider=req.provider,
            output_path=str(final_path),
            file_size=file_size,
            key_points_count=len(data.get("key_points", [])),
            source=data.get("source"),
            url=req.url,
            mode="multi",
            extracted_data=json.dumps(data, ensure_ascii=False),
        )

        images.append({
            "url": f"/output/{final_path.name}",
            "format": fmt,
            "size": file_size,
        })

    return _ok(images=images, title=data.get("title", ""), extracted_data=data)


@app.post("/api/caption")
async def api_caption(req: CaptionRequest):
    """Generate platform-specific captions."""
    loop = asyncio.get_running_loop()
    try:
        captions = await loop.run_in_executor(
            None, generate_captions, req.data, req.platforms, req.provider
        )
    except ValueError as e:
        raise _err(str(e))
    return _ok(captions=captions)


@app.get("/api/history")
async def api_history(
    days: int | None = None,
    q: str | None = None,
    limit: int = 20,
):
    """List or search generation history."""
    if q:
        rows = search_generations(q, limit=limit)
    else:
        rows = list_generations(days=days, limit=limit)
    # Parse extracted_data JSON strings
    for row in rows:
        row["extracted_data"] = _parse_extracted_data(row.get("extracted_data"))
    return _ok(rows=rows)


@app.get("/api/stats")
async def api_stats(days: int | None = None):
    """Get generation statistics."""
    stats = get_stats(days=days)
    return _ok(**stats)


@app.get("/api/history/{gen_id}")
async def api_history_detail(gen_id: int):
    """Get a single generation record with full extracted data."""
    row = get_generation_by_id(gen_id)
    if not row:
        raise _err(f"Generation #{gen_id} not found.", 404)
    row["extracted_data"] = _parse_extracted_data(row.get("extracted_data"))
    # Build image URL from output_path
    output_name = Path(row.get("output_path", "")).name
    row["image_url"] = f"/output/{output_name}" if output_name else None
    return _ok(row=row)


@app.post("/api/re-render")
async def api_re_render(req: ReRenderRequest):
    """Re-render a card from edited extracted data (skips AI extraction)."""
    ed = req.extracted_data
    if "title" not in ed or "key_points" not in ed:
        raise _err("extracted_data must contain 'title' and 'key_points'.")
    if not isinstance(ed.get("key_points"), list) or not ed["key_points"]:
        raise _err("key_points must be a non-empty list.")

    options = PipelineOptions(
        theme=req.theme,
        format=req.format,
        scale=req.scale,
        webp=req.webp,
        watermark_position=req.watermark_position,
        watermark_opacity=req.watermark_opacity,
        brand_name=req.brand_name,
    )
    output_path = _build_output_path(req.theme, req.format, req.webp)

    loop = asyncio.get_running_loop()
    try:
        final_path = await loop.run_in_executor(
            None, render_and_capture, ed, options, output_path
        )
    except Exception as e:
        raise _err(f"Re-render failed: {e}", 500)

    file_size = final_path.stat().st_size if final_path.exists() else None
    ed_json = json.dumps(ed, ensure_ascii=False)

    if req.history_id:
        update_generation(
            req.history_id,
            extracted_data=ed_json,
            output_path=str(final_path),
            file_size=file_size,
            key_points_count=len(ed.get("key_points", [])),
            title=ed.get("title", ""),
        )
        history_id = req.history_id
    else:
        history_id = record_generation(
            title=ed.get("title", ""),
            theme=req.theme,
            format=req.format,
            provider="re-render",
            output_path=str(final_path),
            file_size=file_size,
            key_points_count=len(ed.get("key_points", [])),
            source=ed.get("source"),
            mode="re-render",
            extracted_data=ed_json,
        )

    return _ok(
        image_url=f"/output/{final_path.name}",
        title=ed.get("title", ""),
        file_size=file_size,
        extracted_data=ed,
        history_id=history_id,
    )


@app.get("/api/export/html/{gen_id}")
async def api_export_html(gen_id: int):
    """Export a generation's rendered HTML as a downloadable file."""
    row = get_generation_by_id(gen_id)
    if not row:
        raise _err(f"Generation #{gen_id} not found.", 404)

    extracted = _parse_extracted_data(row.get("extracted_data"))
    if not extracted:
        raise _err("No extracted data available for this generation.", 400)

    from src.renderer import render_card

    html_content = render_card(
        extracted,
        theme=row.get("theme", "dark"),
        format=row.get("format", "story"),
    )
    return Response(
        content=html_content,
        media_type="text/html; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="imggen_{gen_id}.html"'
        },
    )


@app.post("/api/digest")
async def api_digest(req: DigestRequest):
    """Generate a weekly digest card."""
    generations = list_generations(days=req.days, limit=50)
    if not generations:
        raise _err("No generations found in the given period.")

    loop = asyncio.get_running_loop()
    try:
        digest_data = await loop.run_in_executor(
            None, generate_digest, generations, req.days, req.provider
        )
    except ValueError as e:
        raise _err(str(e))

    # Render digest as a card
    card_data = {
        "title": digest_data["title"],
        "key_points": [
            {"emoji": "📰", "text": f"{pt['article_title']}: {pt['insight']}"}
            for pt in digest_data.get("digest_points", [])
        ],
        "source": digest_data.get("period", ""),
    }

    options = PipelineOptions(theme=req.theme, provider=req.provider)
    output_path = _build_output_path(req.theme, "story", False)
    try:
        final_path = await loop.run_in_executor(
            None, render_and_capture, card_data, options, output_path
        )
    except Exception as e:
        raise _err(f"Digest render failed: {e}", 500)

    return _ok(
        image_url=f"/output/{final_path.name}",
        title=digest_data["title"],
    )


@app.get("/api/presets")
async def api_presets_list():
    """List all presets."""
    presets = list_presets()
    return _ok(presets=presets)


@app.post("/api/presets")
async def api_presets_save(req: PresetSaveRequest):
    """Save a preset."""
    save_preset(req.name, req.values)
    return _ok()


@app.delete("/api/presets/{name}")
async def api_presets_delete(name: str):
    """Delete a preset."""
    deleted = delete_preset(name)
    if not deleted:
        raise _err(f"Preset '{name}' not found.", 404)
    return _ok()


@app.get("/api/meta")
async def api_meta():
    """Return available themes, formats, providers, and smart mode metadata."""
    from src.smart_renderer import COLOR_PALETTES, LAYOUT_PATTERNS

    return _ok(
        themes=sorted(VALID_THEMES),
        formats=sorted(VALID_FORMATS),
        providers=["cli", "claude", "gemini", "gpt"],
        modes=["card", "article", "smart"],
        color_moods=sorted(COLOR_PALETTES.keys()),
        layout_patterns={k: v for k, v in LAYOUT_PATTERNS.items()},
    )


# ---------------------------------------------------------------------------
# Batch SSE endpoint
# ---------------------------------------------------------------------------

@app.post("/api/batch")
async def api_batch(
    file: UploadFile = File(...),
    workers: int = Form(3),
    theme: str = Form("dark"),
    format: str = Form("story"),
    provider: str = Form("cli"),
):
    """Batch process a file of URLs/paths. Returns SSE stream."""
    content = (await file.read()).decode("utf-8")
    entries = [
        line.strip() for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not entries:
        raise _err("Batch file is empty.")

    from src.batch import run_batch

    async def stream():
        total = len(entries)
        yield f"data: {json.dumps({'type': 'start', 'total': total})}\n\n"

        options = {
            "theme": theme,
            "format": format,
            "provider": provider,
        }
        results = await run_batch(entries, options, OUTPUT_DIR, workers=workers)

        for r in results:
            if r["status"] == "ok":
                r["url"] = f"/output/{Path(r['output']).name}"
            yield f"data: {json.dumps({'type': 'result', **r})}\n\n"

        ok_count = sum(1 for r in results if r["status"] == "ok")
        yield f"data: {json.dumps({'type': 'done', 'ok': ok_count, 'errors': total - ok_count})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Phase A: Review API endpoints
# ---------------------------------------------------------------------------

@app.get("/api/content/review")
async def api_content_review(
    status: str | None = None,
    account: str | None = None,
    limit: int = 50,
):
    """List content awaiting review with optional filters.

    ?status=DRAFT,PENDING_REVIEW&account=A&limit=50
    """
    if limit <= 0 or limit > 200:
        raise _err("limit must be between 1 and 200", 400)

    # Parse status filter (comma-separated list)
    statuses = []
    if status:
        try:
            statuses = [ContentStatus(s.strip()) for s in status.split(",") if s.strip()]
        except ValueError as e:
            raise _err(f"Invalid status value: {e}", 400)
    else:
        statuses = [ContentStatus.DRAFT, ContentStatus.PENDING_REVIEW]

    dao = ContentDAO()
    account_cfgs = _load_levelup_accounts()

    # Fetch all matching content, then filter and limit
    all_content = []
    for st in statuses:
        items = dao.find_by_status(st, account_type=account)
        all_content.extend(items)

    # Sort by created_at DESC and limit
    all_content.sort(key=lambda c: c.created_at, reverse=True)
    all_content = all_content[:limit]

    items = []
    for content in all_content:
        acct_cfg = account_cfgs.get(content.account_type.value, {})
        platforms = acct_cfg.get("platforms", [])
        warnings = preflight_check(content, platforms)
        detail = _content_to_detail(content, acct_cfg.get("name", ""), platforms)
        detail.preflight_warnings = warnings
        items.append(detail)

    return _ok(items=items, total=len(items))


@app.get("/api/content/{content_id}/detail")
async def api_content_detail(content_id: str):
    """Get a single content item by id."""
    dao = ContentDAO()
    content = dao.find_by_id(content_id)
    if not content:
        raise _err(f"Content #{content_id} not found.", 404)

    account_cfgs = _load_levelup_accounts()
    acct_cfg = account_cfgs.get(content.account_type.value, {})
    platforms = acct_cfg.get("platforms", [])
    warnings = preflight_check(content, platforms)
    detail = _content_to_detail(content, acct_cfg.get("name", ""), platforms)
    detail.preflight_warnings = warnings

    return _ok(item=detail)


@app.post("/api/content/{content_id}/approve")
async def api_content_approve(content_id: str, req: ApproveRequest):
    """Approve content with single-roundtrip preflight check.

    Returns {status, warnings}. If status='ERROR', preflight failed (user sees dialog).
    If status='OK'/'WARNING', transition succeeds and warnings are informational.
    """
    dao = ContentDAO()
    content = dao.find_by_id(content_id)
    if not content:
        raise _err(f"Content #{content_id} not found.", 404)

    account_cfgs = _load_levelup_accounts()
    acct_cfg = account_cfgs.get(content.account_type.value, {})
    platforms = acct_cfg.get("platforms", [])

    # Preflight check
    warnings = preflight_check(content, platforms)
    blocking_warnings = [w for w in warnings if w.startswith("[ERROR]")]

    if blocking_warnings:
        # Return ERROR status without transitioning
        return _ok(
            status="ERROR",
            warnings=blocking_warnings,
            message="修正後方可核准"
        )

    # Transition to APPROVED
    new_content = dc_replace(content, status=ContentStatus.APPROVED)

    # Optionally assign scheduled_time if provided
    if req.publish_time:
        try:
            scheduled = calculate_scheduled_time(req.publish_time)
            new_content = dc_replace(new_content, scheduled_time=scheduled)
        except ValueError as e:
            raise _err(f"Invalid publish_time: {e}", 400)

    dao.update(new_content)

    return _ok(
        status="OK" if not warnings else "WARNING",
        warnings=[w.replace("[WARNING] ", "") for w in warnings if w.startswith("[WARNING]")],
        item=_content_to_detail(new_content, acct_cfg.get("name", ""), platforms).model_dump()
    )


@app.post("/api/content/{content_id}/reject")
async def api_content_reject(content_id: str, req: RejectRequest):
    """Reject/discard content."""
    dao = ContentDAO()
    content = dao.find_by_id(content_id)
    if not content:
        raise _err(f"Content #{content_id} not found.", 404)

    new_content = dc_replace(content, status=ContentStatus.REJECTED)
    if req.reason:
        new_content = dc_replace(new_content, reasoning=req.reason)

    dao.update(new_content)

    account_cfgs = _load_levelup_accounts()
    acct_cfg = account_cfgs.get(content.account_type.value, {})

    return _ok(item=_content_to_detail(new_content, acct_cfg.get("name", ""), acct_cfg.get("platforms", [])).model_dump())


@app.put("/api/content/{content_id}")
async def api_content_edit(content_id: str, req: EditRequest):
    """Edit content title and/or body."""
    if not req.title and not req.body:
        raise _err("At least one of title or body is required.", 400)

    dao = ContentDAO()
    content = dao.find_by_id(content_id)
    if not content:
        raise _err(f"Content #{content_id} not found.", 404)

    updates = {}
    if req.title:
        updates['title'] = req.title
    if req.body:
        updates['body'] = req.body

    new_content = dc_replace(content, **updates)
    dao.update(new_content)

    account_cfgs = _load_levelup_accounts()
    acct_cfg = account_cfgs.get(content.account_type.value, {})
    platforms = acct_cfg.get("platforms", [])

    return _ok(item=_content_to_detail(new_content, acct_cfg.get("name", ""), platforms).model_dump())


@app.post("/api/content/batch")
async def api_content_batch(req: BatchActionRequest):
    """Batch approve or reject multiple content items."""
    if not req.ids:
        raise _err("ids cannot be empty.", 400)
    if req.action not in ("approve", "reject"):
        raise _err("action must be 'approve' or 'reject'.", 400)

    dao = ContentDAO()
    account_cfgs = _load_levelup_accounts()
    results = []

    for content_id in req.ids:
        content = dao.find_by_id(content_id)
        if not content:
            results.append({"id": content_id, "status": "error", "message": "not found"})
            continue

        if req.action == "approve":
            # Quick approval without preflight (bulk mode)
            new_content = dc_replace(content, status=ContentStatus.APPROVED)
        else:
            new_content = dc_replace(content, status=ContentStatus.REJECTED)
            if req.reason:
                new_content = dc_replace(new_content, reasoning=req.reason)

        dao.update(new_content)
        acct_cfg = account_cfgs.get(content.account_type.value, {})
        results.append({
            "id": content_id,
            "status": "ok",
            "item": _content_to_detail(new_content, acct_cfg.get("name", ""), acct_cfg.get("platforms", [])).model_dump()
        })

    return _ok(results=results)


# ---------------------------------------------------------------------------
# Phase B: Curation API (SSE progress streaming)
# ---------------------------------------------------------------------------

class CurationRunRequest(BaseModel):
    accounts: list[str] = ["A", "B", "C"]
    dry_run: bool = False


# Tracks active curation run state
_curation_state: dict[str, Any] = {"running": False, "started_at": None, "progress": []}


def _sse(event_type: str, **kwargs: Any) -> str:
    """Format a server-sent event line."""
    return f"data: {json.dumps({'type': event_type, **kwargs})}\n\n"


@app.post("/api/curation/run")
async def api_curation_run(req: CurationRunRequest):
    """Trigger curation pipeline with SSE progress streaming.

    Returns a stream of events:
      start, account_start, item_fetched, generating_image,
      saved_draft, item_skipped, item_error, account_done, done
    """
    global _curation_state

    if _curation_state.get("running"):
        raise _err("A curation run is already in progress.", 409)

    # Validate accounts
    valid_accounts = {"A", "B", "C"}
    for acct in req.accounts:
        if acct not in valid_accounts:
            raise _err(f"Invalid account: {acct}. Must be A, B, or C.", 400)

    async def stream():
        global _curation_state

        _curation_state = {
            "running": True,
            "started_at": datetime.now().isoformat(),
            "progress": [],
        }

        sys.path.insert(0, str(PROJECT_ROOT))
        from scripts.daily_curation import curate_for_account, SCRAPERS
        from src.config import LevelUpConfig

        yield _sse("start", accounts=req.accounts, dry_run=req.dry_run)

        total_drafted = 0
        loop = asyncio.get_running_loop()
        event_queue: asyncio.Queue[dict] = asyncio.Queue()
        done_event = asyncio.Event()

        def emit_callback(event_type: str, **kwargs: Any) -> None:
            """Thread-safe callback: puts event into asyncio queue."""
            event = {"type": event_type, **kwargs}
            _curation_state["progress"].append(event)
            loop.call_soon_threadsafe(event_queue.put_nowait, event)

        async def _run_account(acct_id: str) -> int:
            """Run one account's curation in a thread executor."""
            scraper = SCRAPERS[acct_id]()
            config = LevelUpConfig()
            dao = ContentDAO()

            def _blocking():
                return asyncio.run(
                    curate_for_account(
                        acct_id, scraper, config, dao,
                        dry_run=req.dry_run,
                        progress_callback=emit_callback,
                    )
                )

            return await loop.run_in_executor(None, _blocking)

        async def _drain_queue() -> None:
            """Yield events from queue until signalled done."""
            while not done_event.is_set() or not event_queue.empty():
                try:
                    event = event_queue.get_nowait()
                    yield event
                except asyncio.QueueEmpty:
                    await asyncio.sleep(0.05)

        try:
            for acct_id in req.accounts:
                yield _sse("account_start", account=acct_id)
                done_event.clear()

                task = asyncio.create_task(_run_account(acct_id))

                # Stream events while task runs
                while not task.done():
                    try:
                        event = event_queue.get_nowait()
                        yield f"data: {json.dumps(event)}\n\n"
                    except asyncio.QueueEmpty:
                        await asyncio.sleep(0.05)

                # Drain remaining events after task finishes
                while not event_queue.empty():
                    event = await event_queue.get()
                    yield f"data: {json.dumps(event)}\n\n"

                done_event.set()

                result = task.result()
                if isinstance(result, Exception):
                    yield _sse("account_error", account=acct_id, error=str(result))
                else:
                    total_drafted += result
                    yield _sse("account_done", account=acct_id, drafted=result)

        except Exception as exc:
            yield _sse("error", message=str(exc))
        finally:
            _curation_state["running"] = False
            yield _sse("done", total_drafted=total_drafted)

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/api/curation/status")
async def api_curation_status():
    """Return the current curation run status."""
    return _ok(**_curation_state)


@app.get("/api/curation/stats")
async def api_curation_stats():
    """Return curation statistics (today/week/approval_rate per account)."""
    dao = ContentDAO()
    stats = dao.get_curation_stats()
    return _ok(stats=stats)


# ---------------------------------------------------------------------------
# Phase C: Scheduling API
# ---------------------------------------------------------------------------

class RescheduleRequest(BaseModel):
    scheduled_time: str  # ISO 8601 datetime string


@app.get("/api/content/scheduled")
async def api_content_scheduled(
    start: str | None = None,
    end: str | None = None,
    account: str | None = None,
):
    """Return APPROVED content scheduled in a date range.

    ?start=2026-03-30&end=2026-04-06&account=A
    """
    today = datetime.now().strftime("%Y-%m-%d")
    start_date = start or today
    end_date = end or today

    dao = ContentDAO()
    account_cfgs = _load_levelup_accounts()
    items = dao.find_scheduled(start_date, end_date, account_type=account)

    result = []
    for content in items:
        acct_cfg = account_cfgs.get(content.account_type.value, {})
        detail = _content_to_detail(content, acct_cfg.get("name", ""), acct_cfg.get("platforms", []))
        result.append(detail)

    return _ok(items=result, total=len(result))


@app.patch("/api/content/{content_id}/reschedule")
async def api_content_reschedule(content_id: str, req: RescheduleRequest):
    """Update scheduled_time for content (drag-and-drop reschedule)."""
    # Validate ISO 8601 format
    try:
        new_time = datetime.fromisoformat(req.scheduled_time)
    except ValueError:
        raise _err(f"Invalid scheduled_time: '{req.scheduled_time}'. Expected ISO 8601.", 400)

    dao = ContentDAO()
    content = dao.find_by_id(content_id)
    if not content:
        raise _err(f"Content #{content_id} not found.", 404)

    new_content = dc_replace(content, scheduled_time=new_time)
    dao.update(new_content)

    account_cfgs = _load_levelup_accounts()
    acct_cfg = account_cfgs.get(content.account_type.value, {})

    return _ok(item=_content_to_detail(new_content, acct_cfg.get("name", ""), acct_cfg.get("platforms", [])).model_dump())


# ---------------------------------------------------------------------------
# Phase D: Curation content list
# ---------------------------------------------------------------------------

class StatusUpdateRequest(BaseModel):
    status: str  # "PENDING_REVIEW" | "REJECTED"


@app.get("/api/content/drafts")
async def api_content_drafts(
    account: str | None = None,
    source: str | None = None,
    days: int | None = None,
):
    """Return DRAFT content with optional filters.

    ?account=A&source=hacker_news&days=7
    """
    dao = ContentDAO()
    account_cfgs = _load_levelup_accounts()
    items = dao.find_drafts(account_type=account, source=source, days=days)

    result = []
    for content in items:
        acct_cfg = account_cfgs.get(content.account_type.value, {})
        detail = _content_to_detail(content, acct_cfg.get("name", ""), acct_cfg.get("platforms", []))
        result.append(detail)

    return _ok(items=result, total=len(result))


@app.patch("/api/content/{content_id}/status")
async def api_content_status_update(content_id: str, req: StatusUpdateRequest):
    """Transition content to PENDING_REVIEW or REJECTED (Curation page action)."""
    allowed_statuses = {"PENDING_REVIEW", "REJECTED"}
    if req.status not in allowed_statuses:
        raise _err(f"status must be one of: {', '.join(allowed_statuses)}", 400)

    dao = ContentDAO()
    content = dao.find_by_id(content_id)
    if not content:
        raise _err(f"Content #{content_id} not found.", 404)

    try:
        new_status = ContentStatus(req.status)
    except ValueError:
        raise _err(f"Invalid status: {req.status}", 400)

    new_content = dc_replace(content, status=new_status)
    dao.update(new_content)

    account_cfgs = _load_levelup_accounts()
    acct_cfg = account_cfgs.get(content.account_type.value, {})

    return _ok(item=_content_to_detail(new_content, acct_cfg.get("name", ""), acct_cfg.get("platforms", [])).model_dump())


# ---------------------------------------------------------------------------
# Dashboard / LevelUp content endpoints
# ---------------------------------------------------------------------------

_DB_PATH = Path("~/.imggen/history.db").expanduser()


def _get_db_conn():
    """Open a SQLite connection to the history DB with Row factory."""
    import sqlite3
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _load_levelup_accounts() -> dict[str, dict]:
    """Load account configs from LevelUpConfig, falling back to defaults."""
    try:
        from src.config import LevelUpConfig
        cfg = LevelUpConfig()
        accounts = {}
        for acct_id, acct in cfg.list_accounts().items():
            accounts[acct_id] = {
                "name": acct.name,
                "platforms": acct.platforms,
                "publish_time": acct.publish_time,
                "color_mood": acct.color_mood,
                "tone": acct.tone,
            }
        return accounts
    except Exception:
        return {
            "A": {"name": "Account A", "platforms": [], "publish_time": "09:00", "color_mood": "dark", "tone": ""},
            "B": {"name": "Account B", "platforms": [], "publish_time": "12:00", "color_mood": "light", "tone": ""},
            "C": {"name": "Account C", "platforms": [], "publish_time": "18:00", "color_mood": "gradient", "tone": ""},
        }


@app.get("/api/content/stats")
async def api_content_stats():
    """Return generation stats grouped by account (A, B, C)."""
    import sqlite3

    try:
        conn = _get_db_conn()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB connection failed: {e}")

    try:
        cursor = conn.cursor()

        # Status counts per account
        cursor.execute(
            "SELECT account_type, status, COUNT(*) as cnt "
            "FROM generations WHERE account_type IS NOT NULL "
            "GROUP BY account_type, status"
        )
        count_rows = cursor.fetchall()

        # Weekly output: published/approved in last 7 days per account
        cursor.execute(
            "SELECT account_type, COUNT(*) as cnt "
            "FROM generations "
            "WHERE account_type IS NOT NULL "
            "  AND status IN ('PUBLISHED', 'APPROVED') "
            "  AND created_at >= datetime('now', '-7 days') "
            "GROUP BY account_type"
        )
        weekly_rows = cursor.fetchall()
    except sqlite3.Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"DB query failed: {e}")
    finally:
        conn.close()

    # Build counts map: {account_type: {status: count}}
    counts_map: dict[str, dict[str, int]] = {}
    for row in count_rows:
        acct = row["account_type"]
        status = row["status"] or "UNKNOWN"
        if acct not in counts_map:
            counts_map[acct] = {}
        counts_map[acct][status] = row["cnt"]

    weekly_map: dict[str, int] = {row["account_type"]: row["cnt"] for row in weekly_rows}

    # Load account names
    account_cfgs = _load_levelup_accounts()

    all_statuses = ["DRAFT", "PENDING_REVIEW", "APPROVED", "PUBLISHED", "REJECTED"]
    accounts_out: dict[str, dict] = {}

    for acct_id in ["A", "B", "C"]:
        acct_counts = counts_map.get(acct_id, {})
        counts = {s: acct_counts.get(s, 0) for s in all_statuses}

        approved = counts.get("APPROVED", 0)
        rejected = counts.get("REJECTED", 0)
        denom = approved + rejected
        approval_rate = round(approved / denom, 4) if denom > 0 else 0.0

        cfg_entry = account_cfgs.get(acct_id, {})
        accounts_out[acct_id] = {
            "name": cfg_entry.get("name", f"Account {acct_id}"),
            "counts": counts,
            "weekly_output": weekly_map.get(acct_id, 0),
            "approval_rate": approval_rate,
        }

    return _ok(accounts=accounts_out)


@app.get("/api/content/recent")
async def api_content_recent(limit: int = 10):
    """Return the most recent N LevelUp content rows."""
    import sqlite3

    try:
        conn = _get_db_conn()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB connection failed: {e}")

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, account_type, title, status, content_type, output_path, created_at "
            "FROM generations "
            "WHERE account_type IS NOT NULL "
            "ORDER BY created_at DESC "
            "LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"DB query failed: {e}")
    finally:
        conn.close()

    items = []
    for row in rows:
        output_path = row["output_path"]
        image_url = None
        if output_path:
            fname = Path(output_path).name
            if fname:
                image_url = f"/output/{fname}"
        items.append({
            "id": str(row["id"]),
            "account_type": row["account_type"],
            "title": row["title"],
            "status": row["status"],
            "content_type": row["content_type"],
            "image_url": image_url,
            "created_at": row["created_at"],
        })

    return _ok(items=items)


@app.get("/api/content/schedule")
async def api_content_schedule(date: str | None = None):
    """Return APPROVED content scheduled for a specific date (default: today)."""
    import sqlite3

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    try:
        conn = _get_db_conn()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB connection failed: {e}")

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, account_type, title, status, content_type, scheduled_time, output_path "
            "FROM generations "
            "WHERE account_type IS NOT NULL "
            "  AND status = 'APPROVED' "
            "  AND DATE(scheduled_time) = ? "
            "ORDER BY scheduled_time",
            (date,),
        )
        rows = cursor.fetchall()
    except sqlite3.Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"DB query failed: {e}")
    finally:
        conn.close()

    items = []
    for row in rows:
        output_path = row["output_path"]
        image_url = None
        if output_path:
            fname = Path(output_path).name
            if fname:
                image_url = f"/output/{fname}"
        items.append({
            "id": str(row["id"]),
            "account_type": row["account_type"],
            "title": row["title"],
            "status": row["status"],
            "content_type": row["content_type"],
            "scheduled_time": row["scheduled_time"],
            "image_url": image_url,
        })

    return _ok(items=items)


@app.get("/api/accounts")
async def api_accounts():
    """Return account configurations from LevelUpConfig."""
    accounts = _load_levelup_accounts()
    return _ok(accounts=accounts)


# ---------------------------------------------------------------------------
# Phase E: Account Settings API
# ---------------------------------------------------------------------------

class AccountUpdateRequest(BaseModel):
    name: str | None = None
    platforms: list[str] | None = None
    publish_time: str | None = None
    color_mood: str | None = None
    tone: str | None = None
    prompt_content: str | None = None


class PreviewRequest(BaseModel):
    color_mood: str = "dark_tech"


_LEVELUP_CONFIG_PATH = Path("~/.imggen/accounts.toml").expanduser()
_PROMPTS_DIR = PROJECT_ROOT / "prompts"


@app.get("/api/accounts/{account_id}/prompt")
async def api_account_prompt(account_id: str):
    """Read the prompt file for an account."""
    if account_id not in ("A", "B", "C"):
        raise _err(f"Invalid account: {account_id}", 400)

    try:
        from src.config import LevelUpConfig
        cfg = LevelUpConfig()
        account = cfg.get_account(account_id)
        prompt_path = PROJECT_ROOT / account.prompt_file
    except Exception:
        # Fallback to default path
        prompt_path = _PROMPTS_DIR / f"account_{account_id.lower()}.txt"

    if not prompt_path.exists():
        raise _err(f"Prompt file not found for account {account_id}.", 404)

    content = prompt_path.read_text(encoding="utf-8")
    return _ok(account_id=account_id, prompt=content, path=str(prompt_path))


@app.put("/api/accounts/{account_id}")
async def api_account_update(account_id: str, req: AccountUpdateRequest):
    """Update account configuration and optionally write prompt content."""
    if account_id not in ("A", "B", "C"):
        raise _err(f"Invalid account: {account_id}", 400)

    # Validate publish_time format if provided
    if req.publish_time:
        import re as _re
        if not _re.match(r"^\d{2}:\d{2}$", req.publish_time):
            raise _err("publish_time must be HH:MM format.", 400)

    try:
        from src.config import LevelUpConfig
        cfg = LevelUpConfig()
    except FileNotFoundError:
        raise _err("Account config file not found. Run setup first.", 500)

    updates = req.model_dump(exclude_none=True, exclude={"prompt_content"})

    try:
        updated = cfg.save_account(account_id, updates)
    except ValueError as e:
        raise _err(str(e), 400)

    # Write prompt file if provided
    if req.prompt_content is not None:
        try:
            prompt_path = PROJECT_ROOT / updated.prompt_file
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text(req.prompt_content, encoding="utf-8")
        except Exception as e:
            raise _err(f"Failed to write prompt file: {e}", 500)

    return _ok(account={
        "id": account_id,
        "name": updated.name,
        "platforms": updated.platforms,
        "publish_time": updated.publish_time,
        "color_mood": updated.color_mood,
        "tone": updated.tone,
        "prompt_file": updated.prompt_file,
    })


@app.post("/api/accounts/{account_id}/preview")
async def api_account_preview(account_id: str, req: PreviewRequest):
    """Generate a preview image card for an account with the given color_mood."""
    if account_id not in ("A", "B", "C"):
        raise _err(f"Invalid account: {account_id}", 400)

    sample_text = (
        "This is a preview card showing how your content will look "
        "with the selected color mood and design settings."
    )
    options = PipelineOptions(
        theme="dark",
        format="story",
        provider="claude",
        mode="smart",
        color_mood=req.color_mood,
    )
    output_path = OUTPUT_DIR / f"preview_{account_id}_{req.color_mood}.png"

    loop = asyncio.get_running_loop()
    try:
        _, final_path = await loop.run_in_executor(
            None, run_pipeline, sample_text, options, output_path
        )
    except Exception as e:
        raise _err(f"Preview generation failed: {e}", 500)

    return _ok(
        account_id=account_id,
        color_mood=req.color_mood,
        preview_url=f"/output/{final_path.name}",
    )


# ---------------------------------------------------------------------------
# Watch SSE endpoint
# ---------------------------------------------------------------------------

_watch_task: asyncio.Task | None = None


@app.post("/api/watch/start")
async def api_watch_start(
    directory: str = Form(...),
    theme: str = Form("dark"),
    format: str = Form("story"),
    provider: str = Form("cli"),
):
    """Start watching a directory. Returns SSE stream of events."""
    watch_dir = Path(directory).resolve()
    if not watch_dir.is_dir():
        raise _err(f"Not a directory: {directory}")

    async def stream():
        yield f"data: {json.dumps({'type': 'started', 'directory': str(watch_dir)})}\n\n"

        from src.watcher import WATCH_EXTENSIONS
        seen: dict[str, float] = {}
        options = PipelineOptions(theme=theme, format=format, provider=provider)

        while True:
            for p in watch_dir.iterdir():
                if p.is_file() and p.suffix.lower() in WATCH_EXTENSIONS:
                    mtime = p.stat().st_mtime
                    key = str(p)
                    if key not in seen or seen[key] < mtime:
                        seen[key] = mtime
                        yield f"data: {json.dumps({'type': 'detected', 'file': p.name})}\n\n"

                        try:
                            text = p.read_text(encoding="utf-8")
                            output_path = _build_output_path(theme, format, False)
                            loop = asyncio.get_running_loop()
                            data, final_path = await loop.run_in_executor(
                                None, run_pipeline, text, options, output_path
                            )
                            yield f"data: {json.dumps({'type': 'generated', 'file': p.name, 'url': f'/output/{final_path.name}', 'title': data.get('title', '')})}\n\n"
                        except Exception as e:
                            yield f"data: {json.dumps({'type': 'error', 'file': p.name, 'error': str(e)})}\n\n"

            await asyncio.sleep(2)

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/api/watch/stop")
async def api_watch_stop():
    """Stop the watch (client should close SSE connection)."""
    return _ok()
