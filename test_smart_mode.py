#!/usr/bin/env python3
"""
Test script to demonstrate Smart Mode output format.
Shows extraction output, HTML structure, and color palettes.
"""

import json
from pathlib import Path
from src.smart_renderer import (
    FORMAT_SPECS,
    COLOR_PALETTES,
    LAYOUT_PATTERNS,
    _build_design_system_css,
    _build_layout_prompt,
)

# ===========================================================================
# Test Data: Smart Mode Extraction Output
# ===========================================================================

DEMO_EXTRACTION = {
    "title": "AI 改變內容創作",
    "key_points": [
        {"text": "Claude 3.5 模型精準度達 95%，超越業界標準", "importance": 1.0},
        {"text": "實時協作減少 60% 創作時間", "importance": 0.9},
        {"text": "成本下降至每千字 $0.02", "importance": 0.7},
        {"text": "支持 100+ 語言本地化", "importance": 0.6},
    ],
    "content_type": "news",  # news, opinion, howto, data, comparison, quote, timeline, ranking
    "layout_hint": "hero_list",  # Based on content type
    "color_mood": "dark_tech",  # Based on content tone
    "source": "Anthropic Blog 2026-03",
}

# ===========================================================================
# Display Format Specifications
# ===========================================================================

print("=" * 70)
print("SMART MODE FORMAT TEST")
print("=" * 70)

print("\n📐 Canvas Dimensions (4 formats):")
print("-" * 70)
for fmt, specs in FORMAT_SPECS.items():
    print(f"  {fmt:12} → {specs['width']}×{specs['height']}px")

# ===========================================================================
# Display Color Palettes
# ===========================================================================

print("\n🎨 Color Palettes (5 options):")
print("-" * 70)
for mood, palette_vars in COLOR_PALETTES.items():
    # Parse the first few CSS variables to show
    lines = palette_vars.strip().split(";")
    vars_preview = f"{lines[0]}; {lines[1]}; ..."
    print(f"  {mood:20} → {vars_preview}")

# ===========================================================================
# Display Layout Patterns
# ===========================================================================

print("\n📐 Layout Patterns (7 options):")
print("-" * 70)
for pattern_name, description in LAYOUT_PATTERNS.items():
    print(f"  {pattern_name:20} — {description[:50]}...")

# ===========================================================================
# Show Extraction Output Schema
# ===========================================================================

print("\n📋 Extraction Output (Smart Mode):")
print("-" * 70)
print(json.dumps(DEMO_EXTRACTION, indent=2, ensure_ascii=False))

# ===========================================================================
# Generate Sample Design System CSS
# ===========================================================================

print("\n🎨 Generated Design System CSS (story format, dark_tech palette):")
print("-" * 70)
design_css = _build_design_system_css(
    COLOR_PALETTES["dark_tech"],
    FORMAT_SPECS["story"]["width"],
    FORMAT_SPECS["story"]["height"],
)
# Show first 30 lines
lines = design_css.split("\n")
for line in lines[:30]:
    print(line)
if len(lines) > 30:
    print(f"... ({len(lines) - 30} more lines)")

# ===========================================================================
# Generate Layout Prompt
# ===========================================================================

print("\n📝 Generated Layout Prompt:")
print("-" * 70)
prompt = _build_layout_prompt(DEMO_EXTRACTION, "story", "dark_tech")
lines = prompt.split("\n")
for i, line in enumerate(lines[:50]):  # Show first 50 lines
    print(line)
if len(lines) > 50:
    print(f"\n... (truncated, {len(lines)} total lines)")

# ===========================================================================
# Example Generated HTML Structure (mock)
# ===========================================================================

print("\n" + "=" * 70)
print("EXAMPLE GENERATED HTML STRUCTURE")
print("=" * 70)

MOCK_HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 改變內容創作</title>
    <style>
        /* Design system CSS injected here */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Noto+Sans+TC:wght@400;500;700;900&display=swap');

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
          --fs-title: clamp(22px, 6vw, 32px);
          --fs-subtitle: clamp(16px, 4vw, 20px);
          --bg: #090d1a;
          --accent: #2563eb;
          --text-primary: #dde2f0;
          /* ... more CSS variables ... */
        }

        html, body {
            width: 430px;
            height: 764px;
            overflow: hidden;
            background: var(--bg);
            font-family: 'Outfit', 'Noto Sans TC', -apple-system, sans-serif;
            color: var(--text-primary);
        }

        @keyframes fadeUp {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .animated {
            animation: fadeUp 0.32s cubic-bezier(0.16,1,0.3,1) calc(var(--i, 0) * 0.08s) both;
        }

        /* Hero section styling for dark_tech mood */
        .hero {
            background: var(--accent);
            padding: 32px 24px;
            border-radius: 12px;
            margin-bottom: 24px;
        }

        .hero h1 {
            font-size: var(--fs-title);
            font-weight: 700;
            margin-bottom: 12px;
        }

        /* Supporting list */
        .points {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .point {
            display: flex;
            gap: 12px;
            padding: 12px 16px;
            background: var(--bg-card);
            border-radius: 8px;
            border: 1px solid var(--border);
        }

        .point-number {
            font-weight: 700;
            color: var(--accent);
            min-width: 24px;
        }

        .point-text {
            font-size: var(--fs-body);
            color: var(--text-secondary);
        }

        /* Footer attribution */
        .footer {
            position: absolute;
            bottom: 16px;
            width: 100%;
            text-align: center;
            font-size: var(--fs-label);
            color: var(--text-muted);
        }
    </style>
</head>
<body>
    <div class="container" style="padding: 24px;">
        <!-- Hero section with most important point -->
        <div class="hero animated" style="--i: 0;">
            <h1>AI 改變內容創作</h1>
            <p style="font-size: var(--fs-subtitle);">Claude 3.5 模型精準度達 95%</p>
        </div>

        <!-- Supporting points as numbered list -->
        <div class="points">
            <div class="point animated" style="--i: 1;">
                <span class="point-number">1</span>
                <span class="point-text">實時協作減少 60% 創作時間</span>
            </div>
            <div class="point animated" style="--i: 2;">
                <span class="point-number">2</span>
                <span class="point-text">成本下降至每千字 $0.02</span>
            </div>
            <div class="point animated" style="--i: 3;">
                <span class="point-number">3</span>
                <span class="point-text">支持 100+ 語言本地化</span>
            </div>
        </div>
    </div>

    <!-- Attribution footer -->
    <div class="footer">
        <p>Anthropic Blog 2026-03 • Designed with NOZOMI</p>
    </div>

    <!-- Watermark overlay (if provided) -->
    <div class="watermark-overlay watermark-bottom-right" style="opacity: 0.8;">
        <span class="watermark-text">My Brand</span>
    </div>
</body>
</html>"""

print(MOCK_HTML)

# ===========================================================================
# Summary
# ===========================================================================

print("\n" + "=" * 70)
print("KEY SMART MODE FEATURES")
print("=" * 70)
print("""
✓ AI generates unique HTML+CSS for each content (no fixed templates)
✓ 5 color palettes: dark_tech, warm_earth, clean_light, bold_contrast, soft_pastel
✓ 7 layout patterns: hero_list, grid, timeline, comparison, quote_centered, data_dashboard, numbered_ranking
✓ 4 canvas formats: story (430×764), square (430×430), landscape (430×242), twitter (430×215)
✓ Design system CSS injected with responsive fonts and animations
✓ Importance scores guide visual hierarchy (1.0 = most prominent)
✓ Content type and mood guide layout selection
✓ All text must be preserved exactly (no paraphrasing)
✓ Chinese text uses 'Noto Sans TC', Latin uses 'Outfit'
✓ Watermark and thread badges injected post-generation
✓ No JavaScript, no external images (except Google Fonts)
✓ Perfect fit to exact canvas dimensions
""")

print("=" * 70)
print("To test with real API:\n")
print("  python main.py --file test.txt --mode smart --format story")
print("  python main.py --text \"Article text...\" --mode smart --format square")
print("\nRequired: Set ANTHROPIC_API_KEY environment variable")
print("=" * 70)
