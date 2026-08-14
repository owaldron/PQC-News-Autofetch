# NewsAutofetch

Agent-guided search and summary of articles on **NIST's ongoing standardization
of additional post-quantum digital signature schemes** (the "on-ramp" / second
call for signatures).

📰 **Read the digests: <https://owaldron.github.io/PQC-News-Autofetch/>**

[fetch.sh](fetch.sh) drives the `claude` CLI headlessly to web-search for
relevant articles, then writes a dated digest to `backlog/`. A running index of
everything already summarized keeps each run focused on **new** articles only.

## Prerequisites

- [`claude`](https://claude.com/claude-code) CLI on your `PATH`
  (`claude --version`).
- Authentication available in the shell that runs the script. For unattended /
  cron use, set `ANTHROPIC_API_KEY` (or configure an `apiKeyHelper`) so no
  interactive login is needed.

## Usage

```bash
./fetch.sh              # digest of articles from the last 14 days (default)
./fetch.sh --days 30    # custom recency window (in days)
./fetch.sh --backfill   # no recency limit — bulk-populate an empty backlog
./fetch.sh --help       # usage
```

Run `--backfill` once to seed the backlog, then run the default periodically to
pick up what's new.

### Environment variables

| Variable      | Default              | Purpose                                        |
|---------------|----------------------|------------------------------------------------|
| `MODEL`       | your CLI default     | Override the Claude model (e.g. `MODEL=opus`).  |
| `MAX_QUERIES` | `24` (`60` backfill) | Cap on web searches/fetches per run.            |

## What it does

Each run, the agent:

1. Reads [instructions.md](instructions.md) — the output template: the synopsis
   paragraph that opens each digest, plus the per-article fields (relevance
   score, title, date, authors, summary, link).
2. Reads [sources.md](sources.md) — preferred sources and the tracked candidate
   schemes; High-priority sources are weighted higher.
3. Reads `backlog/index.md` — the cache of already-summarized articles.
4. Runs **targeted, keyword-scoped** web searches (scheme name × process keyword,
   scoped to sources like IACR ePrint, pqc-forum, and NIST CSRC), up to
   `MAX_QUERIES`, excluding anything already in the index.
5. Writes the ranked digest to `backlog/<YYYY-MM-DD>.md`.
6. Appends the new articles to `backlog/index.md` so future runs skip them.

Tools are restricted to a scoped allowlist (`Read Write Edit WebSearch WebFetch`);
the script does **not** bypass permissions.

## Files

| Path                    | Role                                                       |
|-------------------------|------------------------------------------------------------|
| `fetch.sh`              | The runner.                                                 |
| `instructions.md`       | Output template / scoring guide (edit to change format).    |
| `sources.md`            | Tracked schemes + preferred sources (edit to tune results). |
| `backlog/<date>.md`     | A dated digest — the output you read.                       |
| `backlog/index.md`      | Dedup cache of every article already summarized.            |
| `site/build.py`         | Renders `backlog/` into the static site (see below).        |

## Website

Every push to `main` that touches `backlog/` or `site/` rebuilds
<https://owaldron.github.io/PQC-News-Autofetch/> via
[.github/workflows/pages.yml](.github/workflows/pages.yml): a home page listing
the digests, one page per digest, and an "All articles" archive built from
`backlog/index.md`. The markdown files themselves are never modified.

Preview locally:

```bash
pip install markdown-it-py linkify-it-py
python site/build.py                  # writes ./_site (gitignored)
python -m http.server -d _site 8000   # then open http://localhost:8000
```

Styling lives in [site/style.css](site/style.css).

## Customizing

- **Add or drop sources / schemes:** edit [sources.md](sources.md). New scheme
  names flow into the keyword queries automatically.
- **Change the digest format or scoring:** edit [instructions.md](instructions.md).
- **Force a re-summary of an article:** remove its line from `backlog/index.md`.

## Scheduling (optional)

Run daily via cron (ensure `ANTHROPIC_API_KEY` is set in the cron environment):

```cron
0 8 * * *  cd /Users/owenwaldron/Documents/NewsAutofetch && ./fetch.sh >> backlog/fetch.log 2>&1
```
