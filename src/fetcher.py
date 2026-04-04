"""
fetcher.py - URL content fetching for imgGen.

Shared implementation used by both main.py (single-run) and batch.py.
Raises RuntimeError on failure so callers can wrap as needed.

Threads URLs are handled specially: Googlebot UA causes Meta to return
static HTML containing og: meta tags and embedded thread_items JSON.
"""

import html as html_module
import json
import re
from urllib.parse import urlparse

import httpx
import trafilatura

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Googlebot UA causes Threads to return full static HTML with thread_items JSON.
# Regular browser UAs get a JS-rendered shell with no content.
_THREADS_USER_AGENTS = [
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/128.0.6613.119 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.119 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
]

_THREADS_DOMAINS = {"threads.com", "threads.net"}


def _is_threads_url(url: str) -> bool:
    try:
        host = urlparse(url).hostname or ""
        host = host.removeprefix("www.")
        return host in _THREADS_DOMAINS
    except Exception:
        return False


def _extract_meta(page_html: str, prop: str) -> str:
    m = re.search(rf'<meta property="{re.escape(prop)}"[^>]*content="([^"]*)"', page_html)
    if not m:
        m = re.search(rf'<meta[^>]*content="([^"]*)"[^>]*property="{re.escape(prop)}"', page_html)
    return html_module.unescape(m.group(1)) if m else ""


def _extract_thread_items(page_html: str) -> list:
    m = re.search(r'"thread_items":\s*(\[.*?\])\s*,\s*"thread_type"', page_html, re.DOTALL)
    if not m:
        return []
    try:
        return json.loads(m.group(1))
    except Exception:
        return []


def _parse_post(item: dict) -> dict:
    post = item.get("post", {})
    user = post.get("user", {})
    caption = post.get("caption") or {}
    text = caption.get("text", "") if isinstance(caption, dict) else str(caption)
    return {
        "username": user.get("username", ""),
        "full_name": user.get("full_name", ""),
        "text": text.strip(),
        "like_count": post.get("like_count", 0),
        "reply_count": post.get("text_post_app_info", {}).get("direct_reply_count", 0),
    }


def _fetch_threads_content(url: str) -> str:
    """Fetch a Threads post using Googlebot UA and extract post text.

    Returns plain text combining author info and post body.
    Falls back to og:description if thread_items JSON is not found.

    Raises:
        RuntimeError: On HTTP error or network failure.
    """
    import random
    headers = {
        "User-Agent": random.choice(_THREADS_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Cache-Control": "no-cache",
    }

    try:
        response = httpx.get(url, headers=headers, follow_redirects=True, timeout=15)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"HTTP error fetching URL: {e.response.status_code} {e.response.reason_phrase}"
        ) from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Network error fetching URL: {e}") from e

    page_html = response.text
    items = _extract_thread_items(page_html)

    if items:
        posts = [_parse_post(it) for it in items]
        parts = []
        for p in posts:
            if p["username"]:
                parts.append(f"@{p['username']} ({p['full_name']})" if p["full_name"] else f"@{p['username']}")
            if p["text"]:
                parts.append(p["text"])
        text = "\n\n".join(parts).strip()
        if text:
            return text

    # Fallback: og:description contains post preview text
    og_desc = _extract_meta(page_html, "og:description")
    og_title = _extract_meta(page_html, "og:title")
    fallback = "\n\n".join(filter(None, [og_title, og_desc])).strip()
    if fallback:
        return fallback

    raise RuntimeError(
        "Could not extract content from Threads URL. "
        "The post may be private or the page structure may have changed."
    )


def _strip_html(text: str) -> str:
    """Fallback HTML cleaner using regex (removes tags, scripts, styles)."""
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_article_text(html: str, url: str) -> str:
    """Extract article body text using trafilatura, fallback to regex strip.

    Args:
        html: Raw HTML string.
        url: The source URL (helps trafilatura with extraction heuristics).

    Returns:
        Cleaned article text.
    """
    result = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=False,
        favor_precision=True,
    )
    if result and len(result) > 50:
        return result
    # Fallback to regex strip
    return _strip_html(html)


def fetch_url_content(url: str) -> str:
    """Fetch text content from a URL, stripping HTML if needed.

    Threads URLs are handled with Googlebot UA to extract post text.

    Args:
        url: The URL to fetch.

    Returns:
        Plain text content of the page.

    Raises:
        RuntimeError: On HTTP error or network failure.
    """
    if _is_threads_url(url):
        return _fetch_threads_content(url)

    try:
        response = httpx.get(
            url,
            headers={"User-Agent": _USER_AGENT},
            follow_redirects=True,
            timeout=30,
        )
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "html" in content_type:
            return _extract_article_text(response.text, url)
        return response.text

    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            f"HTTP error fetching URL: {e.response.status_code} {e.response.reason_phrase}"
        ) from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Network error fetching URL: {e}") from e
