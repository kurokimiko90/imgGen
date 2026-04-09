#!/bin/bash

# Test Smart Mode Examples
# This script demonstrates various Smart Mode configurations

set -e

PROJECT_DIR="/Users/huruoning/Documents/project/imgGen"
cd "$PROJECT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Smart Mode Testing Guide${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Check API key
echo -e "${YELLOW}1. Environment Check${NC}"
echo "---"
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  ANTHROPIC_API_KEY is not set"
    echo "To use Smart Mode with Claude API:"
    echo "  export ANTHROPIC_API_KEY='your-key-here'"
else
    echo "✓ ANTHROPIC_API_KEY is set"
fi
echo

# Show available models
echo -e "${YELLOW}2. Available Claude Models${NC}"
echo "---"
echo "• sonnet  (default) — Fast, cost-effective, excellent quality"
echo "• opus             — Premium design, deeper reasoning"
echo

# Show format options
echo -e "${YELLOW}3. Output Formats${NC}"
echo "---"
echo "• story (430×764)       — Instagram Story / TikTok"
echo "• square (430×430)      — Social media feed"
echo "• landscape (430×242)   — Web / Email header"
echo "• twitter (430×215)     — Twitter card"
echo

# Test configuration
echo -e "${YELLOW}4. Typical Commands${NC}"
echo "---"
echo

echo -e "${GREEN}Example 1: Simple Smart Mode (Sonnet)${NC}"
echo "$ python main.py --file article.txt --mode smart --format story"
echo "→ Extracts content, generates unique HTML+CSS layout, screenshots as PNG"
echo

echo -e "${GREEN}Example 2: Premium Design (Opus)${NC}"
echo "$ python main.py --text 'Article...' --mode smart --model opus --format square"
echo "→ Uses stronger model for deeper design reasoning"
echo

echo -e "${GREEN}Example 3: Multi-format Output${NC}"
echo "$ python main.py --url https://example.com --mode smart \\"
echo "  --formats story,square,twitter,landscape"
echo "→ Generates 4 different format outputs"
echo

echo -e "${GREEN}Example 4: Thread Mode${NC}"
echo "$ python main.py --file article.txt --mode smart --thread"
echo "→ One card per key point with sequence numbering (1/4, 2/4, ...)"
echo

echo -e "${GREEN}Example 5: With Watermark${NC}"
echo "$ python main.py --file article.txt --mode smart \\"
echo "  --watermark logo.png --brand-name '@myusername' \\"
echo "  --watermark-position bottom-right --watermark-opacity 0.8"
echo "→ Adds logo and text watermark overlay"
echo

echo -e "${GREEN}Example 6: Batch Processing${NC}"
echo "$ echo 'https://article1.com' > batch.txt"
echo "$ echo 'https://article2.com' >> batch.txt"
echo "$ python main.py --batch batch.txt --workers 3 --mode smart"
echo "→ Processes multiple articles concurrently"
echo

# Color palettes
echo -e "${YELLOW}5. Color Palettes (Auto-selected by AI)${NC}"
echo "---"
echo "• dark_tech      — Dark blue (tech, business, analysis)"
echo "• warm_earth     — Warm brown (lifestyle, wellness)"
echo "• clean_light    — Minimal white/blue (editorial)"
echo "• bold_contrast  — High contrast orange/black (marketing)"
echo "• soft_pastel    — Soft pink/purple (gentle, brand stories)"
echo

# Layout patterns
echo -e "${YELLOW}6. Layout Patterns (Auto-selected by AI)${NC}"
echo "---"
echo "• hero_list           — Hero section + supporting list"
echo "• grid                — 2-column or stacked card grid"
echo "• timeline            — Vertical timeline with steps"
echo "• comparison          — Side-by-side or stacked contrast"
echo "• quote_centered      — Large centered quote"
echo "• data_dashboard      — Stats and metrics"
echo "• numbered_ranking    — Top-N ranked list"
echo

# Extraction output
echo -e "${YELLOW}7. Smart Mode Extraction Output${NC}"
echo "---"
cat << 'JSON'
{
  "title": "Content title (max 15 chars)",
  "key_points": [
    {
      "text": "Most important point",
      "importance": 1.0
    },
    {
      "text": "Supporting point",
      "importance": 0.8
    }
  ],
  "content_type": "news|opinion|howto|data|...",
  "layout_hint": "hero_list|grid|timeline|...",
  "color_mood": "dark_tech|warm_earth|...",
  "source": "Source attribution"
}
JSON
echo

# Design system features
echo -e "${YELLOW}8. Design System Features${NC}"
echo "---"
echo "✓ Responsive typography with clamp()"
echo "✓ CSS variable-based color palette"
echo "✓ FadeUp staggered animations"
echo "✓ Exact canvas dimensions (no scrolling)"
echo "✓ Google Fonts: Outfit (Latin) + Noto Sans TC (Chinese)"
echo "✓ No JavaScript, no external images"
echo "✓ Watermark and thread badge injection"
echo

# Performance notes
echo -e "${YELLOW}9. Performance & Cost${NC}"
echo "---"
echo "Sonnet (default):"
echo "  • Generation time: 2–5 seconds"
echo "  • Cost per card: $0.05–0.10"
echo "  • Best for: Daily use, high volume"
echo
echo "Opus:"
echo "  • Generation time: 3–8 seconds"
echo "  • Cost per card: $0.20–0.40"
echo "  • Best for: Critical content, special designs"
echo

# Testing checklist
echo -e "${YELLOW}10. Testing Checklist${NC}"
echo "---"
echo "□ Set ANTHROPIC_API_KEY environment variable"
echo "□ Run simple test: python main.py --text 'Test' --mode smart"
echo "□ Verify output PNG in ./output/ directory"
echo "□ Check console for any validation errors"
echo "□ Test with Opus model for premium quality"
echo "□ Test multi-format: --formats story,square,twitter"
echo "□ Test thread mode: --thread"
echo "□ Test with URL fetching: --url https://..."
echo

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Setup Complete!${NC}"
echo -e "${BLUE}Ready to test Smart Mode 🚀${NC}"
echo -e "${BLUE}========================================${NC}"
