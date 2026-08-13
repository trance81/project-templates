---
status: active
updated: YYYY-MM-DD
source: 작성자 직접
revisit: 없음(영구)
---

# 0001. pjt-docs 지식관리 구조 도입

## 결정
프로젝트 지식을 특정 AI 도구 폴더(.claude 등)가 아닌 pjt-docs/에 일반 문서로 관리한다. 표준은 project-templates 리포의 STRUCTURE.md.

## 이유
- 특정 AI에 종속되면 도구를 바꾸거나 사람이 볼 때 지식이 갇힌다
- git 커밋/풀만으로 회사·집·외부 어디서든 동일한 지식 확보
- 인덱스(README)와 이력(CHANGELOG)으로 AI·사람 모두 현황 파악 가능

## 재론 조건
없음 — 구조 자체 변경은 project-templates 리포에서 결정한다.
