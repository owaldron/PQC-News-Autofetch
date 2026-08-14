# NIST PQC Additional Signatures — Article Tracker

This backlog tracks the most essential news, analysis, and research about NIST's
standardization of ADDITIONAL post-quantum digital signature schemes (the
"on-ramp" / second call for signatures — distinct from the original
CRYSTALS-Dilithium, FALCON, and SPHINCS+ selections).

## Output template

Each daily digest is `backlog/<YYYY-MM-DD>.md` and opens with a
`# NIST PQC Signatures — <YYYY-MM-DD>` heading.

### Synopsis (required)

Immediately after the heading, before the first article, write a **synopsis**:
one paragraph of 2–4 sentences summarizing the period as a whole. It is the
first thing a reader sees — on the website it is the digest's blurb on the index
page — so it must stand on its own without the entries below it.

Say what actually changed and why it matters: process milestones (withdrawals,
round advancements, deadlines), the dominant theme of the articles, and the
shape of the rest (e.g. "the remainder is implementation work"). Draw only on
the articles in this digest — do not speculate. If the period was quiet or
nothing new was found, say so plainly; a short synopsis is better than a padded
one.

### Articles

After the synopsis, list articles ordered by relevance (highest first). Each
article captures:

1. **Relevance score** — 1–10 (10 = directly about the standardization process /
   official NIST action; lower = tangential PQC-signature context).
2. **Title**
3. **Date** — publication date (YYYY-MM-DD).
4. **Authors** — or the publishing organization if bylines are absent.
5. **Summary** — 2–4 sentences on what it says and why it matters to the process.
6. **Link** — canonical URL.

### File format

    # NIST PQC Signatures — YYYY-MM-DD

    <synopsis paragraph — 2–4 sentences on the period as a whole>

    ### [<score>/10] <Title>
    - **Date:** YYYY-MM-DD
    - **Authors:** ...
    - **Summary:** ...
    - **Link:** <url>

    ### [<score>/10] <Title>
    ...
