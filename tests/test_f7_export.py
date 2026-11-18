"""F7: 저장 (MP4 · GIF · 프레임 띠 · PNG) 과 버전 저장."""
import importlib.util
import os
import shutil

import numpy as np
import pytest
from PIL import Image

from asciiart import export
from asciiart.player import PieceRenderer
from asciiart.run import run

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F6 = os.path.join(ROOT, "examples", "f6_demo.py")
F3 = os.path.join(ROOT, "examples", "f3_demo.py")
SMALL = dict(COLS=40, ROWS=20, FONT_PX=8, LOOP_SECONDS=1, STAR_COUNT=20, METEORS=2, METEOR_GAP=0.1,
             T_IN=0.05, T_IN_D=0.2, T_OUT=0.6, T_OUT_D=0.2)


def load(path, **over):
    spec = importlib.util.spec_from_file_location("m_" + os.path.basename(path).replace(".", "_"), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    ns = vars(m)
    ns.update(over)
    return ns


def quiet(*_):
    pass


def decode(path):
    import cv2
    cap = cv2.VideoCapture(path)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f[..., ::-1])
    cap.release()
    return frames


def psnr(a, b):
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    return 99.0 if mse == 0 else 10 * np.log10(255.0 ** 2 / mse)


# ---------- MP4 ----------
def test_mp4_frames_duration_size(tmp_path):
    r = PieceRenderer(load(F6, **SMALL))
    path = export.write_mp4(r, str(tmp_path / "a.mp4"), loops=3, progress=quiet)
    info = export.probe(path)
    img = r.image_at(0)
    assert info["frames"] == 3 * r.n                         # 끝 프레임 중복 없이 정확히 3 루프
    assert abs(info["duration"] - 3 * r.n / r.fps) < 1e-3
    assert (info["width"], info["height"]) == (img.shape[1], img.shape[0])
    assert info["fps"] == r.fps


def test_mp4_frames_match_code_render(tmp_path):
    """영상 속 프레임 = 같은 번호로 코드에서 렌더한 그림 (압축 오차 안)."""
    ns = load(F6, **SMALL)
    path = export.write_mp4(PieceRenderer(ns), str(tmp_path / "b.mp4"), loops=2, progress=quiet)
    video = decode(path)
    ref = PieceRenderer(load(F6, **SMALL))
    n = ref.n
    for i in (0, 5, n - 1, n, n + 5):
        assert psnr(video[i], ref.image_at(i % n)) > 30, i
    # 루프 이음매: 넣은 그림은 픽셀까지 같다 (F6 테스트). 영상에서는 0번이 기준 프레임(I), 2번째 루프의
    # 처음은 차이 프레임(P)이라 압축 오차만 조금 다르다 → 서로 35dB 이상이면 눈으로 구분되지 않는다.
    assert psnr(video[n], video[0]) > 35


def test_mp4_odd_size_is_padded(tmp_path):
    ns = load(F3, COLS=21, ROWS=11, FONT_PX=7, LOOP_SECONDS=0.5)   # 홀수 크기가 되는 설정
    r = PieceRenderer(ns)
    h, w = r.image_at(0).shape[:2]
    path = export.write_mp4(r, str(tmp_path / "odd.mp4"), progress=quiet)
    info = export.probe(path)
    assert info["width"] == w + w % 2 and info["height"] == h + h % 2 and info["frames"] == r.n


def test_mp4_cancel_removes_partial_file(tmp_path):
    r = PieceRenderer(load(F6, **SMALL))
    path = str(tmp_path / "c.mp4")

    def stop(done, total, label):
        if done == 5:
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        export.write_mp4(r, path, loops=2, progress=stop)
    assert not os.path.exists(path) and not os.path.exists(path + ".part.mp4")


def test_missing_ffmpeg_gives_clear_error(monkeypatch, tmp_path):
    monkeypatch.setenv("ASCIIART_FFMPEG", str(tmp_path / "nope" / "ffmpeg"))
    r = PieceRenderer(load(F6, **SMALL))
    with pytest.raises(FileNotFoundError):
        export.write_mp4(r, str(tmp_path / "d.mp4"), progress=quiet)
    monkeypatch.delenv("ASCIIART_FFMPEG")
    monkeypatch.setattr(export.shutil, "which", lambda *_: None)
    monkeypatch.setattr(export.sys, "executable", str(tmp_path / "python"))
    with pytest.raises(export.ExportError) as e:
        export.find_tool("ffmpeg")
    assert "ffmpeg" in str(e.value)


def test_ffmpeg_found_next_to_python_without_activate(monkeypatch):
    """conda activate 없이 환경의 python 경로로 실행해도 같은 폴더의 ffmpeg 를 찾는다."""
    monkeypatch.setattr(export.shutil, "which", lambda *_: None)
    monkeypatch.delenv("ASCIIART_FFMPEG", raising=False)
    assert os.path.dirname(export.find_tool("ffmpeg")) == os.path.dirname(export.sys.executable)


# ---------- GIF · 프레임 띠 · PNG ----------
def test_gif_timing_is_gif_friendly():
    assert export.gif_timing(30, 10) == (3, 100)
    assert export.gif_timing(24, 12) == (2, 80)
    assert export.gif_timing(60, 25) == (2, 30)


def test_gif_frames_and_size(tmp_path):
    r = PieceRenderer(load(F6, **SMALL))
    path = export.write_gif(r, str(tmp_path / "a.gif"), progress=quiet)
    im = Image.open(path)
    step, delay = export.gif_timing(r.fps)
    assert im.n_frames == len(range(0, r.n, step))
    assert im.info["duration"] == delay and im.info.get("loop") == 0
    w, h = r.image_at(0).shape[1], r.image_at(0).shape[0]
    assert im.size == (int(w * export.GIF_SCALE), int(h * export.GIF_SCALE))


def test_strip_layout_and_frames(tmp_path):
    r = PieceRenderer(load(F6, **SMALL))
    frames = export.strip_frames(r, 6)
    assert len(frames) == 6 and frames[0] == 0 and frames == sorted(frames)
    path = export.write_strip(r, str(tmp_path / "s.png"), frames, columns=3, scale=0.5)
    im = Image.open(path)
    h, w = r.image_at(0).shape[:2]
    assert im.size == (3 * int(w * 0.5) + 2 * export.STRIP_GAP, 2 * int(h * 0.5) + export.STRIP_GAP)


def test_png_frame_is_exact(tmp_path):
    r = PieceRenderer(load(F6, **SMALL))
    path = export.write_png(r, str(tmp_path / "f.png"), 7)
    saved = np.asarray(Image.open(path).convert("RGB"))
    assert (saved == PieceRenderer(load(F6, **SMALL)).image_at(7)).all()


# ---------- 명령줄 · 버전 저장 ----------
@pytest.fixture
def piece_copy(tmp_path):
    """작품 파일을 임시 작품 폴더로 복사 (pieces/<slug>/piece.py 구조)."""
    folder = tmp_path / "pieces" / "demo"
    folder.mkdir(parents=True)
    dst = folder / "piece.py"
    src = open(F3, encoding="utf-8").read().replace(
        "sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))",
        "sys.path.insert(0, %r)" % ROOT)
    for k, v in (("COLS, ROWS   = 96, 40", "COLS, ROWS   = 40, 16"), ("LOOP_SECONDS = 4 ", "LOOP_SECONDS = 1 ")):
        assert k in src
        src = src.replace(k, v)
    dst.write_text(src, encoding="utf-8")
    return str(dst)


def test_cli_exports_and_version(piece_copy):
    ns = load(piece_copy)
    outputs = run(ns, ["--mp4", "--loops", "2", "--strip", "--gif", "--png", "3", "--version", "s3_v1"])
    folder = os.path.dirname(piece_copy)
    v = os.path.join(folder, "versions", "s3_v1")
    for name in ("piece.py", "preview.mp4", "strip.png", "preview.gif", "frame.png"):
        assert os.path.isfile(os.path.join(v, name)), name
    assert export.probe(os.path.join(v, "preview.mp4"))["frames"] == 2 * PieceRenderer(load(piece_copy)).n
    assert set(outputs) == {"mp4", "strip", "gif", "png"}
    with pytest.raises(SystemExit):                          # 같은 버전 이름은 덮어쓰지 않는다
        run(load(piece_copy), ["--png", "0", "--version", "s3_v1"])


def test_cli_version_needs_output(piece_copy):
    with pytest.raises(SystemExit):
        run(load(piece_copy), ["--version", "x"])


def test_cli_set_not_allowed_with_version(piece_copy):
    with pytest.raises(SystemExit):
        run(load(piece_copy), ["--mp4", "--set", "WAVES=3", "--version", "x"])
