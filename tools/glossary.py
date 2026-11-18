"""작품의 GLOSSARY.md 에서 '설정'과 '함수' 절을 piece.py 로부터 자동으로 만들고 갱신한다.

    python tools/glossary.py pieces/<slug>/piece.py

- 설정: 맨 앞 설정 블록의 `이름 = 값  # 뜻 (범위)` 주석에서 뽑는다. 설정 블록의 소제목(# ===== ② 등장 설정 =====)이
  용어집의 절이 된다. 형식은 `이름 : 뜻 : 단위·범위` (eyeTutorial Glossary.txt 방식 + 범위 칸).
- 함수: def 이름과 docstring 첫 줄.
- 손으로 쓴 절(일반 용어, 장면 변수, 키 등)은 그대로 둔다. 자동 절은 아래 표시 사이만 바꾼다.
      <!-- auto settings --> … <!-- end auto settings -->
      <!-- auto functions --> … <!-- end auto functions -->
"""
import ast
import io
import os
import re
import sys
import tokenize

CODE_MARK = "# ===== 코드 ====="


def _comments(text):
    """줄 번호 → 그 줄의 주석 (문자열 안의 # 은 주석이 아님)."""
    out = {}
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type == tokenize.COMMENT:
            out[tok.start[0]] = tok.string.lstrip("#").strip()
    return out


def _split_range(comment):
    """주석 끝의 괄호는 '단위·범위' 칸으로: '등장 길이 (초)' → ('등장 길이', '초')."""
    m = re.search(r"\(([^()]*)\)\s*$", comment)
    if not m:
        return comment or "—", "—"
    return (comment[:m.start()].strip() or "—"), (m.group(1).strip() or "—")


def settings_entries(src):
    """[(절 이름, [(이름, 뜻, 범위), …]), …]. 절은 '# ===== ② 등장 설정 =====' 같은 소제목."""
    head = src.partition(CODE_MARK)[0]
    comments = _comments(head)
    titles = {}
    for no, line in enumerate(head.splitlines(), start=1):
        m = re.match(r"^# =+ (.+?) =+\s*$", line)
        if m:
            titles[no] = m.group(1).split(":")[0].strip()
    assigns = []
    for node in ast.parse(head).body:
        if not isinstance(node, ast.Assign):
            continue
        names = []
        for target in node.targets:
            for e in (target.elts if isinstance(target, ast.Tuple) else [target]):
                if isinstance(e, ast.Name) and e.id.isupper() and e.id != "RANGES":
                    names.append(e.id)
        if names:
            assigns.append((node.lineno, names))
    sections, cur = [], None
    events = sorted([(no, "title", t) for no, t in titles.items()] + [(no, "assign", n) for no, n in assigns])
    for no, kind, val in events:
        if kind == "title":
            cur = (val, [])
            sections.append(cur)
            continue
        if cur is None:
            cur = ("설정", [])
            sections.append(cur)
        meaning, rng = _split_range(comments.get(no, ""))
        for n in val:
            cur[1].append((n, meaning, rng))
    return [s for s in sections if s[1]]


def function_entries(src):
    code = src.partition(CODE_MARK)[2]
    out = []
    for node in ast.parse(code).body:
        if isinstance(node, ast.FunctionDef):
            doc = (ast.get_docstring(node) or "—").strip().splitlines()[0]
            out.append((node.name, doc))
    return out


def render_settings(src):
    lines = ["<!-- auto settings -->"]
    for title, items in settings_entries(src):
        lines.append("")
        lines.append("--- %s ---" % title)
        for name, meaning, rng in items:
            lines.append("%s : %s : %s" % (name, meaning, rng))
    lines.append("<!-- end auto settings -->")
    return "\n".join(lines)


def render_functions(src):
    lines = ["<!-- auto functions -->", "", "--- 함수 ---"]
    for name, doc in function_entries(src):
        lines.append("%s : %s : —" % (name, doc))
    lines.append("<!-- end auto functions -->")
    return "\n".join(lines)


DEFAULT = """# 용어집 — {title}

형식: `이름 : 뜻 : 단위·범위` (eyeTutorial Glossary.txt 방식 + 범위 칸). 이름 하나에 뜻 하나.
설정·함수 절은 `python tools/glossary.py {rel}` 로 자동 갱신된다. 나머지 절은 손으로 쓴다.

--- 일반 용어 ---
칸 : 글자 하나가 들어가는 자리 (cell) : COLS×ROWS 개
램프 : 어두움→밝음 순으로 늘어놓은 글자열 : 문자열
phase : 모션 한 루프의 진행도. 0 과 1 이 같은 장면 : 0~1
p : 등장 진행도. 1 이면 완성 화면 : 0~1

{settings}

{functions}

--- 키 (창 재생) ---
Space : 정지 / 재생 : —
R : 등장부터 다시 : —
S : 지금 프레임을 PNG 로 저장 : —
←→ : 한 프레임 이동 : —
Esc : 끝내기 : —
"""


def update(piece_path, title=None):
    src = open(piece_path, encoding="utf-8").read()
    path = os.path.join(os.path.dirname(piece_path), "GLOSSARY.md")
    settings, functions = render_settings(src), render_functions(src)
    if os.path.exists(path):
        text = open(path, encoding="utf-8").read()
        for tag, block in (("settings", settings), ("functions", functions)):
            pat = re.compile(r"<!-- auto %s -->.*?<!-- end auto %s -->" % (tag, tag), re.S)
            text = pat.sub(lambda _m: block, text) if pat.search(text) else text.rstrip() + "\n\n" + block + "\n"
    else:
        rel = os.path.relpath(piece_path)
        if rel.startswith(".."):
            rel = os.path.abspath(piece_path)
        text = DEFAULT.format(title=title or os.path.basename(os.path.dirname(piece_path)), rel=rel,
                              settings=settings, functions=functions)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1 or not args[0].endswith(".py"):
        print("사용법: python tools/glossary.py pieces/<slug>/piece.py", file=sys.stderr)
        return 2
    print("용어집 갱신:", update(args[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
