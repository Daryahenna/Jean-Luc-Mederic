#!/usr/bin/env python3
"""
Translate Jekyll guide files from one language to another using OpenAI API.

Reads RU guides, sends them to OpenAI with a system prompt (translation spec),
writes the output as new files in the target language directory.

Safety guards:
  - Never modifies existing files in the source directory.
  - Skips target files that already exist (no overwrites).
  - Validates output before writing (checks frontmatter + lang field).

Usage:
    python translate.py --source-lang ru --target-lang fr \\
        --prompt prompts/opencode-translate-fr.md \\
        --source-dir _guides/ru \\
        --target-dir _guides/fr \\
        --model gpt-4o \\
        [--files slug1,slug2]

Env: OPENAI_API_KEY must be set.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml
from openai import OpenAI

# RU → FR slug map. Mirrors the table in prompts/opencode-translate-fr.md.
SLUG_MAP_FR = {
    "objection-dorogo": "objection-c-est-cher",
    "objection-podumat": "objection-je-vais-reflechir",
    "objection-pozhe": "objection-plus-tard",
    "objection-net-vremeni": "objection-pas-le-temps",
    "objection-nado-posovetovatsya": "objection-je-dois-en-parler",
    "closing-questions": "questions-de-cloture",
    "prospecting-plan": "plan-de-prospection",
    "kp-ghosting": "client-disparu-apres-devis",
}

# RU → EN slug map. Will be used when EN target is requested.
SLUG_MAP_EN = {
    "objection-dorogo": "objection-its-too-expensive",
    "objection-podumat": "objection-let-me-think",
    "objection-pozhe": "objection-not-now",
    "objection-net-vremeni": "objection-no-time",
    "objection-nado-posovetovatsya": "objection-need-to-consult",
    "closing-questions": "closing-questions",
    "prospecting-plan": "prospecting-plan",
    "kp-ghosting": "client-ghosted-after-proposal",
}

SLUG_MAPS = {
    "fr": SLUG_MAP_FR,
    "en": SLUG_MAP_EN,
}

# Models that use the new max_completion_tokens parameter (reasoning + GPT-5 family).
# Older models (gpt-4o, gpt-4o-mini, gpt-4-turbo) use max_tokens.
NEW_PARAM_MODEL_PREFIXES = ("o1", "o3", "o4", "gpt-5")


def parse_frontmatter(text: str) -> tuple[dict, str] | tuple[None, None]:
    """Split a markdown file into (frontmatter_dict, body_str). Returns (None, None) on failure."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        return None, None
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None, None
    return fm, m.group(2)


def validate_translation(text: str, target_lang: str, expected_slug: str) -> list[str]:
    """Return a list of validation errors. Empty list means OK."""
    errors: list[str] = []

    fm, body = parse_frontmatter(text)
    if fm is None:
        errors.append("frontmatter missing or invalid YAML")
        return errors

    if fm.get("lang") != target_lang:
        errors.append(f"frontmatter lang is {fm.get('lang')!r}, expected {target_lang!r}")

    if fm.get("slug") != expected_slug:
        errors.append(f"frontmatter slug is {fm.get('slug')!r}, expected {expected_slug!r}")

    required_fields = [
        "title", "description", "promise", "category", "chips",
        "hero_emoji", "author", "date", "reading_time", "lang", "slug", "faq",
    ]
    for field in required_fields:
        if field not in fm:
            errors.append(f"frontmatter missing field: {field}")

    if "faq" in fm and isinstance(fm["faq"], list):
        if len(fm["faq"]) != 4:
            errors.append(f"FAQ has {len(fm['faq'])} items, expected 4")

    body_text = body or ""
    if "callout is-key" not in body_text:
        errors.append("body missing main 'callout is-key' block")
    if "{% include paris-banner.html" not in body_text:
        errors.append("body missing paris-banner include")
    if "<div class=\"dialog\">" not in body_text:
        errors.append("body missing dialog block")

    if target_lang == "fr":
        if re.search(r"<span class=\"who\">Менеджер", body_text):
            errors.append("dialog uses 'Менеджер' instead of 'Vendeur' (Russian leaked)")
        if "Жан-Люк" in body_text:
            errors.append("text contains 'Жан-Люк' (Russian leaked)")
    if target_lang == "en":
        if re.search(r"<span class=\"who\">Менеджер", body_text):
            errors.append("dialog uses 'Менеджер' instead of English equivalent")

    return errors


def strip_code_fence(text: str) -> str:
    """Some models wrap output in ```markdown ... ```. Strip if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text


def call_openai(
    client: OpenAI,
    model: str,
    system_prompt: str,
    user_msg: str,
    max_output_tokens: int = 16000,
) -> str:
    """Single OpenAI chat completion call. Handles new vs old param names."""
    use_new_param = model.startswith(NEW_PARAM_MODEL_PREFIXES)

    kwargs = dict(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
    )
    if use_new_param:
        kwargs["max_completion_tokens"] = max_output_tokens
    else:
        kwargs["max_tokens"] = max_output_tokens
        # Reasonable default temperature for translation: low but not zero.
        kwargs["temperature"] = 0.3

    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def translate_one(
    client: OpenAI,
    model: str,
    system_prompt: str,
    source_path: Path,
    target_lang: str,
    target_slug: str,
) -> tuple[str, list[str]]:
    """Translate one guide file. Returns (translated_text, validation_errors)."""
    source_text = source_path.read_text(encoding="utf-8")
    user_msg = (
        f"Translate this Russian guide to {target_lang.upper()}. "
        f"Use slug '{target_slug}' in the frontmatter. "
        f"Output ONLY the full translated markdown file (frontmatter + body). "
        f"No preamble, no explanation, no code fences.\n\n"
        f"--- SOURCE FILE: {source_path.name} ---\n\n"
        f"{source_text}"
    )

    print(f"  → Calling {model}...", flush=True)
    raw = call_openai(client, model, system_prompt, user_msg)
    output = strip_code_fence(raw)

    errors = validate_translation(output, target_lang, target_slug)
    return output, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Translate Jekyll guides via OpenAI API.")
    parser.add_argument("--source-lang", required=True)
    parser.add_argument("--target-lang", required=True)
    parser.add_argument("--prompt", required=True, help="Path to system prompt file (markdown)")
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--target-dir", required=True)
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument("--files", default="", help="Comma-separated source slugs (omit ext). Empty = all untranslated.")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY env var not set", file=sys.stderr)
        return 1

    source_dir = Path(args.source_dir)
    target_dir = Path(args.target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    prompt_path = Path(args.prompt)
    if not prompt_path.exists():
        print(f"ERROR: prompt file not found: {prompt_path}", file=sys.stderr)
        return 1
    system_prompt = prompt_path.read_text(encoding="utf-8")

    slug_map = SLUG_MAPS.get(args.target_lang)
    if not slug_map:
        print(f"ERROR: no slug map defined for target lang {args.target_lang!r}", file=sys.stderr)
        return 1

    if args.files.strip():
        wanted_slugs = [s.strip() for s in args.files.split(",") if s.strip()]
    else:
        wanted_slugs = [p.stem for p in sorted(source_dir.glob("*.md"))]

    client = OpenAI(api_key=api_key)

    log_lines = [
        f"# Translation log {args.source_lang.upper()} → {args.target_lang.upper()}",
        f"Date: {datetime.utcnow().isoformat()}Z",
        f"Model: {args.model}",
        f"Provider: OpenAI",
        "",
    ]
    translated: list[str] = []
    skipped: list[tuple[str, str]] = []
    failed: list[tuple[str, list[str]]] = []

    for slug in wanted_slugs:
        source_path = source_dir / f"{slug}.md"
        if not source_path.exists():
            skipped.append((slug, "source file not found"))
            print(f"SKIP: {slug} (source not found)")
            continue

        target_slug = slug_map.get(slug)
        if not target_slug:
            skipped.append((slug, "no slug map entry"))
            print(f"SKIP: {slug} (no slug map entry for target lang)")
            continue

        target_path = target_dir / f"{target_slug}.md"
        if target_path.exists():
            skipped.append((target_slug, "target already exists"))
            print(f"SKIP: {target_slug} (already exists at {target_path})")
            continue

        print(f"TRANSLATE: {slug} → {target_slug}")
        try:
            output, errors = translate_one(
                client=client,
                model=args.model,
                system_prompt=system_prompt,
                source_path=source_path,
                target_lang=args.target_lang,
                target_slug=target_slug,
            )
        except Exception as e:  # noqa: BLE001
            failed.append((target_slug, [f"API error: {e}"]))
            print(f"  ✗ API error: {e}")
            continue

        if errors:
            failed.append((target_slug, errors))
            warn_header = (
                "<!-- TRANSLATION VALIDATION FAILED. Review before merging. Errors:\n"
                + "\n".join(f"  - {e}" for e in errors)
                + "\n-->\n"
            )
            target_path.write_text(warn_header + output, encoding="utf-8")
            print(f"  ⚠ Wrote with validation errors: {len(errors)} issue(s)")
            for e in errors:
                print(f"     - {e}")
        else:
            target_path.write_text(output, encoding="utf-8")
            translated.append(target_slug)
            print(f"  ✓ Wrote {target_path}")

    log_lines.append("## Translated successfully")
    if translated:
        for s in translated:
            log_lines.append(f"- {s}.md")
    else:
        log_lines.append("(none)")
    log_lines.append("")
    log_lines.append("## Skipped")
    if skipped:
        for s, reason in skipped:
            log_lines.append(f"- {s} — {reason}")
    else:
        log_lines.append("(none)")
    log_lines.append("")
    log_lines.append("## Validation failures (need human review)")
    if failed:
        for s, errs in failed:
            log_lines.append(f"- {s}.md")
            for e in errs:
                log_lines.append(f"    - {e}")
    else:
        log_lines.append("(none)")

    log_path = target_dir / "_TRANSLATION_LOG.md"
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"\nLog written to {log_path}")
    print(f"Translated: {len(translated)} | Skipped: {len(skipped)} | Failed: {len(failed)}")

    if not translated and (failed or not skipped):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
