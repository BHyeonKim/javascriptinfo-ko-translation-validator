#!/usr/bin/env python3
"""
Glossary-based translation consistency checker for ko.javascript.info.

Compares 한국어(영어) 병기 patterns in the input file against the
ko.javascript.info Google Sheets glossary (cached locally under glossary/).
Refreshes cache on every run via sha256 comparison; falls back to cache on
network failure.

Usage: python3 check_glossary.py <file_path>
Output (stdout): JSON with violations, passed list, and cache metadata.
"""

import csv
import datetime
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from _text_utils import strip_non_korean_content


SPREADSHEET_ID = "1fYaEI8vz26N3R2VaxrlNnk9fMQ8zIy4RpvjRp4jZd0Q"
SHEETS = {
    "sheet1": "1401860741",
    "sheet2": "843106813",
}
CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    + SPREADSHEET_ID
    + "/gviz/tq?tqx=out:csv&gid={gid}"
)
FETCH_TIMEOUT = 5  # seconds

GLOSSARY_DIR = Path(__file__).resolve().parent.parent / "glossary"

# 한국어(영어) 병기 패턴 — 영어는 알파벳으로 시작, 콤마/공백/언더스코어/하이픈 허용
PAIR_RE = re.compile(
    r"([가-힣][가-힣\s·]{0,20})\(([A-Za-z][A-Za-z0-9 ,_\-]{0,60})\)"
)


def resolve_korean(korean_text: str, candidates: list[str]) -> tuple[str, bool]:
    """본문의 한국어 부분에서 실제 사용된 용어를 추출하고 표준 일치 여부 반환.

    정규식이 앞 단어까지 욕심부려 잡는 경우에 대비해, 후보 표기가 suffix로
    들어있으면 통과로 본다.
    """
    korean_text = korean_text.strip()
    for cand in sorted(candidates, key=len, reverse=True):
        if korean_text == cand:
            return cand, True
        if korean_text.endswith(cand):
            cut = len(korean_text) - len(cand)
            if cut > 0 and korean_text[cut - 1].isspace():
                return cand, True
    tokens = korean_text.split()
    return (tokens[-1] if tokens else korean_text), False


def refresh_cache() -> dict:
    """Fetch sheets, update files if hash changed. Returns cache status dict."""
    meta_path = GLOSSARY_DIR / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        meta = {
            "spreadsheet_id": SPREADSHEET_ID,
            "last_fetched": None,
            "sheets": {name: {"gid": gid, "sha256": ""} for name, gid in SHEETS.items()},
        }

    refreshed = False
    warning = None

    for name, gid in SHEETS.items():
        url = CSV_URL.format(gid=gid)
        try:
            with urllib.request.urlopen(url, timeout=FETCH_TIMEOUT) as resp:
                body = resp.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            warning = f"network fetch failed for {name}: {exc}"
            continue

        new_hash = hashlib.sha256(body).hexdigest()
        old_hash = meta["sheets"].get(name, {}).get("sha256", "")
        if new_hash != old_hash:
            (GLOSSARY_DIR / f"{name}.csv").write_bytes(body)
            meta["sheets"][name] = {"gid": gid, "sha256": new_hash}
            refreshed = True

    if refreshed:
        meta["last_fetched"] = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).isoformat(timespec="seconds")
        meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return {
        "last_fetched": meta.get("last_fetched"),
        "refreshed": refreshed,
        "network_warning": warning,
    }


def load_glossary() -> dict[str, list[str]]:
    """Read both CSVs, return {english_lower: [korean_candidate, ...]}."""
    glossary: dict[str, list[str]] = {}
    for name in SHEETS:
        path = GLOSSARY_DIR / f"{name}.csv"
        if not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.reader(f):
                if len(row) < 2:
                    continue
                english = row[0].strip()
                korean = row[1].strip()
                if not english or not korean:
                    continue
                if not re.match(r"^[A-Za-z]", english):
                    # Skip symbol-only entries from sheet2 (병기 패턴 키와 매칭 불가)
                    continue
                key = english.lower()
                # 슬래시/콤마 분리 표기는 모두 정답 후보 (예: "문, 구문", "세미콜론/쌍반점")
                parts = re.split(r"\s*[/,]\s*", korean)
                candidates = [c for c in parts if c]
                glossary[key] = candidates
    return glossary


def check_file(file_path: str) -> dict:
    cache_status = refresh_cache()
    glossary = load_glossary()

    raw = Path(file_path).read_text(encoding="utf-8")
    cleaned = strip_non_korean_content(raw)

    violations = []
    passed = []

    for line_num, line in enumerate(cleaned.splitlines(), start=1):
        for match in PAIR_RE.finditer(line):
            korean_raw = match.group(1).strip()
            english_raw = match.group(2).strip()
            english_key = english_raw.split(",")[0].strip().lower()
            candidates = glossary.get(english_key)
            if not candidates:
                continue
            korean_used, is_match = resolve_korean(korean_raw, candidates)
            if is_match:
                passed.append(f"{korean_used}({english_raw}) — 표준 번역어 일치")
            else:
                violations.append(
                    {
                        "line": line_num,
                        "rule_id": "GLOSSARY-mismatch",
                        "problem": f"{korean_used}({english_raw})",
                        "suggestion": f"{candidates[0]}({english_raw})",
                        "severity": "recommended",
                    }
                )

    return {
        "source": "glossary",
        "violations": violations,
        "passed": passed,
        "cache": cache_status,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <file_path>", file=sys.stderr)
        sys.exit(1)

    target = sys.argv[1]
    if not os.path.exists(target):
        print(json.dumps({"error": f"File not found: {target}"}))
        sys.exit(1)

    result = check_file(target)
    print(json.dumps(result, ensure_ascii=False, indent=2))
