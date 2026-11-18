"""F9: /ascii 스킬 (SKILL.md · reference.md · template.py) 과 도구 (new_piece · glossary)."""
import importlib
import importlib.util
import os
import re

import pytest

import test_pieces as P
from asciiart.run import render_still
from asciiart.stages import link_report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, ".claude", "skills", "ascii")


def read(*parts):
    return open(os.path.join(*parts), encoding="utf-8").read()


# ---------- 스킬 파일 ----------
def test_skill_frontmatter():
    text = read(SKILL, "SKILL.md")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "frontmatter 가 없습니다"
    front = m.group(1)
    assert re.search(r"^name: ascii$", front, re.M)
    assert re.search(r"^description: .+", front, re.M) and re.search(r"^argument-hint: .+", front, re.M)
    assert "$ARGUMENTS" in text


def test_skill_points_to_real_files():
    text = read(SKILL, "SKILL.md")
    for rel in ("reference.md", "template.py"):
        assert rel in text and os.path.isfile(os.path.join(SKILL, rel)), rel
    for tool in ("tools/new_piece.py", "tools/glossary.py", "tools/image_to_field.py"):
        assert tool in text and os.path.isfile(os.path.join(ROOT, tool)), tool
    assert "docs/PLAN.md" in text and os.path.isfile(os.path.join(ROOT, "docs", "PLAN.md"))
    assert not os.path.exists(os.path.join(SKILL, "template.ts"))             # 예전 TypeScript 템플릿은 없앰


def test_skill_keeps_the_agreed_rules():
    """사용자와 정한 규칙이 스킬 본문에 들어 있다."""
    text = read(SKILL, "SKILL.md")
    for must in ("① 정지 그림", "② 등장", "③ 모션", "최종본", "AskUserQuestion", "최대 4개", "(추천)",
                 "고정된 목록이 아니다", "참고", "--version", "versions/", "한국어", "conda activate min",
                 "직접 보지 않은 것", "3D", "알아서"):
        assert must in text, must


def test_reference_names_exist_in_engine():
    """참고서의 함수 이름이 엔진에 실제로 있다 (이름이 바뀌면 여기서 걸림)."""
    text = read(SKILL, "reference.md")
    modules = {m: importlib.import_module("asciiart." + m) for m in
               ("grid", "ramp", "color", "shade", "post", "ease", "noise", "schedule", "field", "three")}
    names = set(re.findall(r"`([a-z_][a-z0-9_]*)\(", text)) | set(re.findall(r"[\s(,`]([a-z_][a-z0-9_]{3,})\(", text))
    import builtins
    names -= {"draw", "scene", "intro", "motion", "setup", "fn", "run", "sin", "loop", "rgb"} | set(dir(builtins))
    missing = sorted(n for n in names if not any(hasattr(m, n) for m in modules.values())
                     and not any(hasattr(getattr(m, c), n) for m in modules.values() for c in dir(m)
                                 if isinstance(getattr(m, c), type)))
    assert not missing, "참고서에만 있는 이름: %s" % missing


# ---------- 템플릿으로 새 작품 ----------
@pytest.fixture
def new_piece(tmp_path):
    from tools.new_piece import main
    code = main(["test-orb", "--title", "시험 구", "--request", "빛나는 공 \"하나\"", "--root", str(tmp_path)])
    assert code == 0
    return os.path.join(str(tmp_path), "test-orb", "piece.py")


def test_new_piece_passes_all_piece_rules(new_piece):
    P.test_settings_block_first(new_piece)
    P.test_no_magic_numbers(new_piece)
    P.test_no_nondeterministic_calls(new_piece)
    P.test_scene_is_deterministic_and_not_empty(new_piece)
    P.test_settings_change_result(new_piece)
    P.test_stage_links_for_staged_pieces(new_piece)
    P.test_brief_has_progress(new_piece)
    glossary = os.path.join(os.path.dirname(new_piece), "GLOSSARY.md")
    P.test_glossary_names_unique(glossary)
    P.test_glossary_covers_settings(glossary)


def test_new_piece_fills_placeholders(new_piece):
    src = read(new_piece)
    assert "<제목>" not in src and "시험 구" in src and "빛나는 공 'ㅎ" not in src
    assert "<사용자 원문>" not in src
    brief = read(os.path.dirname(new_piece), "brief.md")
    assert "빛나는 공 \"하나\"" in brief and "## 참고한 모습" in brief


def test_new_piece_renders_still(new_piece):
    grid, img = render_still(P.load(new_piece))
    assert img.shape == (60 * 16, 120 * 10, 3) and grid.filled_ratio() > 0.05


def test_new_piece_refuses_existing_and_bad_slug(new_piece, tmp_path):
    from tools.new_piece import main
    assert main(["test-orb", "--title", "x", "--request", "y", "--root", str(tmp_path)]) == 1
    assert main(["Bad_Slug", "--title", "x", "--request", "y", "--root", str(tmp_path)]) == 2


def test_glossary_update_keeps_handwritten_sections(new_piece):
    from tools.glossary import update
    folder = os.path.dirname(new_piece)
    path = os.path.join(folder, "GLOSSARY.md")
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n--- 장면 변수 ---\norder : 칸마다 드러나는 순서 : 0~1\n")
    src = read(new_piece).replace("# 주제 크기, 화면 높이 절반 = 1 (0.05~3)", "# 공 크기 (0.1~2)")
    open(new_piece, "w", encoding="utf-8").write(src)
    update(new_piece)
    g = read(path)
    assert "order : 칸마다 드러나는 순서 : 0~1" in g                    # 손으로 쓴 절은 그대로
    assert "SUBJECT_R : 공 크기 : 0.1~2" in g                           # 자동 절은 새 주석으로
    assert g.count("<!-- auto settings -->") == 1


def test_template_itself_runs():
    path = os.path.join(SKILL, "template.py")
    spec = importlib.util.spec_from_file_location("tmpl", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert all(same for _, same, _ in link_report(vars(m)))
