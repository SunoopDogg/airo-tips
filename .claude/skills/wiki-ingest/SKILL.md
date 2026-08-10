---
name: wiki-ingest
description: Read a new source document and integrate it into this LLM Wiki — write its source page, update every existing entity and concept page it touches, record contradictions, refresh index.md and log.md. Use this whenever a source needs to enter the wiki, and lean toward using it rather than hand-editing pages — "ingest this", "process this source", "I dropped a new article in raw/", "add this paper to the wiki", "read this and file it", "here's a new source", "can you write this up", a bare file path or URL offered with any hint that it belongs in the wiki, a pasted article or transcript, or a batch like "ingest everything in raw/" or "process these five PDFs". Also use it when the human describes new material rather than naming it ("I found a good piece on X, put it in"), when a query turns up a source that was never ingested, or when someone asks what a source would change in the wiki. Do NOT use it to answer questions from the wiki's existing contents (that is wiki-query) or to audit the wiki for contradictions, orphans, stale claims, and broken links (that is wiki-lint).
---

# Ingest a source

A source arrives; the wiki absorbs it. The output is not a summary page — it is a summary page
*plus* every edit that source implies across the pages you already have. A source that creates six
new pages and updates none has not been integrated, it has been filed next to the wiki.

One source realistically touches 5–15 pages. Default to one source at a time with the human in the
loop; batch mode is at the bottom, for when they ask.

`raw/` is **immutable**. Read it, never edit, move, rename, or delete anything inside it. If a raw
file is malformed, note that on the source page and work with what is there. Everything you write
lives under `wiki/`, `index.md`, or `log.md`.

Conventions — frontmatter keys and order, filenames, link style, log and index formats — are frozen
in `CLAUDE.md`. Read it if you have not this session. Dataview is not installed in this vault, so
never emit Dataview queries; plain YAML frontmatter only.

## 1. Read the source completely

Read the whole thing before deciding anything. Skimming produces pages that repeat the abstract.

Markdown clipped from the web hangs images off the text: read the markdown first, then look at
which `![](raw/assets/...)` images the text actually leans on and view those separately with Read.
A chart, diagram, screenshot, or table-as-image often carries the claim the prose only gestures at.
Skip decorative images — author avatars, logos, spacers.

PDFs: read them in page ranges. Long transcripts: read straight through; the useful material is
usually scattered, not in a conclusion section.

Note as you go: proper nouns, recurring concepts, dated claims, numbers, quotable lines, and
anything that sounds like it disagrees with something you have already filed.

## 2. Orient in the existing wiki

Before writing, find out what the wiki already knows. Two moves:

- Read `index.md` top to bottom. It is the catalog, and it is short — this is the cheapest way to
  see every page that exists.
- Grep `wiki/` for the source's proper nouns and key terms, including near-misses. `grep -ril
  "memex" wiki/` finds the pages that mention a thing without having a page for it.

Read the pages that come back. You are looking for three things: pages this source *extends*, pages
it *contradicts*, and concepts mentioned repeatedly across pages that still have no page of their
own — this source may be the one that earns them a page.

On an empty or near-empty wiki this step legitimately returns nothing, and the first ingest is
mostly new pages. It stops being true fast. By the third or fourth source, "nothing to update" means
you did not search hard enough.

## 3. Decide what deserves a page

A new page is warranted when the thing has enough substance to say something beyond a definition,
and when you expect it to recur across sources. Otherwise it is a mention on a page that already
exists — a linked name in a sentence is not a loss, and `[[Some Concept]]` pointing at a file that
does not exist yet is a legitimate marker that it might later.

Prefer editing an existing page over creating a near-duplicate. `Memex` and `The Memex` must not
both exist; search before you create.

Placement: `wiki/entities/` for things with a proper name (people, orgs, places, products,
characters), `wiki/concepts/` for ideas, themes, mechanisms, recurring topics. Filename is the page
title exactly, Title Case, flat inside the folder.

## 4. Check in with the human

Send **one** message before writing: 5–10 key takeaways, plus the plan — which pages you would
create, which existing pages you would update, and any contradiction you spotted. Then write on
acknowledgment.

The human's job here is steering emphasis: they know which thread matters and which is trivia, and
that judgment is expensive to recover later. Their job is not approving each page — do not run a
confirm-per-page loop, and do not ask questions you can answer by reading. If they say nothing about
a proposal, proceed with it.

## 5. Write the source page

One page per raw source, in `wiki/sources/`, titled with the source's own title, not its filename —
`raw/as-we-may-think.md` becomes `wiki/sources/As We May Think.md`.
`sources:` is `[]` for source pages — they are the root of the citation graph — and they carry
`source_path` and `ingested` immediately after `sources`.

```markdown
---
title: As We May Think
type: source
tags: [essay, memex, information-retrieval]
created: 2026-08-18
updated: 2026-08-18
status: stable
sources: []
source_path: raw/as-we-may-think.md
ingested: 2026-08-18
---

Vannevar Bush's July 1945 *Atlantic* essay arguing that the postwar scientific effort should turn
from weapons to making the human record accessible.

## What this is

An essay by [[Vannevar Bush]], then head of the US Office of Scientific Research and Development,
written for a general audience. It is discursive rather than technical — the machines it describes
are sketches, not designs.

## Key claims

- The bottleneck in research is retrieval, not production: specialization has outrun any one
  researcher's ability to find what is already known.
- Indexing by hierarchy fights the mind, which works by association. See [[Associative Indexing]].
- The [[Memex]] — a desk that stores a library on microfilm and lets a user build named trails of
  linked documents — would make those associative paths shareable and permanent.

## Notable quotes

> "The summation of human experience is being expanded at a prodigious rate, and the means we use
> for threading through the consequent maze to the momentarily important item is the same as was
> used in the days of square-rigged ships."

## What it changed here

Created [[Memex]], [[Associative Indexing]], [[Vannevar Bush]]. Added the pre-digital origin of
hypertext to [[Hypertext]], which previously started at [[Project Xanadu]].
```

Keep "What it changed here" honest — it is the diff of this ingest, and a lint pass reads it later.

## 6. Update the pages this source touches

This is the real work; budget most of your effort here.

For each existing page the source bears on, add what the source contributes — a claim, a date, a
correction, a new connection — cited inline: `Bush proposed the memex in 1945 ([[As We May Think]]).`
Add the source to that page's `sources:` list, and bump `updated:`.

Link generously. Every proper noun or named concept with a page (or one it deserves) becomes
`[[Link]]` on first mention in the body.

**Contradictions are never silently overwritten.** When the source disagrees with something already
on a page, add or extend a `## Contradictions` section on the affected page: state both claims, cite
both sources, and say which is better supported and why — primary over secondary, specific over
vague, later over earlier when the later source had access to more. If you genuinely cannot tell,
write that. A newer source is not automatically right, and disagreement between sources is
information; losing it is the main way this wiki degrades.

**No new page is left orphaned.** Every page you create needs at least one inbound `[[link]]` from
somewhere other than `index.md` — usually the source page, better still a related concept or entity
page. If nothing in the wiki naturally links to a new page, that is a signal it should have been a
mention instead.

## 7. Bookkeeping

- `index.md`: add one line per new page under its `### Entities` / `### Concepts` / `### Sources` /
  `### Notes` heading, in the form `- [[Vannevar Bush]] — engineer who proposed the memex in 1945.`
  Replace the `_(none yet)_` placeholder under a heading rather than appending beneath it. Revise
  existing lines whose summary the source made wrong.
- `log.md`: append at the bottom, never rewrite past entries. Exact heading prefix, then 2–5 lines
  covering what changed and every page touched as `[[links]]`:

  ```
  ## [2026-08-18] ingest | As We May Think
  Ingested Bush's 1945 essay. Created [[Memex]], [[Associative Indexing]], [[Vannevar Bush]].
  Updated [[Hypertext]] with its pre-digital origin; noted a date conflict with [[Project Xanadu]]
  on its Contradictions section.
  ```
- Bump `updated:` on **every** page you edited, including `index.md` and `log.md` themselves. A
  stale `updated:` makes the next lint pass untrustworthy.
- Move `status:` along when the page earns it: `stub` → `developing` → `stable`.

Then verify quickly: every new page has an inbound link, every new page is in `index.md`, every
claim you added carries a citation, and the log entry names the same pages you actually touched.

## Batch mode

When the human asks for several sources at once, skip the per-source checkpoint and report once at
the end — a table of source → pages created → pages updated → contradictions found. Everything else
holds, especially step 2: ingest sources one at a time in sequence so that source three can update
the pages source one created. Ingesting them in parallel produces a pile of disconnected pages,
which is the failure this whole skill exists to prevent.
