---
name: wiki-query
description: Answer a question from this project's LLM Wiki with citations to wiki pages, and file the durable answers back into wiki/notes/ so explorations compound instead of dying in chat history. Use it for any question touching the wiki's subject matter and for phrasings like what do we know about X, compare X and Y, what did the sources say about Z, summarize the state of my thinking on X, make me a table of the tradeoffs, does anything contradict X, is there anything in here about X, who is X, why does X matter — plus every follow-up question in an ongoing conversation about the wiki, including follow-ups phrased with no wiki keywords at all. Lean toward triggering. If a question could plausibly be answered from wiki/, this skill applies; reading index.md and finding nothing costs one file read, while answering from general knowledge silently bypasses the entire wiki and is the failure mode that matters. Do not use it when the human is filing a new source document into raw/ (that is wiki-ingest), or asking for a health check such as orphans, broken links, thin stubs, stale claims, or a contradiction sweep (that is wiki-lint).
---

# Wiki Query

The human asks a question. You answer it from the wiki, with a trail they can follow, and you file
the answer back if it is worth having again. Read `CLAUDE.md` at the repo root if you have not yet
this session — it is the schema, and it is authoritative over anything here.

Run `date +%F` once at the start. Every date you write (`created:`, `updated:`, the log heading)
comes from that, not from memory.

Wiki filenames contain spaces. Quote every shell path — `cat "wiki/notes/Memex vs Modern RAG.md"`.

## 1. Retrieve, in this order

**Read `index.md` first.** It is a curated one-line summary of every page, so it tells you which
pages are relevant before you have read any of them. Grep tells you which pages contain a string,
which is a different and worse question. Pick your candidates from the index.

**Drill into the candidate pages.** Read them fully, and follow their `[[links]]` and `sources:`
frontmatter one hop out — a page's neighbours usually hold half the answer, and the link graph is
the real structure of this wiki.

**Grep `wiki/` as a second pass** for terms the index did not surface — synonyms, proper nouns,
anything the one-line summaries could not have mentioned. `grep -ril "term" wiki/`. The index is
written by hand and lags reality; this catches what it missed.

**Fall back to `raw/` only when `wiki/` genuinely does not cover it.** `raw/` is immutable — read
only, never edit, move, or delete. And treat needing it as a finding, not a rescue — if the answer
was in a source but not in the wiki, the wiki has a gap. Say so in your answer and offer to run
wiki-ingest on that source, or to write the missing page.

Right now this wiki is close to empty. "The wiki does not cover this" is the expected outcome for
most questions, not an edge case. Reach that conclusion quickly and say it plainly.

## 2. Answer

**Cite with wikilinks.** Every substantive claim carries the page it came from — `Bush proposed the
memex in 1945 ([[As We May Think]])`. This is what lets the human check you and jump to the page.
An uncited claim reads as if it came from nowhere, because it did.

**Separate what the wiki says from what you concluded.** Sourced claims get citations; your own
synthesis gets marked as yours ("reading these together, the pattern is..."). Blurring the two is
how a confident inference becomes a remembered fact.

**Surface disagreement, do not resolve it silently.** If two pages conflict, present both with their
citations and say which is better supported and why — and note that a `## Contradictions` section on
the relevant page is where this belongs permanently (see `CLAUDE.md`). Offer to add it.

**When the wiki does not know, say so.** Do not backfill from general knowledge, and do not pad the
gap with plausible-sounding context — the value of this wiki is that its contents are traceable to
sources the human chose. State the gap, then offer the real options: research it (clearly marked as
outside-the-wiki knowledge), or point at a source to ingest.

## 3. Choose the output form

- **Prose in chat** — the default. Most questions want an answer, not an artifact.
- **A comparison table** — when the question is comparative ("compare X and Y", "which of these
  does Z"). Tables are for genuinely parallel dimensions; do not force prose into a grid.
- **A filed note** — when the answer is durable. See below.

Slides, charts, and diagrams are possible but not set up in this project. Mention it if the human
seems to want one; do not build tooling for it unasked.

## 4. File durable answers

This is the point of the operation. An answer that only exists in chat history has to be re-derived
the next time it comes up.

The test — **would the human want this answer again without re-deriving it?**

- **File it**: comparisons, analyses, syntheses, connections drawn between pages, answers to
  "what's the state of my thinking on X", anything that took real reading to assemble.
- **Do not file it**: lookups, "which page says X", "when was Y", clarifications of something you
  just said. A wiki full of one-line answers is noise, and noise makes the index useless.
- **Close call**: offer, do not assume. "Worth filing as a note?" costs one line.

When you file, do all four steps — a note that skips any of them is half-filed:

**1. Write the page** at `wiki/notes/<Exact Title>.md`. Filename is the title, exactly, Title Case,
flat in `notes/`, so `[[Exact Title]]` resolves with no alias. Frontmatter keys in schema order.
`sources:` lists the source pages the answer draws on, transitively — if you used a concept page
that cites `[[As We May Think]]`, that source belongs here too.

**2. Add the index line** under `### Notes` in `index.md`, and bump `index.md`'s own `updated:`.
The `### Notes` section currently reads `_(filed answers, comparisons, analyses — none yet)_` —
**replace that placeholder** with your line rather than adding underneath it, or it sits above real
entries forever.

**3. Append to `log.md`.** Newest at the bottom, never rewrite earlier entries. Only file-worthy
queries get a log entry — logging every lookup fills the history with the same noise you just
declined to file.

**4. Add an inbound link.** A page nothing links to is a bug. The index line is a catalog entry, not
a link — go to the most related entity, concept, or source page and add a real `[[mention]]` in its
prose, plus a bumped `updated:`. If there is genuinely no page to link from, say so in your answer
instead of leaving the note orphaned.

## Worked example

The human asks "how does Bush's memex differ from modern RAG?" — a comparison, durable, so it gets
filed. (Illustrative only; these pages do not exist in this vault.)

`wiki/notes/Memex vs Modern RAG.md`:

```markdown
---
title: Memex vs Modern RAG
type: note
tags: [comparison, retrieval]
created: 2026-08-18
updated: 2026-08-18
status: developing
sources: ["[[As We May Think]]"]
---

Both [[Memex]] and retrieval-augmented generation attack the same problem — finding the relevant
thing in a corpus too large to hold in mind — but they put the associative work in different hands.

## Where they agree

Bush's complaint was that indexes are artificial. Retrieval by rigid category loses the thing you
half-remember ([[As We May Think]]). RAG shares the diagnosis and answers it with embeddings, which
retrieve by similarity rather than by filing category.

## Where they diverge

The memex's trails are authored. A researcher walks a path once and it persists, reviewable and
shareable ([[As We May Think]]). RAG's retrieval is computed per query and discarded — nothing
accumulates, and the second reader gets no benefit from the first reader's path.

My read, not the sources': this is the sharper difference than the usual analog-versus-neural
framing. Bush was designing a memory that compounds; RAG is a lookup that does not.

## Open question

Whether anything in current practice recovers the durable-trail property. Nothing in the wiki
addresses this yet — worth a source.
```

`index.md`, under `### Notes`:

```markdown
- [[Memex vs Modern RAG]] — where Bush's associative trails differ from retrieval-augmented generation.
```

`log.md`, appended at the bottom:

```markdown
## [2026-08-18] query | How does Bush's memex differ from modern RAG?
Compared authored trails against computed retrieval; both share the diagnosis, differ on whether
paths persist. Read [[Memex]], [[As We May Think]], [[Retrieval-Augmented Generation]].
Filed [[Memex vs Modern RAG]]; linked inbound from [[Memex]].
Gap noted — nothing in the wiki on durable retrieval trails in current systems.
```
