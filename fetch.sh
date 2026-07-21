#!/usr/bin/env bash
#
# fetch.sh — Agent-guided search & summary of articles on NIST's ongoing
# standardization of ADDITIONAL post-quantum digital signature schemes.
#
# Drives the `claude` CLI headlessly to:
#   1. read intructions.md (output template) and sources.md (preferred sources)
#   2. read backlog/index.md (cache of already-summarized articles)
#   3. search the web for NEW, relevant articles
#   4. write a dated digest to backlog/<YYYY-MM-DD>.md
#   5. append newly-summarized articles to backlog/index.md so future runs skip them
#
# Usage:
#   ./fetch.sh              # default: articles from the last 14 days
#   ./fetch.sh --days 30    # custom recency window (days)
#   ./fetch.sh --backfill   # no recency limit — bulk-populate an empty backlog
#
# Env:
#   MODEL=opus ./fetch.sh   # override the claude model (default: CLI default)

set -euo pipefail

# --- resolve project dir so relative paths work from anywhere ----------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- args --------------------------------------------------------------------
DAYS=14
WINDOW_DESC="published within the last 14 days"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --backfill)
      WINDOW_DESC="from any date since NIST's additional-signatures call began (2022 onward) — this is an initial backfill to populate the backlog"
      shift ;;
    --days)
      DAYS="${2:?--days needs a number}"
      WINDOW_DESC="published within the last ${DAYS} days"
      shift 2 ;;
    -h|--help)
      awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# --- preconditions -----------------------------------------------------------
command -v claude >/dev/null 2>&1 || { echo "error: claude CLI not found in PATH" >&2; exit 1; }

DATE="$(date +%F)"          # YYYY-MM-DD
OUTPUT="backlog/${DATE}.md"
INDEX="backlog/index.md"

mkdir -p backlog
if [[ ! -f "$INDEX" ]]; then
  cat > "$INDEX" <<'EOF'
# Backlog index

Cache of articles already summarized. One line per article; future runs skip any
article whose link appears here. Format: `- [YYYY-MM-DD captured] Title — URL`

EOF
fi

# --- prompt ------------------------------------------------------------------
read -r -d '' PROMPT <<EOF || true
You are a research assistant maintaining an ongoing tracker of news and analysis
about NIST's standardization of ADDITIONAL post-quantum digital signature
schemes (the "on-ramp" / second call for signatures — distinct from the original
CRYSTALS-Dilithium / FALCON / SPHINCS+ selections).

Using only the allowed tools:

1. Read intructions.md — it defines the output TEMPLATE (fields each entry must
   capture: relevance score, title, date, authors, summary, link).
2. Read sources.md — treat "High-priority sources" as preferred/authoritative and
   weight them higher. If it is empty, use reputable sources of your own judgment
   (NIST CSRC PQC pages, the pqc-forum mailing list, IACR ePrint, major security
   press, academic venues).
3. Read ${INDEX} — the cache of articles ALREADY summarized on previous runs. You
   MUST NOT include any article whose link already appears there.
4. Search the web for articles ${WINDOW_DESC} that are genuinely relevant to the
   NIST additional-signatures standardization process (candidate schemes, round
   updates, evaluations, cryptanalysis, official NIST announcements, expert
   analysis). Exclude anything already in ${INDEX}.
5. Rank the remaining NEW articles by relevance and keep the most essential ones
   (aim for the top ~8; fewer is fine if little is new; for a backfill you may
   include more). Assign each a relevance score.
6. Write the digest to ${OUTPUT}, following the template in intructions.md, under
   a "# NIST PQC Signatures — ${DATE}" heading. If nothing new is relevant, still
   create ${OUTPUT} noting that none were found.
7. Append each included article to ${INDEX} as a new line:
   "- [${DATE}] <title> — <url>". Do not remove or reorder existing lines.

Only include real articles you actually found via search, with working links. Do
not fabricate.
EOF

# --- run ---------------------------------------------------------------------
echo "==> Fetching NIST PQC signatures digest → ${OUTPUT} (${WINDOW_DESC})"
claude -p "$PROMPT" \
  --allowedTools "Read Write Edit WebSearch WebFetch" \
  --permission-mode acceptEdits \
  ${MODEL:+--model "$MODEL"}

echo "==> Done. Digest: ${OUTPUT}  |  Index: ${INDEX}"
