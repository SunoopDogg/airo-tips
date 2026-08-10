---
name: query
description: Answer questions from this repository's accumulated wiki with traceable source citations, uncertainty, contradictions, and related connections. Use when the user asks to query, search, compare, explain, analyze, or synthesize knowledge already captured in wiki/, or asks to save a valuable answer back as a note page.
---

# Query the wiki

Follow the repository-root `AGENTS.md`. Ground the answer in the wiki; do not silently substitute general memory or web knowledge for missing evidence.

## 1. Retrieve

1. Read `index.md` first and inspect recent relevant `log.md` entries when recency matters.
2. Select candidate pages from index descriptions, then search `wiki/` for query terms, aliases, related wikilinks, and cited source pages.
3. Read the relevant pages and follow their `sources` links far enough to verify material claims. Read raw files only when a wiki citation is ambiguous or verification is essential; say when doing so.
4. Do not use the web unless the user requests it or the question explicitly requires current external facts. Clearly separate external findings from wiki-held knowledge.

## 2. Answer

- Lead with the direct conclusion, then give the evidence and important caveats.
- Cite claims with existing wikilinks such as `[[페이지 제목]]`; cite the underlying source page rather than only a note page.
- Surface contradictory sources, uncertainty, stale dates, and missing evidence.
- Distinguish fact, source opinion, and new inference. Mark new connections as analysis.
- Mention adjacent wiki knowledge only when it helps the question.
- If the wiki cannot answer, state what is missing and suggest a precise source or ingest target. Do not fabricate an answer.

## 3. Save only when authorized

A normal query is read-only: do not edit files or append to the log. If the user explicitly asks to save, file, or preserve the answer:

1. Create or update a `type: note` page with direct source-page provenance.
2. Link it from the relevant concept/entity pages only where useful.
3. Update `index.md`.
4. Append one completed `query` entry to `log.md`.
5. Verify links, frontmatter, and the final diff.

Report which wiki pages support the answer and, for saved queries, which files changed.
