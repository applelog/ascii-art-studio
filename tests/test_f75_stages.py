"""F7.5: 단계 구조 (① scene · ② intro · ③ motion) — 시간축, 연결 검사, 단계별 출력."""
import importlib.util
import os

import pytest

from asciiart import export
from asciiart.player import PieceRenderer, Playback
from asciiart.run import run
from asciiart.stages import link_report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROOT, "examples", "f75_demo.py")
F6 = os.path.join(ROOT, "examples", "f6_demo.py")
SMALL = dict(COLS=48, ROWS=24, FONT_PX=8, SUPERSAMPLE=1, INTRO_SECONDS=0.5, INTRO_HOLD=0.2,
             LOOP_SECONDS=1, STAR_COUNT=20, FINAL_LOOPS=2)


def load(path=DEMO, **over):
    spec = importlib.util.spec_from_file_location("m_" + os.path.basename(path).replace(".", "_"), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    ns = vars(m)
    ns.update(over)
    return ns


def quiet(*_):
    pass


# ---------- 연결 검사 ----------
def test_demo_links_are_equal():
    rep = link_report(load(**SMALL))
    assert [name for name, _, _ in rep] == ["② 등장 끝 (p=1)", "③ 모션 처음 (phase=0)", "③ 모션 끝 (phase=1)"]
    assert all(same for _, same, _ in rep)


def test_link_check_catches_a_jump():
    ns = load(**SMALL)
    draw = ns["draw"]
    ns["motion"] = lambda s, t, phase, g: draw(s, phase + 0.1, g)     # 모션이 완성 화면에서 시작하지 않음
    rep = dict((n, (same, diff)) for n, same, diff in link_report(ns))
    assert not rep["③ 모션 처음 (phase=0)"][0] and rep["③ 모션 처음 (phase=0)"][1] > 0
    assert rep["② 등장 끝 (p=1)"][0]


def test_non_staged_piece_has_no_links():
    assert link_report(load(F6)) == []


# ---------- 시간축 ----------
def test_timeline_all_intro_then_motion_laps():
    r = PieceRenderer(load(**SMALL))
    ni, nm = r.n_intro, r.n_motion
    assert (ni, nm) == (15, 30) and r.n == ni + nm and r.loop_start == ni and not r.cyclic
    assert r.locate(0) == ("intro", 0, ni)
    assert r.locate(ni - 1) == ("intro", ni - 1, ni)
    assert r.locate(ni) == ("motion", 0, nm)
    assert r.locate(ni + nm) == ("motion", 0, nm)            # 두 번째 바퀴
    assert r.locate(ni + nm + 5) == ("motion", 5, nm)
    assert r.describe(ni + 2) == "③ 모션 3/30"


def test_timeline_parts():
    ns = load(**SMALL)
    intro = PieceRenderer(ns, part="intro")
    assert intro.n == 15 + 6 and not intro.loop                # 등장 + 완성 화면 0.2초
    assert intro.locate(14)[0] == "intro" and intro.locate(15) == ("scene", 0, 1)
    motion = PieceRenderer(ns, part="motion")
    assert motion.cyclic and motion.n == 30 and motion.locate(31) == ("motion", 1, 30)
    still = PieceRenderer(ns, part="scene")
    assert still.n == 1 and still.locate(99) == ("scene", 0, 1)


def test_video_frame_counts():
    ns = load(**SMALL)
    assert len(PieceRenderer(ns).video_frames(2)) == 15 + 2 * 30
    assert len(PieceRenderer(ns, part="intro").video_frames(5)) == 21        # 등장은 반복 없음
    assert len(PieceRenderer(ns, part="motion").video_frames(3)) == 90


def test_intro_end_flows_into_motion_and_motion_laps_join():
    """등장 마지막 다음 = 모션 처음 = 완성 화면, 모션 끝 다음 = 모션 처음 (그림 기준)."""
    r = PieceRenderer(load(**SMALL))
    ni, nm = r.n_intro, r.n_motion
    scene = PieceRenderer(load(**SMALL), part="scene").grid_at(0).digest()
    assert r.grid_at(ni).digest() == scene
    assert r.grid_at(ni + nm).digest() == scene
    assert r.grid_at(0).digest() != scene                     # 등장 처음은 비어 있음


@pytest.mark.parametrize("k", [3, 14, 15, 16, 44, 45, 50])
def test_seek_equals_sequential_across_stage_boundary(k):
    """잔상이 있어도, 등장→모션 경계와 두 번째 바퀴에서 건너뛴 그림 = 연속 재생 그림."""
    seq = PieceRenderer(load(**SMALL))
    for i in range(k + 1):
        img = seq.image_at(i)
    jump = PieceRenderer(load(**SMALL)).image_at(k)
    assert (jump == img).all()


# ---------- 창 재생 ----------
def test_playback_runs_intro_once_then_loops_motion():
    r = PieceRenderer(load(**SMALL))

    class Clock:
        t = 0.0

        def __call__(self):
            return self.t

    c = Clock()
    pb = Playback(r.n, r.fps, r.loop, c, cyclic=r.cyclic)
    c.t = 0.3
    assert r.locate(pb.update())[0] == "intro"
    c.t = 0.5 + 1.0 + 0.1                                     # 등장 0.5초 + 모션 한 바퀴 + 0.1초
    stage, i, _ = r.locate(pb.update())
    assert stage == "motion" and i == 3
    pb.restart()
    assert r.locate(pb.update())[0] == "intro"                # R: 등장부터 다시
    pb.step(-1)
    assert pb.frame == 0                                      # 0 앞으로는 가지 않음


# ---------- 명령줄 ----------
@pytest.fixture
def staged_piece(tmp_path):
    folder = tmp_path / "pieces" / "planet"
    folder.mkdir(parents=True)
    src = open(DEMO, encoding="utf-8").read().replace(
        "sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))",
        "sys.path.insert(0, %r)" % ROOT)
    small = "".join("%s = %r\n" % (k, v) for k, v in SMALL.items() if k not in ("COLS", "ROWS"))
    small += "COLS, ROWS = %d, %d\n" % (SMALL["COLS"], SMALL["ROWS"])
    src = src.replace("# ===== 코드 =====", small + "# ===== 코드 =====", 1)
    path = folder / "piece.py"
    path.write_text(src, encoding="utf-8")
    return str(path)


def test_cli_stage_outputs(staged_piece, capsys):
    out = os.path.join(os.path.dirname(staged_piece), "out")
    run(load(staged_piece), ["--stage", "2"])
    assert export.probe(os.path.join(out, "stage2.mp4"))["frames"] == 21
    assert os.path.isfile(os.path.join(out, "stage2_strip.png"))
    run(load(staged_piece), ["--stage", "3"])
    assert export.probe(os.path.join(out, "stage3.mp4"))["frames"] == 60      # 기본 2 바퀴
    run(load(staged_piece), ["--final"])
    info = export.probe(os.path.join(out, "final.mp4"))
    assert info["frames"] == 15 + 2 * 30 and abs(info["duration"] - (0.5 + 2 * 1.0)) < 1e-3
    assert os.path.isfile(os.path.join(out, "still.png"))
    assert "모두 같음" in capsys.readouterr().out


def test_cli_stage_version_saves_code_and_previews(staged_piece):
    run(load(staged_piece), ["--stage", "2", "--version", "s2_v1"])
    v = os.path.join(os.path.dirname(staged_piece), "versions", "s2_v1")
    assert sorted(os.listdir(v)) == ["piece.py", "preview.mp4", "strip.json", "strip.png"]
    import json
    meta = json.load(open(os.path.join(v, "strip.json"), encoding="utf-8"))
    assert meta["part"] == "intro" and meta["frames"] and all(isinstance(f, int) for f in meta["frames"])


def test_cli_check_exit_codes(staged_piece):
    with pytest.raises(SystemExit) as e:
        run(load(staged_piece), ["--check"])
    assert e.value.code == 0


def test_cli_stage2_needs_staged_piece():
    with pytest.raises(SystemExit):
        run(load(F6), ["--stage", "2"])


# ---------- 글자 버퍼 캐시 · 미리 계산 ----------
def test_cached_grid_equals_fresh_and_prefetch_thread():
    import threading
    from asciiart.grid import Grid

    ns = load(**SMALL)
    r = PieceRenderer(ns)
    fresh = PieceRenderer(load(**SMALL))
    scratch = Grid(ns["COLS"], ns["ROWS"])
    t = threading.Thread(target=lambda: [r.prefetch(k, scratch) for k in range(20, 40)])
    t.start()
    t.join()
    assert all(r.cached(k) for k in range(20, 40))
    for k in (20, 25, 39):
        assert r.grid_at(k).digest() == fresh.grid_at(k).digest()
    assert r.cache_hits == 3
    # 모션 두 번째 바퀴는 첫 바퀴 캐시를 쓴다
    assert r.cached(r.n_intro + r.n_motion + 5) == r.cached(r.n_intro + 5)


def test_cache_respects_limit(monkeypatch):
    import asciiart.player as P

    monkeypatch.setattr(P, "CACHE_LIMIT_MB", 0)
    r = PieceRenderer(load(**SMALL))
    r.grid_at(3)
    assert not r.cached(3) and r._cache_bytes == 0          # 상한을 넘으면 저장하지 않고 계산만
    assert r.grid_at(3).digest() == PieceRenderer(load(**SMALL)).grid_at(3).digest()


def test_images_identical_with_and_without_cache():
    a = PieceRenderer(load(**SMALL))
    for k in range(0, 60):
        a.grid_at(k)                                         # 캐시 채우기
    a2 = PieceRenderer(load(**SMALL))
    a2._cache, a2._cache_bytes = a._cache, a._cache_bytes   # 채운 캐시를 쓰는 렌더러
    b = PieceRenderer(load(**SMALL))                         # 캐시 없이 계산
    for k in (0, 14, 15, 44, 59):
        assert (a2.image_at(k) == b.image_at(k)).all()
