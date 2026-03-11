"""Markdown text utilities."""

from __future__ import annotations

import re

FENCED_BLOCK_RE = re.compile(r"^(`{3,}|~{3,})", re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`[^`]+`")
MD_LINK_RE = re.compile(r"!?\[([^\]]*)\]\(([^)]+)\)")


def strip_code(text: str) -> str:
    text = _strip_fenced_blocks(text)
    text = _strip_indented_blocks(text)
    text = INLINE_CODE_RE.sub("", text)
    return text


def _strip_fenced_blocks(text: str) -> str:
    lines = text.split("\n")
    result = []
    in_fence = False
    fence_marker = ""

    for line in lines:
        if in_fence:
            stripped = line.strip()
            if stripped == fence_marker:
                in_fence = False
            continue

        m = FENCED_BLOCK_RE.match(line)
        if m:
            in_fence = True
            fence_marker = m.group(1)
            continue

        result.append(line)

    return "\n".join(result)


def _strip_indented_blocks(text: str) -> str:
    lines = text.split("\n")
    result = []
    prev_blank = True

    for line in lines:
        is_indented = line.startswith("    ") or line.startswith("\t")
        is_blank = line.strip() == ""

        if is_indented and prev_blank and not is_blank:
            prev_blank = False
            continue
        if is_indented and not prev_blank and len(result) > 0:
            last_kept = result[-1] if result else ""
            if last_kept.strip() == "" or (
                last_kept.startswith("    ") or last_kept.startswith("\t")
            ):
                continue

        result.append(line)
        prev_blank = is_blank

    return "\n".join(result)


def extract_local_link_targets(text: str) -> list[str]:
    clean = strip_code(text)
    targets = []
    for match in MD_LINK_RE.finditer(clean):
        target = match.group(2).strip()
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if "?" in target:
            target = target.split("?")[0]
        if "#" in target:
            target = target.split("#")[0]
        if target:
            targets.append(target)
    return targets
