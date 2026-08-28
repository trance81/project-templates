#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pjt-docs 정합성 검사.

검사 항목:
  1. 문서 메타데이터 누락/필수 필드(status, updated) 누락
  2. 인덱스 ↔ 실제 파일 불일치 (표에 없는 문서 / 파일 없는 링크)
     - 기본 인덱스는 README.md 지식 지도 표
     - _index.md 가 있는 하위 폴더는 그 폴더 아래 문서를 그 _index.md 가 등재한다.
       README 에는 _index.md 한 줄만 올린다 (STRUCTURE.md 3장)
  3. 문서 안 깨진 상대 링크
  4. status: active 인데 updated 가 오래된 문서 (기본 180일 — --stale-days 로 조정)

사용: python scripts/check-docs.py [--stale-days 180] [--docs pjt-docs]
종료코드: 문제 있으면 1, 없으면 0
"""
import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8")  # Windows cp949 콘솔 대비

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)#]+)(?:#[^)]*)?\)")
INDEX_EXEMPT = {"README.md", "CHANGELOG.md", "HELP.md"}   # 루트에서 인덱스 표 등재 의무 없는 파일
SUBINDEX = "_index.md"                                 # 하위 트리 인덱스. 메타데이터 의무 없음
SKIP_DIRS = {"local", "원본"}                          # 검사 제외 (로컬 전용·원본 보존)


def parse_frontmatter(text):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    fields = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    return fields


def is_exempt(p, root):
    """메타데이터·등재 의무가 없는 파일: 루트의 README/CHANGELOG/HELP, 어디든 _index.md"""
    return (p.name in INDEX_EXEMPT and p.parent == root) or p.name == SUBINDEX


def nearest_subindex(p, root):
    """p 를 등재해야 할 _index.md. 가장 가까운 상위 폴더(루트 제외)의 것. 없으면 None.
    _index.md 자신은 한 단계 위 폴더부터 찾는다 (자기 자신에 등재할 수는 없으므로)."""
    d = p.parent.parent if p.name == SUBINDEX else p.parent
    while d != root:
        if root not in d.parents:
            return None
        cand = d / SUBINDEX
        if cand.exists():
            return cand
        d = d.parent
    return None


def links_in(path):
    out = set()
    for link in LINK_RE.findall(path.read_text(encoding="utf-8")):
        if link.startswith(("http://", "https://", "mailto:")):
            continue
        out.add((path.parent / link).resolve())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stale-days", type=int, default=180)
    ap.add_argument("--docs", default="pjt-docs")
    args = ap.parse_args()

    root = Path(args.docs)
    if not root.is_dir():
        print(f"❌ {root} 폴더 없음")
        return 1
    root = root.resolve()

    problems = []
    docs = [
        p for p in root.rglob("*.md")
        if not any(part in SKIP_DIRS for part in p.relative_to(root).parts)
    ]

    # 1) 문서 메타데이터 검사 + 4) staleness
    today = date.today()
    for p in docs:
        rel = p.relative_to(root).as_posix()
        if is_exempt(p, root):
            continue
        text = p.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if fm is None:
            problems.append(f"문서 메타데이터 없음: {rel}")
            continue
        for field in ("status", "updated"):
            if field not in fm:
                problems.append(f"문서 메타데이터 {field} 누락: {rel}")
        status = fm.get("status", "")
        if status not in ("draft", "active", "deprecated", ""):
            problems.append(f"status 값 이상({status}): {rel}")
        if "updated" in fm:
            try:
                upd = datetime.strptime(fm["updated"], "%Y-%m-%d").date()
                if status == "active":
                    age = (today - upd).days
                    if age > args.stale_days:
                        problems.append(f"신선도 경고: {rel} — active인데 {age}일 경과 (updated {fm['updated']}). 내용 확인 후 updated 갱신 또는 deprecated 처리")
            except ValueError:
                problems.append(f"updated 형식 오류(YYYY-MM-DD 아님): {rel}")

    # 2) 인덱스 ↔ 파일 대조. 문서마다 자기를 등재해야 할 인덱스가 하나 정해진다.
    readme = root / "README.md"
    if not readme.exists():
        problems.append("README.md(인덱스) 없음")
    index_files = ([readme] if readme.exists() else []) + [p for p in docs if p.name == SUBINDEX]
    indexed_by = {}   # 인덱스 파일 -> 그 파일이 가리키는 문서 집합
    for idx in index_files:
        targets = links_in(idx)
        indexed_by[idx] = targets
        for t in targets:
            if not t.exists():
                problems.append(f"인덱스가 없는 파일을 가리킴: {idx.relative_to(root).as_posix()} → {t.relative_to(root).as_posix() if root in t.parents else t}")

    for p in docs:
        if p.name in INDEX_EXEMPT and p.parent == root:
            continue
        owner = nearest_subindex(p, root)
        if owner is None:
            owner = readme if readme.exists() else None
        if owner is None:
            continue
        if p.resolve() not in indexed_by.get(owner, set()):
            where = owner.relative_to(root).as_posix()
            hint = "README.md 지식 지도에 추가할 것" if owner == readme else f"{where} 에 추가할 것"
            problems.append(f"인덱스 미등재 문서: {p.relative_to(root).as_posix()} ({hint})")

    # 3) 각 문서의 깨진 상대 링크
    for p in docs:
        for link in LINK_RE.findall(p.read_text(encoding="utf-8")):
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            if not (p.parent / link).exists():
                problems.append(f"깨진 링크: {p.relative_to(root).as_posix()} → {link}")

    if problems:
        print(f"❌ {len(problems)}건 발견:\n")
        for pr in problems:
            print(f"  - {pr}")
        return 1
    print(f"✅ 문제 없음 ({len(docs)}개 문서 검사)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
