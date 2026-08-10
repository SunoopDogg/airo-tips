#!/usr/bin/env python3
"""airo-tips 위키 기계 검사. 저장소 루트에서: python3 .claude/skills/wiki-lint/check.py

오류(exit 1): 프론트매터 키·순서·type·폴더·title·status·날짜, source 페이지 추가 키,
              고아 페이지, index.md 드리프트(누락·유령·섹션·형식)
경고:         미해결 링크, updated < mtime, source_path 부재, 금지 패턴(Dataview·작업 이력·
              작업 시점·개인정보·금액 의심)

셸로 다시 짜지 말 것: macOS sort/uniq/comm 은 한글에서 깨지고, APFS 파일명은 NFD, 본문은 NFC다.
"""
import datetime as dt
import pathlib
import re
import sys
import unicodedata as ud

ROOT = pathlib.Path(__file__).resolve().parents[3]
KEYS = ["title", "type", "tags", "created", "updated", "status", "sources"]
FOLDER = {"topic": "topics", "source": "sources"}
SECTION = {"Topics": "topic", "Sources": "source"}
LINK = re.compile(r"\[\[([^\]]+)\]\]")
FORBIDDEN = [
    (r"```dataview", "Dataview 블록"),
    (r"^## What it changed here", "작업 이력 절"),
    (r"\(20\d\d-\d\d-\d\d 확정\)", "작업 시점 표기"),
    (r"인제스트", "작업 이력 서술 의심"),
    (r"0\d{1,2}-\d{3,4}-\d{4}", "전화번호 의심"),
    (r"[\w.+-]+@[\w-]+\.[\w.]+", "이메일 의심"),
    (r"\d[\d,]*\s*(천만|만|억)?\s*원(?![가-힣])", "금액 의심"),
]

nfc = lambda s: ud.normalize("NFC", s)
norm = lambda t: nfc(t.split("|")[0].split("\\")[0].split("#")[0]).strip().casefold()

errors, warns = [], []
E, W = errors.append, warns.append

pages = {nfc(p.stem): p for p in (ROOT / "wiki").rglob("*.md")}
pages.update({"index": ROOT / "index.md", "log": ROOT / "log.md"})
targets = {k.casefold(): k for k in pages}
types, inbound, indexed = {}, {k: set() for k in pages}, set()

for stem, p in pages.items():
    text = nfc(p.read_text())
    rel = p.relative_to(ROOT)
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    fm, keys = {}, []
    if not m:
        E(f"{rel}: 프론트매터 없음")
    else:
        lines = [l for l in m.group(1).split("\n") if re.match(r"\w", l)]
        keys = [l.split(":", 1)[0].strip() for l in lines]
        fm = {l.split(":", 1)[0].strip(): l.split(":", 1)[1].strip() for l in lines if ":" in l}
        t = fm.get("type")
        types[stem] = t
        if keys[:7] != KEYS:
            E(f"{rel}: 프론트매터 키/순서 {keys}")
        if t not in FOLDER and t != "overview":
            E(f"{rel}: type={t}")
        if t in FOLDER and p.parent.name != FOLDER[t]:
            E(f"{rel}: type={t}인데 폴더가 {p.parent.name}/")
        if nfc(fm.get("title", "")) != stem:
            E(f"{rel}: title '{fm.get('title')}' ≠ 파일명 '{stem}'")
        if t == "source":
            if keys[7:9] != ["source_path", "ingested"]:
                E(f"{rel}: source 페이지는 sources: 바로 뒤에 source_path, ingested")
            if fm.get("source_path") and not (ROOT / fm["source_path"]).exists():
                W(f"{rel}: source_path 없음 — {fm['source_path']}")
        if fm.get("status") not in {"stub", "developing", "stable"}:
            E(f"{rel}: status={fm.get('status')}")
        for k in ("created", "updated"):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fm.get(k, "")):
                E(f"{rel}: {k} 형식 '{fm.get(k)}'")
        mtime = dt.date.fromtimestamp(p.stat().st_mtime).isoformat()
        if fm.get("updated", "9") < mtime:
            W(f"{rel}: updated {fm['updated']} < mtime {mtime}")

    if stem == "log":  # append-only. 지난 항목의 링크는 고치지 않는다
        continue
    for raw in LINK.findall(text):
        tgt = norm(raw)
        if tgt not in targets:
            (E if stem == "index" else W)(f"{rel}: 미해결 링크 [[{raw}]]")
        elif stem == "index":
            indexed.add(targets[tgt])
        elif targets[tgt] != stem:
            inbound[targets[tgt]].add(stem)

    if stem == "index":
        section = None
        for i, line in enumerate(text.split("\n"), 1):
            if line.startswith("### "):
                section = line[4:].strip()
            elif line.startswith("- ") and section in SECTION:
                if not re.fullmatch(r"- \[\[[^\]]+\]\] — .+\.", line):
                    E(f"index.md:{i}: 형식 — '- [[페이지]] — 한 문장.'")
                lk = LINK.search(line)
                if lk and types.get(targets.get(norm(lk.group(1)))) not in (None, SECTION[section]):
                    E(f"index.md:{i}: [[{lk.group(1)}]] 은 {types[targets[norm(lk.group(1))]]}인데 ### {section} 아래")
    elif m:
        body, off = text[m.end():], m.group(0).count("\n")
        for pat, msg in FORBIDDEN:
            for mm in re.finditer(pat, body, re.M):
                W(f"{rel}:{body[:mm.start()].count(chr(10)) + 1 + off}: {msg} — {mm.group(0)[:40]}")

for stem, p in pages.items():
    if stem in ("index", "log"):
        continue
    if not inbound[stem]:
        E(f"{p.relative_to(ROOT)}: 고아 — index.md 외 인바운드 링크 없음")
    if stem not in indexed:
        E(f"{p.relative_to(ROOT)}: index.md 에 없음")

for label, items in (("오류", errors), ("경고", warns)):
    print(f"## {label} {len(items)}")
    print(*items, sep="\n") if items else None
print(f"\n{len(pages) - 2} 페이지 검사")
sys.exit(1 if errors else 0)
