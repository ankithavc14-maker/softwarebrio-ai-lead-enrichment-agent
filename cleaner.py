import re
from bs4 import BeautifulSoup


EMAIL_RE = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.I,
)

LINKEDIN_RE = re.compile(
    r"https?://(?:www\.)?linkedin\.com/(?:in|company)/[A-Za-z0-9%._~/-]+",
    re.I,
)

NOISE_TAGS = [
    "script",
    "style",
    "noscript",
    "svg",
    "canvas",
    "template",
    "iframe",
    "nav",
]


def clean_html(html: str, max_chars: int) -> tuple[str, list[str], list[str]]:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(NOISE_TAGS):
        tag.decompose()

    # Header/footer chrome can consume a large evidence budget, and isn't
    # always wrapped in <nav> (which NOISE_TAGS already strips above).
    for tag in soup.find_all(["header", "footer"]):
        tag.decompose()

    emails = sorted(set(EMAIL_RE.findall(soup.get_text(" ", strip=True))))
    linkedin_urls = sorted(set(LINKEDIN_RE.findall(html)))

    # Prefer semantic content containers where available.
    root = soup.find("main") or soup.find("article") or soup.body or soup

    text = root.get_text("\n", strip=True)
    lines = []
    previous = None

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            continue
        if line == previous:
            continue
        previous = line
        lines.append(line)

    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned[:max_chars], emails, linkedin_urls


def dedupe_and_budget(text: str, max_chars: int) -> str:
    """Keep the earliest occurrence of repeated lines and enforce a global budget."""
    seen = set()
    output = []

    for line in text.splitlines():
        normalized = re.sub(r"\s+", " ", line).strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(line)

        if sum(len(x) + 1 for x in output) >= max_chars:
            break

    return "\n".join(output)[:max_chars]
