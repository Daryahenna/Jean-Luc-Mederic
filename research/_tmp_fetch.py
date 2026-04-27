import argparse
import json
import gzip
import re
import sys
import urllib.parse
import urllib.request


UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"


def http_get(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.7,en;q=0.6",
            "Accept-Encoding": "gzip",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        enc = (resp.headers.get("Content-Encoding") or "").lower()

    if enc == "gzip":
        try:
            raw = gzip.decompress(raw)
        except Exception:
            pass

    return raw.decode("utf-8", errors="ignore")


def bing_search(query: str, count: int = 10, mkt: str = "ru-RU", setlang: str = "ru"):
    # PowerShell in this environment may mangle Cyrillic in argv.
    # Allow passing percent-encoded queries (ASCII-safe): "%D0%BF%D1%80...".
    if "%" in query:
        try:
            query = urllib.parse.unquote_plus(query)
        except Exception:
            pass
    url = (
        "https://www.bing.com/search?"
        + urllib.parse.urlencode(
            {
                "q": query,
                "count": str(count),
                "mkt": mkt,
                "setlang": setlang,
            }
        )
    )
    html = http_get(url)
    results = []
    for m in re.finditer(r'<li class="b_algo[^"]*".*?<h2><a href="(.*?)"[^>]*>(.*?)</a>', html, re.S):
        link = m.group(1).strip()
        title = re.sub(r"<.*?>", "", m.group(2)).strip()
        results.append({"title": title, "url": link})
        if len(results) >= count:
            break
    return {"query": query, "search_url": url, "results": results}


def bing_proxy_search(query: str, count: int = 10, mkt: str = "ru-RU", setlang: str = "ru"):
    # Uses r.jina.ai to bypass heavy JS / bot checks.
    bing_url = (
        "https://www.bing.com/search?"
        + urllib.parse.urlencode(
            {
                "q": query,
                "count": str(count),
                "mkt": mkt,
                "setlang": setlang,
            }
        )
    )
    proxy_url = "https://r.jina.ai/http://" + bing_url
    md = http_get(proxy_url)

    # Extract blocks like:
    # 1. [domain url](ck/a...)
    # ## [Title](ck/a...)
    results = []
    cur = {}
    for line in md.splitlines():
        m = re.match(r"^\d+\.\s+\[.*?\s+(https?://\S+)\]\(.*\)$", line.strip())
        if m:
            cur = {"shown_url": m.group(1)}
            continue
        m = re.match(r"^##\s+\[(.+?)\]\((.+?)\)", line.strip())
        if m and cur is not None:
            title = m.group(1).strip()
            link = m.group(2).strip()
            shown = cur.get("shown_url")
            results.append({"title": title, "url": shown or link})
            cur = {}
            if len(results) >= count:
                break

    return {"query": query, "proxy_url": proxy_url, "results": results}


def bukvarix(query: str):
    if "%" in query:
        try:
            query = urllib.parse.unquote_plus(query)
        except Exception:
            pass
    url = "https://bukvarix.com/keywords/?" + urllib.parse.urlencode({"q": query})
    html = http_get(url)
    m = re.search(r'"data"\s*:\s*[^\[]*(\[\[.*?\]\])', html, re.S)
    if not m:
        return {"query": query, "url": url, "rows": []}
    payload = m.group(1)
    try:
        rows = json.loads(payload)
    except Exception:
        rows = []
        for rm in re.finditer(r'\[\s*"(.*?)"\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]', payload):
            rows.append([rm.group(1), int(rm.group(2)), int(rm.group(3)), int(rm.group(4)), int(rm.group(5))])
    return {"query": query, "url": url, "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bing")
    ap.add_argument("--bingproxy")
    ap.add_argument("--bukvarix")
    ap.add_argument("--count", type=int, default=10)
    args = ap.parse_args()

    out = {}
    if args.bing:
        out["bing"] = bing_search(args.bing, count=args.count)
    if args.bingproxy:
        out["bingproxy"] = bing_proxy_search(args.bingproxy, count=args.count)
    if args.bukvarix:
        out["bukvarix"] = bukvarix(args.bukvarix)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
