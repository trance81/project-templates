# -*- coding: utf-8 -*-
"""bento 덱의 #bento-doc JSON 블록을 안전하게 읽고 쓴다.

HTML 런타임은 절대 건드리지 않고 JSON 블록만 교체한다.
`<` 를 \\u003c 로 이스케이프해 페이로드 안에 </script 가 생기지 않게 한다.
"""
import io
import json

OPEN = '<script type="application/bento+json" id="bento-doc">'
CLOSE = '</script>'


def _split(path):
    h = io.open(path, encoding="utf-8").read()
    i = h.index(OPEN)
    j = h.index(CLOSE, i)
    return h, i, j


def load(path):
    """덱 파일에서 문서 JSON(dict)을 읽는다."""
    h, i, j = _split(path)
    return json.loads(h[i + len(OPEN):j])


def save(path, doc):
    """문서 JSON을 같은 파일에 다시 써넣는다. 런타임·나머지 HTML은 보존."""
    h, i, j = _split(path)
    payload = json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c")     # 반드시 두 글자 백슬래시+u
    assert "</script" not in payload, "페이로드에 </script 가 남아 있다"
    io.open(path, "w", encoding="utf-8", newline="").write(
        h[:i + len(OPEN)] + "\n" + payload + "\n" + h[j:])


def insert(doc, path, keep=("docId", "collab", "assets", "modified")):
    """새로 만든 doc 를 기존 파일에 넣되, 파일에 있던 식별자·에셋은 보존한다.

    이미 만들어진 덱을 갱신할 때 사용한다. 사용자가 편집기에서 넣은
    로고(assets)나 문서 식별자(docId)가 날아가는 것을 막는다.
    """
    old = load(path)
    for k in keep:
        if k in old and k not in doc:
            doc[k] = old[k]
    save(path, doc)
    return doc


def check(doc, width=1280, margin=96):
    """간단 검증 — 노트 누락과 좌우 여백 침범을 잡아낸다. 문제 목록을 돌려준다."""
    right = width - margin
    bad = []
    for s in doc.get("slides", []):
        if not s.get("notes"):
            bad.append("notes 누락: %s" % s.get("id"))
        for e in s.get("elements", []):
            if not isinstance(e, dict):          # 헬퍼가 리스트를 반환했는데 append 한 경우
                bad.append("요소가 dict 가 아님: %s (append 대신 += 사용)" % s.get("id"))
                continue
            if e.get("x", 0) + e.get("w", 0) > right + 0.5:
                bad.append("우측 여백 침범: %s/%s" % (s.get("id"), e.get("id")))
    return bad
