#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pjt-docs 정합성 검사.

검사 항목:
  1. 프론트매터 누락/필수 필드(status, updated) 누락
  2. README.md 지식 지도 표 ↔ 실제 파일 불일치 (표에 없는 문서 / 파일 없는 링크)
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
INDEX_EXEMPT = {"README.md", "CHANGELOG.md", "HELP.md"}   # 인덱스 표 등재 의무 없는 파일
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stale-days", type=int, default=180)
    ap.add_argument("--docs", default="pjt-docs")
    args = ap.parse_args()

    root = Path(args.docs)
    if not root.is_dir():
        print(f"❌ {root} 폴더 없음")
        return 1

    problems = []
    docs = [
        p for p in root.rglob("*.md")
        if not any(part in SKIP_DIRS for part in p.relative_to(root).parts)
    ]

    # 1) 프론트매터 검사 + 4) staleness
    today = date.today()
    for p in docs:
        rel = p.relative_to(root).as_posix()
        if p.name in INDEX_EXEMPT and p.parent == root:
            continue
        text = p.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if fm is None:
            problems.append(f"프론트매터 없음: {rel}")
            continue
        for field in ("status", "updated"):
            if field not in fm:
                problems.append(f"프론트매터 {field} 누락: {rel}")
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

    # 2) 인덱스 표 ↔ 파일 대조
    readme = root / "README.md"
    indexed = set()
    if readme.exists():
        for link in LINK_RE.findall(readme.read_text(encoding="utf-8")):
            if link.startswith(("http://", "https://")):
                continue
            indexed.add((root / link).resolve())
            if not (root / link).exists():
                problems.append(f"인덱스가 없는 파일을 가리킴: README.md → {link}")
        for p in docs:
            if p.name in INDEX_EXEMPT and p.parent == root:
                continue
            if p.resolve() not in indexed:
                problems.append(f"인덱스 미등재 문서: {p.relative_to(root).as_posix()} (README.md 지식 지도에 추가할 것)")
    else:
        problems.append("README.md(인덱스) 없음")

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
