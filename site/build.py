#!/usr/bin/env python3
"""Build a static site from the markdown digests in backlog/.

Reads backlog/<YYYY-MM-DD>.md (the digests) and backlog/index.md (the dedup
cache of every article ever captured) and writes flat HTML into _site/:

    _site/index.html      list of digests, newest first
    _site/<date>.html     one page per digest
    _site/articles.html   every captured article, grouped by capture date
    _site/style.css       copied verbatim from site/style.css

Requires: markdown-it-py, linkify-it-py.
"""

from __future__ import annotations

import html
import re
import shutil
from datetime import date, datetime, timezone
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parent.parent
BACKLOG = ROOT / "backlog"
OUT = ROOT / "_site"

SITE_TITLE = "NIST PQC Signatures"
SITE_BLURB = (
    "Tracking news, analysis, and research on NIST's standardization of "
    "additional post-quantum digital signature schemes."
)
REPO_URL = "https://github.com/owaldron/PQC-News-Autofetch"

DATE_STEM = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Index lines look like: "- [2026-08-09] Some Title — https://example.com"
INDEX_LINE = re.compile(r"^-\s*\[(\d{4}-\d{2}-\d{2})[^\]]*\]\s*(.+?)\s+—\s+(\S+)\s*$")

# The linkify *option* and the linkify *rule* are separate switches; the digests
# write bare URLs (`- **Link:** https://…`), so both must be on.
md = MarkdownIt("commonmark", {"linkify": True}).enable("table").enable("linkify")


# --- markdown helpers --------------------------------------------------------


def split_title(text: str) -> tuple[str | None, str]:
    """Peel the leading `# ...` heading off a digest; return (title, rest)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        if line.startswith("# "):
            return line[2:].strip(), "\n".join(lines[i + 1 :])
        break
    return None, text


def first_paragraph(text: str) -> str:
    """The digest's lede: the intro prose before the first article entry.

    A digest may open straight into a `### [n/10] …` entry, in which case there
    is no lede and we must not fall through into the entry's own bullets.
    """
    para: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if para:
                break
            continue
        if stripped.startswith("#") or stripped.startswith(("-", "*", "_", "=")):
            break
        para.append(stripped)
    return " ".join(para)


def strip_inline_markup(text: str) -> str:
    """Flatten `**bold**`, `_em_`, and `[text](url)` for plain-text contexts."""
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"(\*\*|__|\*|_|`)", "", text)
    return text.strip()


# --- page template -----------------------------------------------------------


def page(title: str, body: str, *, heading: str | None = None, lede: str = "") -> str:
    """Wrap rendered content in the shared HTML skeleton."""
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    head = ""
    if heading is not None:
        head = f"    <h1>{html.escape(heading)}</h1>\n"
        if lede:
            head += f'    <p class="lede">{html.escape(lede)}</p>\n'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lato:ital,wght@0,400;0,700;1,400&display=swap">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
  <a class="brand" href="index.html">{html.escape(SITE_TITLE)}</a>
  <nav><a href="index.html">Digests</a> · <a href="articles.html">All articles</a></nav>
</header>
<main>
{head}{body}
</main>
<footer>
  Generated from <a href="{REPO_URL}">{html.escape(REPO_URL.split("/")[-1])}</a> · built {built}
</footer>
</body>
</html>
"""


# --- digests -----------------------------------------------------------------


class Digest:
    def __init__(self, path: Path):
        self.path = path
        self.date = path.stem
        raw = path.read_text(encoding="utf-8")
        title, rest = split_title(raw)
        self.title = title or self.date
        self.lede = strip_inline_markup(first_paragraph(rest))
        self.count = len(re.findall(r"(?m)^###\s", rest))
        self.body = md.render(rest)

    @property
    def href(self) -> str:
        return f"{self.date}.html"

    def pretty_date(self) -> str:
        try:
            return date.fromisoformat(self.date).strftime("%B %-d, %Y")
        except ValueError:
            return self.date


def load_digests() -> list[Digest]:
    if not BACKLOG.is_dir():
        return []
    paths = [p for p in BACKLOG.glob("*.md") if DATE_STEM.match(p.stem)]
    return [Digest(p) for p in sorted(paths, reverse=True)]


def render_home(digests: list[Digest]) -> str:
    if not digests:
        body = "<p>No digests yet. Run <code>./fetch.sh</code> to create one.</p>"
        return page(SITE_TITLE, body, heading=SITE_TITLE, lede=SITE_BLURB)

    rows = []
    for d in digests:
        articles = f"{d.count} article{'' if d.count == 1 else 's'}"
        rows.append(
            '<li class="digest">\n'
            f'  <a class="digest-date" href="{d.href}"><time datetime="{d.date}">'
            f"{html.escape(d.pretty_date())}</time></a>\n"
            f'  <span class="count">{articles}</span>\n'
            + (f'  <p class="lede">{html.escape(d.lede)}</p>\n' if d.lede else "")
            + "</li>"
        )
    body = '<ul class="digests">\n' + "\n".join(rows) + "\n</ul>"
    return page(SITE_TITLE, body, heading=SITE_TITLE, lede=SITE_BLURB)


def render_digest(d: Digest) -> str:
    return page(f"{d.title} · {SITE_TITLE}", d.body, heading=d.title)


# --- all-articles page -------------------------------------------------------


def render_articles() -> str | None:
    src = BACKLOG / "index.md"
    if not src.is_file():
        return None

    groups: dict[str, list[tuple[str, str]]] = {}
    leftovers: list[str] = []
    total = 0
    for line in src.read_text(encoding="utf-8").splitlines():
        m = INDEX_LINE.match(line)
        if m:
            captured, title, url = m.groups()
            groups.setdefault(captured, []).append((strip_inline_markup(title), url))
            total += 1
        elif line.strip().startswith("-"):
            # Keep malformed entries visible rather than dropping them silently.
            leftovers.append(line)

    parts = []
    for captured in sorted(groups, reverse=True):
        items = "\n".join(
            f'  <li><a href="{html.escape(url, quote=True)}">{html.escape(title)}</a></li>'
            for title, url in groups[captured]
        )
        parts.append(
            f'<section class="capture">\n'
            f'  <h2><time datetime="{captured}">{captured}</time></h2>\n'
            f"  <ul>\n{items}\n  </ul>\n"
            f"</section>"
        )
    if leftovers:
        parts.append(md.render("\n".join(leftovers)))

    lede = (
        f"{total} article{'' if total == 1 else 's'} captured so far, "
        "grouped by the run that found them."
    )
    body = "\n".join(parts) if parts else "<p>Nothing captured yet.</p>"
    return page(f"All articles · {SITE_TITLE}", body, heading="All articles", lede=lede)


# --- main --------------------------------------------------------------------


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    digests = load_digests()
    (OUT / "index.html").write_text(render_home(digests), encoding="utf-8")
    for d in digests:
        (OUT / d.href).write_text(render_digest(d), encoding="utf-8")

    articles = render_articles()
    if articles is not None:
        (OUT / "articles.html").write_text(articles, encoding="utf-8")

    shutil.copyfile(Path(__file__).resolve().parent / "style.css", OUT / "style.css")
    print(f"built {len(digests)} digest page(s) → {OUT}")


if __name__ == "__main__":
    main()
