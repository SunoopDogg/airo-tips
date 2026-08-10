---
name: wiki-lint
description: Health check and repair pass over this LLM wiki — finds broken [[links]], orphan pages nothing links to, index.md drift, malformed or stale frontmatter, contradictions between pages, claims superseded by newer sources, frequently-mentioned things that have no page yet, thin stubs, and research gaps worth a web search or a new source; then reports everything grouped by severity and fixes what the human approves. Use this whenever the human says "lint the wiki", "health check", "audit the knowledge base", "is the wiki consistent", "check for contradictions", "any broken links", "any orphan pages", "what's missing", "what should I add", "suggest gaps to fill", "what should I read next", "clean up the wiki", "tidy the index", or otherwise asks about the *state* of the wiki rather than its contents — and lean toward using it when a request is ambiguous but sounds like maintenance, since a wasted lint costs little and a skipped one lets rot compound. Do NOT use it to file a new document that landed in raw/ (that is wiki-ingest) or to answer a substantive question about what the wiki says (that is wiki-query); a lint reads pages to judge their health, not to answer their subject matter.
---

# Wiki Lint

A lint pass answers "is this wiki still trustworthy?" Rot in a wiki is quiet: a link that
stopped resolving, an index line pointing at a deleted page, two pages that now disagree.
Nothing errors, answers just get slightly worse forever. Your job is to surface that,
then repair what the human signs off on.

Read `CLAUDE.md` first — it is the schema, and this skill assumes its conventions
(filename = title, frontmatter key order, `[[wikilinks]]`, no Dataview in this vault).
`raw/` is immutable — a lint reads source documents to check the wiki against them, never edits,
renames, or tidies them.

## 0. Scope the pass first

A full read of a large wiki is expensive and mostly re-reads pages that haven't changed.
Ask which scope, and recommend one:

- **Recent** (default) — pages changed since the last `## [YYYY-MM-DD] lint` entry in `log.md`.
  Recent changes are where the rot is. Find the boundary with
  `grep '^## \[.*\] lint' log.md | tail -1`, then `find wiki -name '*.md' -newermt YYYY-MM-DD`.
  If that date is today, or predates any content at all, this degenerates to "nothing changed" —
  fall back to a full pass instead of reporting an empty result.
- **Folder / topic** — e.g. only `wiki/entities/`, or every page tagged with one theme.
- **Full** — everything. Right after a big ingest, or when nobody has linted in a while.

Mechanical checks (1–4 below) are cheap; run them full-wiki regardless of scope.
Reading-based checks (5–9) follow the chosen scope.

If `wiki/` has no pages at all, say so and stop. An empty wiki has no findings, and
inventing some is worse than reporting nothing.

## 1. Broken links

Extract every wikilink target and compare against actual filenames. Strip `|alias` and
`#heading`, and fold case — Obsidian resolves links case-insensitively, so `[[Index]]`
correctly points at `index.md` and a case-sensitive comparison will report it broken forever.

```bash
python3 scripts/check_links.py
```

That one script covers checks 1–3 (broken links, orphans, index drift) and exits non-zero if any
fire. Three details in it are load-bearing, and shell pipelines here have gotten each one wrong:

- **Never `sort`/`uniq`/`comm` on Hangul filenames.** On macOS those tools compare with the
  `en_US.UTF-8` collation, not bytes, so distinct page names tie and collapse into one. A `comm`
  based link check ran green on this wiki while silently dropping four pages from the right-hand
  set. `LC_ALL=C` fixes the shell version; the script sidesteps it entirely.
- **Normalize to NFC.** APFS stores filenames decomposed (NFD) while page text is composed (NFC),
  so `[[에어로랩]]` and `에어로랩.md` differ byte-wise and every Hangul link reads as broken.
- **Fold case, strip `|alias` and `#heading`.** Obsidian resolves links case-insensitively, so
  `[[Index]]` correctly points at `index.md`. Obsidian also requires the alias pipe escaped inside
  a table cell (`[[Pi 0.5\|π0.5]]`), so cut on `\` too or the backslash stays on the target.

Links are pulled from `wiki/` and `index.md` only: `CLAUDE.md` is the schema and its wikilinks are
illustrative examples, and `log.md` is append-only, so a stale link there is not yours to rewrite.
Both still count as *targets*, so `[[Index]]` and `[[Log]]` resolve.

Then judge each hit, because the fix differs:

- **Typo / renamed page** — an existing page is obviously meant. Fix the link.
- **Page that should exist** — the target is a real thing the wiki keeps referring to.
  Offer to create it; don't create it silently, since a new page is a commitment to maintain it.
- **Deliberate forward reference** — the human may be marking something to write later.
  Leave it, mention it once.

## 2. Orphans

A page with no inbound links is unreachable by the link graph, which makes it effectively
deleted. Count inbound links **excluding `index.md` and `log.md`** — the index links
everything by design, so counting it makes this check vacuous. A page linked *only* from
the index or the log is the real signal.

`scripts/check_links.py` reports these. Don't hand-roll the shell version: `grep -F "[[$n"` matches
on prefix, so `[[Remplir` also matches `[[Remplir RPM-5120V314AS1 …]]` and a genuinely orphaned
short-named page reads as linked.

A `sources: ["[[X]]"]` line in frontmatter is a genuine inbound link to X — count it.

Fixing an orphan means finding where it belongs and linking it from there: the hub concept,
the source page it came from, a related entity. Adding a link to the index is not a fix.

## 3. Index drift

The index is where every query starts, so drift here silently degrades every answer.
Two directions, both worth checking:

- Pages that exist but have no `index.md` line.
- Index lines pointing at pages that no longer exist.

Also check that each page sits under the right heading (`### Entities` / `### Concepts` /
`### Sources` / `### Notes`) and that its one-line summary still describes the page.
Restore the exact format:

```
- [[Vannevar Bush]] — engineer who proposed the memex in 1945.
```

## 4. Frontmatter integrity

Per page: all seven keys present and in schema order (`title`, `type`, `tags`, `created`,
`updated`, `status`, `sources`), `type` in `entity | concept | source | note | overview`,
`title` matching the filename exactly, and `type: source` pages carrying `source_path:`
and `ingested:`.

Folder check: `wiki/entities/`, `wiki/concepts/`, `wiki/sources/`, `wiki/notes/` must match
the page's type. Exempt `type: overview` — `index.md` and `log.md` legitimately live at the
repo root, and a mechanical type→folder map flags them on every pass.

Stale `updated:` — compare against filesystem mtime (`stat -f '%Sm' -t '%F' <file>` on macOS; the
GNU `stat -c '%Y %n'` form is not available here); this is
not a git repo, so there is no commit history to check. Treat a mismatch as a soft signal:
mtime doesn't survive a copy or a sync, so it's a prompt to look, not a proven defect.

## 5. Contradictions — the check that actually matters

This one needs reading, not grepping. Two pages can disagree with no textual overlap at all.

Don't pretend to read everything. Sample deliberately: pages changed in this scope, plus the
hub pages (most inbound links, `status: stable`, the ones every query touches). Read them
together and look for claims that can't both be true — dates, numbers, attributions, causal
stories, definitions that drifted apart.

When you find one, write a `## Contradictions` section on the affected page(s): both claims,
both citations, and which is better supported and why. Never resolve it by quietly overwriting
the older claim — disagreement between sources is information, and deleting it is the main way
a wiki degrades. If a contradiction is already recorded and a newer source settles it, update
the section to say so; keep the history.

## 6. Stale claims

A page still asserting something a newer source superseded, with no `## Contradictions`
section recording the shift. Find these by reading source pages ingested since the last lint
and asking what they changed — source pages carry a "what it changed in the wiki" section,
which is the fastest way in. Then check whether the pages it should have changed actually did.

## 7. Missing pages

A name or concept mentioned across several pages with no page of its own. Frequency of
mention is the signal — something referenced in five pages and defined in none is a hole in
the graph. Bare proper nouns that never became `[[links]]` are the same smell:

```bash
grep -rhoE '\b([A-Z][a-z]+ ){1,3}[A-Z][a-z]+\b' wiki | sort | uniq -c | sort -rn | head -30
```

**That grep only finds Latin-script names.** This wiki is Korean, so it returns almost nothing
useful and a clean run proves nothing. Answer this check by reading instead: while going through
pages, note every named thing mentioned on three or more pages that has no file. Count inbound
mentions with `grep -rl` on the term, not on `[[term]]` — the whole point is that it was never
linked.

Cross-check the top hits against existing filenames, and propose the ones that recur.

## 8. Thin stubs

`status: stub` pages that never grew (`grep -rl 'status: stub' wiki`), and pages with an
empty `sources: []` or no inline citations at all. An uncited page is an assertion with no
provenance — either find its source or mark it as unsourced in the text.

## 9. Research gaps

Be actively useful here — sourcing is the human's job, and a good list is worth more than
another mechanical finding. Look for questions the wiki raises but doesn't answer: an entity
with no origin, a concept whose mechanism is described but not evidenced, a comparison the
notes keep gesturing at. Propose what would fill each gap — a web search, a specific document
to drop in `raw/`, or a `wiki/notes/` synthesis you could write from material already present.

## Report before fixing

Some "problems" are a deliberate choice the human made, so auto-fixing them is destructive.
Report first, grouped by severity, and let them pick.

The one exception: trivially safe mechanical fixes — a missing index line, a stale `updated:`
date, a link typo with one obvious target — can be batched and applied on a single
confirmation. Don't ask about them one at a time; that's tedious and the human will just
say yes to all of them.

```markdown
## Lint — <scope> — YYYY-MM-DD
N pages checked.

### Broken (fix these)
1. **Broken link** — `wiki/concepts/Memex.md` → `[[Vanevar Bush]]`; typo for [[Vannevar Bush]]. *Safe fix.*
2. **Missing page** — `[[Differential Analyzer]]` linked from 3 pages, no file. *Create?*
3. **Index drift** — [[Hypertext]] exists but has no index line. *Safe fix.*

### Degrading (worth a look)
4. **Contradiction** — [[Memex]] dates the proposal to 1945, [[As We May Think]] says 1939 draft. Needs a `## Contradictions` section on [[Memex]].
5. **Orphan** — [[Ted Nelson]] has no inbound links; belongs under [[Hypertext]].
6. **Stale** — [[Memex]] not updated since [[Project Xanadu]] was ingested.
7. **Frontmatter** — `wiki/notes/Comparison.md` missing `updated:`. *Safe fix.*

### Opportunities (your call)
8. **Thin stub** — [[Bootstrapping]] still a stub after 3 ingests.
9. **Gap** — nothing covers how the memex influenced later hypertext systems. Suggest a source, or I can draft a note from what's here.

**Safe fixes ready to batch:** 1, 3, 7 — apply all?
```

## After fixing

Update `index.md` for anything created or renamed, bump `updated:` on every page you touched,
and append one entry to `log.md` — exact prefix, newest at the bottom, never rewrite past entries:

```
## [2026-08-18] lint | Recent changes since last pass
Checked 24 pages. Fixed 3 broken links, added 2 missing index lines.
Recorded a contradiction on [[Memex]] about the 1945 date.
Touched: [[Memex]], [[Vannevar Bush]], [[Hypertext]], [[Index]].
```

If the human declined a fix, note that too — otherwise the next lint re-reports it as new.
