---
name: lint
description: Audit and maintain the health of this repository's LLM wiki. Use when the user asks to lint, health-check, validate, clean up, repair, or find contradictions, stale claims, broken links, orphan pages, index drift, schema errors, missing concepts, weak provenance, duplicate pages, or research gaps in wiki/.
---

# Lint the wiki

Follow the repository-root `AGENTS.md`. Default to a read-only audit. Apply repairs only when the user explicitly asks to fix, clean up, or maintain the wiki.

## 1. Establish scope

Inspect `git status --short`, `index.md`, recent `log.md` entries, and all page paths. Preserve unrelated changes and distinguish pre-existing defects from issues introduced during this operation.

## 2. Run deterministic checks first

Check the whole requested scope for:

- invalid or missing YAML fields, unquoted frontmatter wikilinks, invalid page types, and filename/title mismatch;
- broken `[[wikilinks]]`, ambiguous duplicate titles, self-links, and links to non-page names;
- pages missing from the index, stale index entries, wrong sections, duplicate entries, and sort drift;
- source pages whose `source_path:` path is missing, and raw files with no source page;
- malformed or reordered log headings without changing existing log history;
- orphan pages with no meaningful inbound links, excluding `index.md` and `log.md`.

Use repository search or a small temporary script for mechanical checks. Do not add a permanent script unless repeated use justifies it.

## 3. Run semantic checks

Read the implicated pages and assess:

- incompatible claims that are not marked as contradictions;
- newer evidence that may supersede a dated claim;
- claims with absent, circular, weak, or misleading provenance;
- near-duplicate concepts and fragmented pages;
- important recurring concepts that deserve their own page;
- missing cross-references and links that appear related but are not substantively justified;
- knowledge gaps and concrete follow-up sources or questions.

Do not label different scopes, dates, definitions, or source opinions as contradictions until compared in context.

## 4. Report or repair

For an audit, make no edits and report findings by severity (`error`, `warning`, `suggestion`) with file paths, evidence, and a concrete remedy. State explicitly when a check is clean.

For an authorized repair:

1. Apply unambiguous mechanical fixes.
2. Preserve competing claims and provenance; ask before merges, deletions, renames with broad link impact, or judgment-heavy rewrites.
3. Never modify `raw/`.
4. Update `index.md` when page inventory changes.
5. Append one completed `lint` entry to `log.md` only if files were changed.
6. Rerun mechanical checks and inspect the final diff.

Finish with counts by severity, repairs made, unresolved decisions, and recommended research gaps.
