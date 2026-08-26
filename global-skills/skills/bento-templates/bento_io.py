# -*- coding: utf-8 -*-
"""bento 덱의 #bento-doc JSON 블록을 안전하게 읽고 쓴다.

HTML 런타임은 절대 건드리지 않고 JSON 블록만 교체한다.
`<` 를 \\u003c 로 이스케이프해 페이로드 안에 </script 가 생기지 않게 한다.
"""
import io
import json
import os
import re
import shutil
import subprocess
import tempfile

RELEASE_URL = "https://bento.page/releases/slides/Bento_Slides.bento.html"

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


def check(doc, width=1280, margin=96, roles=False):
    """간단 검증 — 노트 누락과 좌우 여백 침범을 잡아낸다. 문제 목록을 돌려준다.

    roles=True 이면 텍스트 요소에 `role`(title/subtitle/body/kicker) 이 하나도
    없는 슬라이드도 경고한다 (레이아웃 재적용을 위해 1.0.18+ 에서 권장).
    """
    right = width - margin
    bad = []
    for s in doc.get("slides", []):
        if not s.get("notes"):
            bad.append("notes 누락: %s" % s.get("id"))
        has_role = False
        for e in s.get("elements", []):
            if not isinstance(e, dict):          # 헬퍼가 리스트를 반환했는데 append 한 경우
                bad.append("요소가 dict 가 아님: %s (append 대신 += 사용)" % s.get("id"))
                continue
            if e.get("x", 0) + e.get("w", 0) > right + 0.5:
                bad.append("우측 여백 침범: %s/%s" % (s.get("id"), e.get("id")))
            if e.get("type") == "text" and e.get("role"):
                has_role = True
        if roles and not has_role and s.get("elements"):
            bad.append("텍스트 role 없음: %s" % s.get("id"))
    return bad


def runtime_version(path):
    """덱 파일에 박힌 bento 앱 런타임 버전 문자열(예: '1.0.18'). 못 찾으면 None."""
    import base64
    import zlib
    h = io.open(path, encoding="utf-8", errors="ignore").read()
    m = re.search(r'<script id="bento-rt" type="bento/deflate-b64">([^<]*)</script>', h)
    if not m:
        return None
    raw = base64.b64decode(m.group(1))
    for w in (15, -15, 31):
        try:
            js = zlib.decompress(raw, w).decode("utf-8", "ignore")
            # 앱 버전 상수는 `const xx="1.0.18",` 꼴로 박혀 있다 (라이브러리 버전과 구분)
            v = re.findall(r'const [A-Za-z_$][\w$]*="(\d+\.\d+\.\d+)",', js)
            return v[0] if v else None
        except Exception:
            pass
    return None


def fetch_latest(dest):
    """bento.page 에서 최신 앱 셸을 dest 로 내려받는다. 실패 시 예외."""
    for cmd in (["curl", "-fsSL", RELEASE_URL, "-o", dest],
                ["powershell", "-NoProfile", "-Command",
                 "iwr '%s' -OutFile '%s'" % (RELEASE_URL, dest)]):
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
            h = io.open(dest, encoding="utf-8", errors="ignore").read()
            if OPEN in h and 'id="bento-rt"' in h:
                return dest
        except Exception:
            continue
    raise RuntimeError("최신 Bento 셸 다운로드 실패: " + RELEASE_URL)


def refresh_runtime(path, shell=None, backup=True):
    """기존 덱의 앱 런타임만 최신으로 교체한다. 문서 JSON·docId·collab·assets·<title> 은 그대로.

    shell: 이미 받아둔 최신 셸 경로. None 이면 bento.page 에서 새로 받는다.
    backup: True 면 <path>.bak 를 남긴다.
    """
    old_html, i, j = _split(path)
    doc = json.loads(old_html[i + len(OPEN):j])
    title = re.search(r"<title>.*?</title>", old_html, re.S)

    tmp = None
    if shell is None:
        fd, tmp = tempfile.mkstemp(suffix=".bento.html")
        os.close(fd)
        shell = fetch_latest(tmp)
    new_html = io.open(shell, encoding="utf-8").read()
    ni = new_html.index(OPEN)
    nj = new_html.index(CLOSE, ni)

    payload = json.dumps(doc, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c")     # 반드시 두 글자 백슬래시+u
    assert "</script" not in payload
    out = new_html[:ni + len(OPEN)] + "\n" + payload + "\n" + new_html[nj:]
    if title:
        out = re.sub(r"<title>.*?</title>", lambda m: title.group(0), out, count=1, flags=re.S)

    if backup:
        shutil.copyfile(path, path + ".bak")
    io.open(path, "w", encoding="utf-8", newline="").write(out)
    if tmp:
        os.remove(tmp)
    return runtime_version(path)
