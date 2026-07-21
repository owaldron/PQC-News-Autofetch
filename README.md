# NewsAutofetch

Agent-guided search and summary of articles on **NIST's ongoing standardization
of additional post-quantum digital signature schemes** (the "on-ramp" / second
call for signatures).

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

1. Reads [intructions.md](intructions.md) — the output template (relevance score,
   title, date, authors, summary, link).
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
| `intructions.md`        | Output template / scoring guide (edit to change format).    |
| `sources.md`            | Tracked schemes + preferred sources (edit to tune results). |
| `backlog/<date>.md`     | A dated digest — the output you read.                       |
| `backlog/index.md`      | Dedup cache of every article already summarized.            |

## Customizing

- **Add or drop sources / schemes:** edit [sources.md](sources.md). New scheme
  names flow into the keyword queries automatically.
- **Change the digest format or scoring:** edit [intructions.md](intructions.md).
- **Force a re-summary of an article:** remove its line from `backlog/index.md`.

## Scheduling (optional)

Run daily via cron (ensure `ANTHROPIC_API_KEY` is set in the cron environment):

```cron
0 8 * * *  cd /Users/owenwaldron/Documents/NewsAutofetch && ./fetch.sh >> backlog/fetch.log 2>&1
```
