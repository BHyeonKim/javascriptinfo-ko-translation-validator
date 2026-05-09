#!/usr/bin/env python3
"""
Korean spell checker for ko.javascript.info translations using hanspell.

Strips markdown code regions before checking to avoid false positives,
then runs `npx hanspell -d` and outputs structured JSON.

Usage: python3 check_spelling.py <file_path>
Output (stdout): JSON array of spelling violations
"""

import sys
import re
import subprocess
import json
import os


def strip_non_korean_content(content: str) -> str:
    """Remove regions that should not be spell-checked."""
    # Fenced code blocks
    content = re.sub(r'```[\s\S]*?```', '\n', content)
    # Inline code
    content = re.sub(r'`[^`\n]+`', ' ', content)
    # URLs
    content = re.sub(r'https?://\S+', ' ', content)
    # Markdown images
    content = re.sub(r'!\[[^\]]*\]\([^\)]+\)', ' ', content)
    # Markdown links → keep link text only
    content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
    # HTML tags
    content = re.sub(r'<[^>]+>', ' ', content)
    # Heading markers
    content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
    # Bold/italic markers
    content = re.sub(r'\*{1,3}', '', content)
    content = re.sub(r'(?<!\w)_([^_\n]+)_(?!\w)', r'\1', content)
    # YAML frontmatter
    content = re.sub(r'^---[\s\S]*?---\n', '', content)
    # Smart quotes and special chars that confuse hanspell
    content = content.replace('“', '"').replace('”', '"')
    return content


def parse_hanspell_output(output: str) -> list[dict]:
    """
    Parse hanspell output into structured violations.

    hanspell output format per error:
        원문 -> 수정안
        설명 텍스트
    """
    violations = []
    lines = output.strip().splitlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if ' -> ' in line:
            parts = line.split(' -> ', 1)
            original = parts[0].strip()
            suggestion = parts[1].strip()
            explanation = ''
            if i + 1 < len(lines) and ' -> ' not in lines[i + 1] and lines[i + 1].strip():
                explanation = lines[i + 1].strip()
                i += 1
            violations.append({
                'original': original,
                'suggestion': suggestion,
                'explanation': explanation,
            })
        i += 1

    return violations


def check_spelling(file_path: str) -> None:
    if not os.path.exists(file_path):
        print(json.dumps({'error': f'File not found: {file_path}'}))
        sys.exit(1)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    cleaned = strip_non_korean_content(content)

    try:
        result = subprocess.run(
            ['npx', '--yes', 'hanspell', '-d'],
            input=cleaned,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        print(json.dumps({'error': 'hanspell timed out after 120 seconds'}))
        sys.exit(1)
    except FileNotFoundError:
        print(json.dumps({'error': 'npx not found — install Node.js first'}))
        sys.exit(1)

    # hanspell: violations go to stderr, corrected text goes to stdout
    violations = parse_hanspell_output(result.stderr)

    output = {
        'file': file_path,
        'violations': violations,
        'total': len(violations),
        'corrected_text': result.stdout.strip(),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <file_path>', file=sys.stderr)
        sys.exit(1)
    check_spelling(sys.argv[1])
