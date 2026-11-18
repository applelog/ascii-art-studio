"""pieces/ 아래 모든 작품을 자동으로 검사한다.

- 같은 코드 → 같은 그림 (결정성)
- 미리보기 = 코드: versions/<v>/preview.png (또는 ②·③ 의 strip.png) 가 그 버전의 piece.py 로 다시 렌더한 그림과 픽셀까지 같다
- 맨 앞 설정 블록이 있고, 렌더 경로에 random/time 이 없다
- 용어집에 같은 이름이 두 번 나오지 않는다
"""
import ast
import glob
import importlib.util
import os
import re

import numpy as np
import pytest
from PIL import Image

from asciiart.run import render_still

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIECES = sorted(glob.glob(os.path.join(ROOT, "pieces", "*", "piece.py")))
VERSIONS = sorted(glob.glob(os.path.join(ROOT, "pieces", "*", "versions", "*", "piece.py")))


def load(path):
    name = "piece_" + re.sub(r"\W", "_", os.path.relpath(path, ROOT))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return vars(mod)


def ids(paths):
    return [os.path.relpath(p, os.path.join(ROOT, "pieces")) for p in paths]


@pytest.mark.parametrize("path", PIECES, ids=ids(PIECES))
def test_settings_block_first(path):
    src = open(path, encoding="utf-8").read()
    head, sep, _ = src.partition("# ===== 코드 =====")
    assert sep, "'# ===== 코드 =====' 줄이 없습니다"
    from asciiart.config import setting_names
    names = setting_names(path)
    assert "COLS" in names and "ROWS" in names, "맨 앞 설정에 COLS, ROWS 가 없습니다"
    assert "import " not in head, "설정 블록 앞에 import 가 있습니다"


# 코드에 직접 써도 되는 숫자: 수학 상수(0, 1, 2, 0.5)뿐. 나머지는 맨 앞 설정 변수로.
ALLOWED_NUMBERS = {0, 1, 2, 0.5}


@pytest.mark.parametrize("path", PIECES, ids=ids(PIECES))
def test_no_magic_numbers(path):
    """맨 앞 설정만 바꾸면 아래 코드가 따라 바뀌어야 한다 (C 의 #define 처럼).

    '# ---------- 임시 도구' 구역(해시·노이즈 공식, 엔진으로 옮길 예정)은 검사하지 않는다.
    """
    src = open(path, encoding="utf-8").read()
    _, _, code = src.partition("# ===== 코드 =====")
    skip, inside = set(), False
    for i, line in enumerate(code.splitlines(), start=1):
        if line.startswith("# ---------- "):
            inside = line.startswith("# ---------- 임시 도구")
        if inside:
            skip.add(i)
    bad = []
    for node in ast.walk(ast.parse(code)):
        if (isinstance(node, ast.Constant) and type(node.value) in (int, float)
                and node.value not in ALLOWED_NUMBERS and node.lineno not in skip):
            bad.append("%d줄: %r" % (node.lineno + src.partition("# ===== 코드 =====")[0].count("\n"), node.value))
    assert not bad, "코드에 숫자가 직접 있습니다 (설정으로 옮기세요): " + ", ".join(sorted(set(bad)))


@pytest.mark.parametrize("path", PIECES, ids=ids(PIECES))
def test_no_nondeterministic_calls(path):
    src = open(path, encoding="utf-8").read()
    assert not re.search(r"^\s*import (random|time)\b|^\s*from (random|time) import", src, re.M)
    assert "np.random.rand(" not in src and "np.random.random(" not in src
    assert "datetime.now" not in src


@pytest.mark.parametrize("path", PIECES, ids=ids(PIECES))
def test_scene_is_deterministic_and_not_empty(path):
    g1, img1 = render_still(load(path))
    g2, img2 = render_still(load(path))
    assert g1.digest() == g2.digest()
    assert img1.tobytes() == img2.tobytes()
    assert g1.filled_ratio() > 0.01


@pytest.mark.parametrize("path", PIECES, ids=ids(PIECES))
def test_settings_change_result(path):
    ns = load(path)
    base = render_still(ns)[0].digest()
    ns2 = load(path)
    ns2["SEED"] = ns2["SEED"] + 1
    assert render_still(ns2)[0].digest() != base


@pytest.mark.parametrize("path", VERSIONS, ids=ids(VERSIONS))
def test_preview_matches_code(path, tmp_path):
    """저장된 미리보기는 그 버전 코드를 다시 실행한 결과와 픽셀까지 같아야 한다.

    ① 버전: preview.png (완성 화면).  ②·③ 버전: strip.png (strip.json 에 적힌 단계·프레임으로 다시 만든 프레임 띠).
    """
    import json
    from asciiart import export
    from asciiart.player import PieceRenderer
    folder = os.path.dirname(path)
    preview, strip, meta = (os.path.join(folder, n) for n in ("preview.png", "strip.png", "strip.json"))
    if not os.path.isfile(preview):                      # 최종본 폴더는 대표 그림 still.png (= 완성 화면)
        preview = os.path.join(folder, "still.png")
    assert os.path.isfile(preview) or os.path.isfile(strip), "미리보기 파일이 없습니다"
    if os.path.isfile(preview):
        _, img = render_still(load(path))
        saved = np.asarray(Image.open(preview).convert("RGB"))
        assert saved.shape == img.shape
        assert (saved == img).all()
    if os.path.isfile(strip):
        assert os.path.isfile(meta), "프레임 띠를 만든 단계·프레임 기록(strip.json)이 없습니다"
        info = json.load(open(meta, encoding="utf-8"))
        again = export.write_strip(PieceRenderer(load(path), part=info["part"]), str(tmp_path / "strip.png"), info["frames"])
        a = np.asarray(Image.open(strip).convert("RGB"))
        b = np.asarray(Image.open(again).convert("RGB"))
        assert a.shape == b.shape and (a == b).all(), "프레임 띠가 그 버전 코드로 다시 만든 것과 다릅니다"


GLOSSARIES = sorted(glob.glob(os.path.join(ROOT, "pieces", "*", "GLOSSARY.md")))


@pytest.mark.parametrize("path", GLOSSARIES, ids=ids(GLOSSARIES))
def test_glossary_names_unique(path):
    names = []
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^([^:#\-][^:]*?)\s*:\s", line)
        if m:
            names += [n.strip() for n in m.group(1).split(",")]
    dup = sorted({n for n in names if names.count(n) > 1})
    assert not dup, "용어집에 같은 이름이 두 번: %s" % dup


@pytest.mark.parametrize("path", GLOSSARIES, ids=ids(GLOSSARIES))
def test_glossary_covers_settings(path):
    piece = os.path.join(os.path.dirname(path), "piece.py")
    head = open(piece, encoding="utf-8").read().partition("# ===== 코드 =====")[0]
    settings = set()
    for line in head.splitlines():
        m = re.match(r"^([A-Z_][A-Z0-9_, ]*)=", line)
        if m:
            settings |= {s.strip() for s in m.group(1).split(",") if s.strip()}
    settings.discard("RANGES")          # 범위 표는 조절하는 값이 아님 (엔진 setting_names 와 같은 기준)
    text = open(path, encoding="utf-8").read()
    missing = sorted(s for s in settings if not re.search(r"^%s\s*:" % re.escape(s), text, re.M))
    assert not missing, "용어집에 없는 설정: %s" % missing


@pytest.mark.parametrize("path", PIECES, ids=ids(PIECES))
def test_stage_links_for_staged_pieces(path):
    """단계 작품이면 ① 완성 화면 = ② 등장 끝 = ③ 모션 처음 = ③ 모션 끝."""
    from asciiart.stages import link_report
    rep = link_report(load(path))
    bad = [(name, diff) for name, same, diff in rep if not same]
    assert not bad, "단계 사이가 튐: %s" % bad


@pytest.mark.parametrize("path", PIECES, ids=ids(PIECES))
def test_brief_has_progress(path):
    brief = os.path.join(os.path.dirname(path), "brief.md")
    assert os.path.isfile(brief), "brief.md 가 없습니다"
    assert "## 진행 상태" in open(brief, encoding="utf-8").read()
