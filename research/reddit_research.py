#!/usr/bin/env python3
"""
Reddit Research Agent — Jean-Luc SEO Machine

Ищет живые цитаты продажников по заданным темам через ПУБЛИЧНЫЙ JSON API
Reddit. Без OAuth, без developer-app, без секретов.

Запуск:
    pip install requests
    python research/reddit_research.py

В GitHub Actions: см. .github/workflows/reddit-research.yml
(никаких секретов не требует).

Принцип:
    Reddit отдаёт JSON на любой странице, если добавить ".json" к URL.
    Например: https://www.reddit.com/r/sales/search.json?q=foo
    Лимит: ~60 запросов в минуту с одного IP. Скрипт это уважает.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests  # type: ignore
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

# ── Subreddits и темы для поиска ──────────────────────────────────────────────
SUBREDDITS = ["sales", "Entrepreneur", "smallbusiness", "freelance", "consulting"]

QUERIES = [
    # Возражения
    "too expensive objection",
    "prospect said too expensive",
    "client ghosted after proposal",
    "need to think about it",
    "already have a vendor",
    "no budget objection",
    "need to check with my boss",
    # Закрытие
    "closing the deal tips",
    "soft close sales",
    "next step after sales call",
    # AI для продаж
    "ChatGPT for sales",
    "AI sales assistant",
    "AI for cold outreach",
    # Mindset и проблемы
    "fear of selling",
    "hate cold calling",
    "scared to quote price",
    "marketing leads are garbage",
    "RFP waste of time",
]

MIN_SCORE = 5
MIN_COMMENTS = 3
POST_LIMIT = 10
TIME_FILTER = "year"
COMMENT_LIMIT = 5

# Reddit просит честный User-Agent. Без него — 429 Rate Limited.
USER_AGENT = "seo-research-bot/1.2 (by jeanluc-seo-machine; contact via repo)"
REQUEST_DELAY_SEC = 1.2  # ~50 req/min, в пределах лимита

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_JSON = SCRIPT_DIR / "reddit_results.json"
DIGEST_MD = SCRIPT_DIR / "reddit_digest.md"


def reddit_get(url: str, params: dict | None = None) -> dict | None:
    """GET wrapper: проверяет статус, парсит JSON, держит rate-limit."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
    except requests.RequestException as e:
        print(f"    network error: {e}", flush=True)
        return None

    if r.status_code == 429:
        # Rate limited — подождём и продолжим
        wait = int(r.headers.get("X-Ratelimit-Reset", "10"))
        print(f"    rate-limited, waiting {wait}s", flush=True)
        time.sleep(wait)
        return None
    if r.status_code != 200:
        print(f"    HTTP {r.status_code} on {r.url}", flush=True)
        return None
    try:
        return r.json()
    except json.JSONDecodeError:
        return None


def search_subreddit(subreddit: str, query: str) -> list[dict]:
    """Search posts in a subreddit via public JSON API."""
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {
        "q": query,
        "restrict_sr": "1",
        "sort": "top",
        "t": TIME_FILTER,
        "limit": str(POST_LIMIT),
    }
    data = reddit_get(url, params=params)
    time.sleep(REQUEST_DELAY_SEC)
    if not data:
        return []
    children = data.get("data", {}).get("children", [])

    results: list[dict] = []
    for child in children:
        post = child.get("data") or {}
        score = post.get("score", 0)
        num_comments = post.get("num_comments", 0)
        if score < MIN_SCORE or num_comments < MIN_COMMENTS:
            continue

        post_id = post.get("id", "")
        permalink = post.get("permalink", "")
        comments = fetch_top_comments(subreddit, post_id) if post_id else []

        results.append({
            "subreddit": subreddit,
            "query": query,
            "title": post.get("title", ""),
            "url": f"https://reddit.com{permalink}",
            "score": score,
            "num_comments": num_comments,
            "selftext": (post.get("selftext") or "")[:600],
            "top_comments": comments,
            "date": datetime.fromtimestamp(
                post.get("created_utc", 0), tz=timezone.utc
            ).strftime("%Y-%m-%d"),
        })
    return results


def fetch_top_comments(subreddit: str, post_id: str) -> list[dict]:
    """Fetch top comments for a post via public JSON API."""
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
    params = {"sort": "top", "limit": str(COMMENT_LIMIT)}
    data = reddit_get(url, params=params)
    time.sleep(REQUEST_DELAY_SEC)
    if not data or not isinstance(data, list) or len(data) < 2:
        return []

    comments_listing = data[1].get("data", {}).get("children", [])
    out: list[dict] = []
    for c in comments_listing[:COMMENT_LIMIT]:
        kind = c.get("kind", "")
        body = (c.get("data") or {}).get("body", "")
        if kind != "t1" or not body or len(body) < 30:
            continue
        out.append({
            "author": (c.get("data") or {}).get("author", "?"),
            "score": (c.get("data") or {}).get("score", 0),
            "body": body[:500],
        })
    return out


def merge_with_existing(new_results: list[dict]) -> list[dict]:
    """Merge new results with existing JSON, dedupe by URL, keep highest-score version."""
    existing: list[dict] = []
    if RESULTS_JSON.exists():
        try:
            existing = json.loads(RESULTS_JSON.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            existing = []

    by_url: dict[str, dict] = {}
    for item in existing + new_results:
        url = item.get("url")
        if not url:
            continue
        prev = by_url.get(url)
        if prev is None or item.get("score", 0) > prev.get("score", 0):
            by_url[url] = item

    return sorted(by_url.values(), key=lambda x: x.get("score", 0), reverse=True)


def write_digest(results: list[dict], top_n: int = 30) -> None:
    """Write a human-readable markdown digest."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    top = sorted(results, key=lambda x: x.get("score", 0), reverse=True)[:top_n]

    lines: list[str] = [
        "# Reddit research digest",
        f"Last updated: {today}",
        f"Total posts in archive: {len(results)} | Showing top {len(top)} by score",
        "",
        "Используется как сырьё для новых статей. Когда видишь горячую тему/цитату —",
        "добавляй её в `research/topics-ru-batch3.md` (или новую batch-карточку).",
        "",
        "---",
        "",
    ]

    for i, item in enumerate(top, 1):
        lines.append(f"## {i}. {item.get('title', '(no title)')}")
        lines.append(
            f"r/{item.get('subreddit')} · {item.get('score', 0)} upvotes · "
            f"{item.get('num_comments', 0)} comments · {item.get('date', '?')}"
        )
        lines.append("")
        lines.append(f"Query that found this: `{item.get('query', '?')}`")
        lines.append("")
        lines.append(f"[Open thread →]({item.get('url', '')})")
        lines.append("")
        if item.get("selftext"):
            lines.append("**Post body (first 300 chars):**")
            lines.append("")
            lines.append("> " + item["selftext"][:300].replace("\n", " ").strip() + "...")
            lines.append("")
        comments = item.get("top_comments") or []
        if comments:
            lines.append("**Top comments:**")
            lines.append("")
            for c in comments[:3]:
                snippet = c.get("body", "")[:300].replace("\n", " ").strip()
                lines.append(f"- _{c.get('author', '?')}_ ({c.get('score', 0)} upvotes): \"{snippet}\"")
            lines.append("")
        lines.append("---")
        lines.append("")

    DIGEST_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    print("=" * 60)
    print(f"Reddit research run · {datetime.now(timezone.utc).isoformat()}")
    print("Mode: public JSON API (no auth required)")
    print("=" * 60)

    new_results: list[dict] = []
    for subreddit in SUBREDDITS:
        for query in QUERIES:
            print(f"  [{subreddit}] '{query}'...", flush=True)
            try:
                posts = search_subreddit(subreddit, query)
            except Exception as e:  # noqa: BLE001
                print(f"    error: {e}", flush=True)
                continue
            new_results.extend(posts)
            print(f"    +{len(posts)} posts (after filter)", flush=True)

    merged = merge_with_existing(new_results)
    RESULTS_JSON.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_digest(merged, top_n=30)

    print("\n" + "=" * 60)
    print(f"New posts this run: {len(new_results)}")
    print(f"Total in archive:   {len(merged)}")
    print(f"Saved JSON:         {RESULTS_JSON}")
    print(f"Saved digest:       {DIGEST_MD}")
    print("=" * 60)
    return 0 if merged else 2


if __name__ == "__main__":
    sys.exit(main())
