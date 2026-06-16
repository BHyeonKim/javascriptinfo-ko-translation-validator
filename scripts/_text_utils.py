"""Shared text preprocessing for ko.javascript.info translation checks."""

import re


def strip_non_korean_content(content: str) -> str:
    """Remove markdown/code regions that should not be inspected as prose."""
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
    # Smart quotes
    content = content.replace('“', '"').replace('”', '"')
    return content
