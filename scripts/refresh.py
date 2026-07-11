#!/usr/bin/env python3
"""Enablement Radar — daily asset checker.

Fetches each tracked public page, hashes its visible text, and compares
against the previous run. Writes data/data.json (read by index.html) and
stores a stripped-text snapshot per asset in data/snapshots/ so that
changes are diffable in git history.

Data discipline: this script never invents dates. detectedLastUpdated is
set only when an explicit 'Last updated <date>' marker is found in the
page text; otherwise the field is null and the UI keeps its seed value.

Zero external dependencies — stdlib only (urllib), so the GitHub Actions
job needs no pip install.
"""

import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "data.json"
SNAP_DIR = ROOT / "data" / "snapshots"

ASSETS = [
    {
        "id": "ultra-access",
        "url": "https://knowledge.workspace.google.com/admin/generative-ai/workspace-with-gemini/ai-ultra-access",
    },
    {
        "id": "nblm-licensing",
        "url": "https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/set-up-licensing",
    },
    {
        "id": "nblm-gemini",
        "url": "https://docs.cloud.google.com/gemini/enterprise/docs/access-notebooklm",
    },
    {
        "id": "ai-addons",
        "url": "https://knowledge.workspace.google.com/admin/getting-started/editions/compare-google-ai-expansion-add-ons",
    },
    {
        "id": "io-blog",
        "url": "https://blog.google/products-and-platforms/products/google-one/google-ai-subscriptions/",
    },
    {
        "id": "gemini-agent-platform",
        "url": "https://cloud.google.com/products/gemini-enterprise-agent-platform/pricing",
    },
    {
        "id": "gemini-api-pricing",
        "url": "https://ai.google.dev/gemini-api/docs/pricing",
    },
    {
        "id": "labs-google",
        "url": "https://labs.google/",
    },
    {
        "id": "openai-pricing",
        "url": "https://openai.com/business/pricing/",
    },
    {
        "id": "anthropic-pricing",
        "url": "https://claude.com/pricing",
    },
    {
        "id": "perplexity-pricing",
        "url": "https://www.perplexity.ai/enterprise/pricing",
    },
    {
        "id": "notion-pricing",
        "url": "https://www.notion.com/pricing",
    },
    {
        "id": "figma-pricing",
        "url": "https://www.figma.com/pricing/",
    },
]

UA = "Mozilla/5.0 (compatible; EnablementRadar/1.0; +https://github.com)"

# Explicit last-updated markers only — never inferred from other dates on the page.
DATE_PATTERNS = [
    re.compile(r"last\s+updated[:\s]+(\d{4}-\d{2}-\d{2})", re.I),
    re.compile(
        r"last\s+updated[:\s]+([A-Z][a-z]+ \d{1,2}, \d{4})", re.I
    ),
]


def strip_html(html: str) -> str:
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def parse_marker_date(text: str):
    for pat in DATE_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        raw = m.group(1)
        try:
            if re.match(r"\d{4}-\d{2}-\d{2}", raw):
                return raw
            return datetime.strptime(raw, "%B %d, %Y").strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def fetch(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def main() -> int:
    previous = {}
    if DATA_FILE.exists():
        try:
            for rec in json.loads(DATA_FILE.read_text(encoding="utf-8")).get("assets", []):
                previous[rec["id"]] = rec
        except (json.JSONDecodeError, KeyError):
            pass

    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out, any_change = [], False

    for asset in ASSETS:
        prev = previous.get(asset["id"], {})
        rec = {
            "id": asset["id"],
            "url": asset["url"],
            "lastChecked": now,
            "contentHash": prev.get("contentHash"),
            "detectedLastUpdated": prev.get("detectedLastUpdated"),
            "changedSinceLastRun": False,
            "fetchError": None,
        }
        try:
            status, html = fetch(asset["url"])
            if status != 200:
                rec["fetchError"] = f"HTTP {status}"
            else:
                text = strip_html(html)
                digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                if prev.get("contentHash") and prev["contentHash"] != digest:
                    rec["changedSinceLastRun"] = True
                    any_change = True
                rec["contentHash"] = digest
                marker = parse_marker_date(text)
                if marker:
                    rec["detectedLastUpdated"] = marker
                (SNAP_DIR / f"{asset['id']}.txt").write_text(text, encoding="utf-8")
        except Exception as exc:  # network errors, timeouts, redirects to consent pages
            rec["fetchError"] = type(exc).__name__
        out.append(rec)
        print(f"{asset['id']}: error={rec['fetchError']} changed={rec['changedSinceLastRun']} "
              f"detected={rec['detectedLastUpdated']}")

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps({"lastRun": now, "assets": out}, indent=2), encoding="utf-8"
    )
    print(f"\nWrote {DATA_FILE.relative_to(ROOT)} · changes detected: {any_change}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
