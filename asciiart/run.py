"""작품 실행기. 작품 파일 맨 끝의 `run(globals())` 가 이것을 부른다.

    python piece.py                           창에서 재생 (정지 그림만 있는 작품은 그림을 띄움)
    python piece.py --stage 1                 ① 정지 그림 PNG 저장 (out/stage1.png)
    python piece.py --stage 1 --version s1_v2 그 PNG 와 지금 코드를 versions/s1_v2/ 에 같이 저장
    python piece.py --set MOON_X=0.4          설정 값을 파일 수정 없이 바꿔서 실행
    python piece.py --seconds 5               5초 뒤 창 자동 종료 (확인용)
    python piece.py --player opencv           재생 창 종류 고르기 (기본 auto: pygame 있으면 pygame)

저장 (모두 프레임을 하나도 빠뜨리지 않는 정확한 그림, 기본 위치: 작품 폴더/out/)
    python piece.py --mp4                     MP4 (루프 작품은 --loops N 번 이어 붙임, 기본 1)
    python piece.py --mp4 --loops 3
    python piece.py --gif                     GIF (한 루프, 크기 절반, 초당 10장)
    python piece.py --strip                   프레임 띠 (한 루프에서 고르게 6장, --strip-count 로 장수)
    python piece.py --png 45                  45번 프레임 PNG
    python piece.py --mp4 --strip --version s3_v1   결과물과 지금 코드를 versions/s3_v1/ 에 함께 저장

단계 작품 (scene · intro · motion 이 있는 작품)
    python piece.py --stage 1                 ① 완성 화면 PNG
    python piece.py --stage 2                 ② 등장 MP4 (끝에 완성 화면 INTRO_HOLD 초) + 프레임 띠
    python piece.py --stage 3                 ③ 모션 MP4 (--loops, 기본 2) + 프레임 띠
    python piece.py --final                   최종: 등장 1번 + 모션 FINAL_LOOPS 번 MP4 + 대표 PNG
    python piece.py --check                   단계 연결 검사만 (① = ② 끝 = ③ 처음 = ③ 끝)
"""
import argparse
import json
import os
import shutil

from . import export
from .atlas import save_png
from .config import apply_set, check, setting_names
from .player import PieceRenderer, play
from .stages import print_report


def render_still(ns):
    """① 완성 화면 (단계 작품은 scene, frame 작품은 0번 프레임). 테스트와 미리보기가 같은 함수를 쓴다.

    글로우가 있으면 글로우까지 그린 그림이다.
    """
    r = PieceRenderer(ns, part="scene")
    img = r.image_at(0)
    r.grid_at(0)
    return r.grid, img


def _piece_file(ns):
    path = ns.get("__file__")
    if not path:
        raise SystemExit("작품 파일 경로를 알 수 없습니다")
    return os.path.abspath(path)


# 버전 폴더 안에서 쓰는 이름 (결과물 종류 → 파일 이름)
VERSION_NAMES = {"stage1": "preview.png", "png": "frame.png", "mp4": "preview.mp4", "gif": "preview.gif",
                 "strip": "strip.png", "stage2": "preview.mp4", "stage2_strip": "strip.png",
                 "stage3": "preview.mp4", "stage3_strip": "strip.png", "final": "final.mp4", "still": "still.png"}


STRIP_META = "strip.json"      # 프레임 띠를 어떤 단계·프레임으로 만들었는지 (테스트가 같은 띠를 다시 만들어 비교)


def save_version(ns, name, outputs, strip_meta=None):
    """지금 코드와 이번에 만든 결과물을 versions/<name>/ 에 저장한다 (버전은 코드로 남긴다).

    outputs: {"stage1": 경로, "mp4": 경로, ...}
    strip_meta: {"part": "intro"|"motion"|"all", "frames": [...]} — 프레임 띠가 있을 때
    """
    piece = _piece_file(ns)
    folder = os.path.dirname(piece)
    if os.path.basename(os.path.dirname(folder)) == "versions":
        raise SystemExit("versions 안의 코드로는 새 버전을 만들지 않습니다")
    dest = os.path.join(folder, "versions", name)
    if os.path.exists(dest):
        raise SystemExit("이미 있는 버전입니다: %s (덮어쓰지 않습니다)" % dest)
    os.makedirs(dest)
    shutil.copy2(piece, os.path.join(dest, "piece.py"))
    for kind, path in outputs.items():
        shutil.copy2(path, os.path.join(dest, VERSION_NAMES[kind]))
    if strip_meta:
        with open(os.path.join(dest, STRIP_META), "w", encoding="utf-8") as f:
            json.dump(strip_meta, f)
    return dest


def _report_video(label, path):
    info = export.probe(path)
    print("%s 저장: %s  (%dx%d, %d프레임, %.2f초, %gfps)"
          % (label, path, info["width"], info["height"], info["frames"], info["duration"], info["fps"]))


def prepare(ns, set_pairs=None, log=print):
    """설정 모으기 → --set 적용 → 범위 검사. 바꾼 설정 이름 목록을 돌려준다."""
    names = setting_names(_piece_file(ns))
    changed = apply_set(ns, set_pairs, names)
    if changed:
        log("설정 변경: " + ", ".join("%s=%r" % (k, ns[k]) for k in changed))
    for w in check(ns, names):
        log("설정 보정: " + w)
    return changed


def run(ns, argv=None):
    doc = (ns.get("__doc__") or "").strip().splitlines()
    ap = argparse.ArgumentParser(description=doc[0] if doc else None)
    ap.add_argument("--stage", type=int, choices=[1, 2, 3])
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--out", help="저장 경로 (기본: 작품 폴더/out/)")
    ap.add_argument("--version", help="versions/<이름>/ 에 코드와 미리보기를 함께 저장")
    ap.add_argument("--set", action="append", metavar="KEY=VALUE", help="설정 값을 바꿔서 실행 (여러 번 가능)")
    ap.add_argument("--seconds", type=float, help="창 재생을 이 시간 뒤에 자동으로 닫음 (확인용)")
    ap.add_argument("--player", choices=["auto", "pygame", "opencv"], default="auto",
                    help="재생 창 종류 (기본: pygame 이 있으면 pygame)")
    ap.add_argument("--mp4", nargs="?", const="", metavar="PATH", help="MP4 저장 (경로 생략 시 out/<이름>.mp4)")
    ap.add_argument("--loops", type=int, help="MP4 에 루프를 몇 번 이어 붙일지 (기본: --mp4 1, --stage 3 2, --final FINAL_LOOPS)")
    ap.add_argument("--check", action="store_true", help="단계 연결 검사만 하고 끝냄")
    ap.add_argument("--gif", nargs="?", const="", metavar="PATH", help="GIF 저장")
    ap.add_argument("--strip", nargs="?", const="", metavar="PATH", help="프레임 띠 PNG 저장")
    ap.add_argument("--strip-count", type=int, default=6, help="프레임 띠 장수")
    ap.add_argument("--png", type=int, metavar="FRAME", help="이 번호 프레임을 PNG 로 저장")
    a = ap.parse_args(argv)

    changed = prepare(ns, a.set)
    if changed and a.version:
        raise SystemExit("--set 으로 바꾼 값은 파일에 없어서 버전으로 저장하지 않습니다. 파일을 고친 뒤 저장하세요.")
    staged = PieceRenderer(ns).kind == "staged" if (a.final or a.stage in (2, 3) or a.check) else False
    if (a.final or a.stage in (2, 3)) and not staged:
        raise SystemExit("--stage 2/3, --final 은 scene · intro · motion 으로 나뉜 작품에서 씁니다")
    if a.check:
        ok = print_report(ns)
        raise SystemExit(0 if ok else 1)

    folder = os.path.dirname(_piece_file(ns))
    name = os.path.basename(folder) if os.path.basename(_piece_file(ns)) == "piece.py" \
        else os.path.splitext(os.path.basename(_piece_file(ns)))[0]
    out_dir = os.path.join(folder, "out")
    outputs = {}
    strip_meta = None

    if a.stage == 1:
        grid, img = render_still(ns)
        out = a.out or os.path.join(out_dir, "stage1.png")
        save_png(img, out)
        print("① 정지 그림 저장: %s  (%dx%d px, %dx%d 칸, 글자 %.0f%%)"
              % (out, img.shape[1], img.shape[0], grid.cols, grid.rows, grid.filled_ratio() * 100))
        outputs["stage1"] = out

    if a.stage in (2, 3) or a.final:
        link_ok = print_report(ns)
        if not link_ok:
            print("주의: 단계 사이가 튈 수 있습니다 (위 ✗ 항목). 그래도 저장은 합니다.")
        try:
            if a.stage == 2:
                r = PieceRenderer(ns, part="intro")
                path = export.write_mp4(r, os.path.join(out_dir, "stage2.mp4"))
                outputs["stage2"] = path
                frames = export.strip_frames(r, a.strip_count)
                outputs["stage2_strip"] = export.write_strip(r, os.path.join(out_dir, "stage2_strip.png"), frames)
                strip_meta = {"part": "intro", "frames": frames}
                _report_video("② 등장", path)
            if a.stage == 3:
                r = PieceRenderer(ns, part="motion")
                path = export.write_mp4(r, os.path.join(out_dir, "stage3.mp4"), loops=a.loops or 2)
                outputs["stage3"] = path
                frames = export.strip_frames(r, a.strip_count)
                outputs["stage3_strip"] = export.write_strip(r, os.path.join(out_dir, "stage3_strip.png"), frames)
                strip_meta = {"part": "motion", "frames": frames}
                _report_video("③ 모션", path)
            if a.final:
                r = PieceRenderer(ns, part="all")
                path = export.write_mp4(r, os.path.join(out_dir, "final.mp4"),
                                        loops=a.loops or ns.get("FINAL_LOOPS", 1))
                outputs["final"] = path
                _report_video("최종본", path)
                grid, img = render_still(ns)
                outputs["still"] = save_png(img, os.path.join(out_dir, "still.png"))
                print("대표 그림 저장: %s" % outputs["still"])
        except KeyboardInterrupt:
            raise SystemExit("저장을 취소했습니다 (만들던 파일은 지웠습니다)")
        except export.ExportError as e:
            raise SystemExit(str(e))
        for k in ("stage2_strip", "stage3_strip"):
            if k in outputs:
                print("프레임 띠 저장: %s" % outputs[k])

    wants_export = any(x is not None for x in (a.mp4, a.gif, a.strip, a.png))
    if wants_export:
        r = PieceRenderer(ns)
        try:
            if a.png is not None:
                path = export.write_png(r, os.path.join(out_dir, "%s_f%04d.png" % (name, a.png)), a.png)
                print("PNG 저장: %s" % path)
                outputs["png"] = path
            if a.strip is not None:
                frames = export.strip_frames(r, a.strip_count)
                path = export.write_strip(r, a.strip or os.path.join(out_dir, name + "_strip.png"), frames)
                strip_meta = {"part": "all", "frames": frames}
                print("프레임 띠 저장: %s" % path)
                outputs["strip"] = path
            if a.gif is not None:
                path = export.write_gif(r, a.gif or os.path.join(out_dir, name + ".gif"))
                step, delay = export.gif_timing(r.fps)
                print("GIF 저장: %s  (%d장, 한 장 %dms)" % (path, len(range(0, r.n, step)), delay))
                outputs["gif"] = path
            if a.mp4 is not None:
                path = export.write_mp4(r, a.mp4 or os.path.join(out_dir, name + ".mp4"), loops=a.loops or 1)
                info = export.probe(path)
                print("MP4 저장: %s  (%dx%d, %d프레임, %.2f초, %gfps)"
                      % (path, info["width"], info["height"], info["frames"], info["duration"], info["fps"]))
                outputs["mp4"] = path
        except KeyboardInterrupt:
            raise SystemExit("저장을 취소했습니다 (만들던 파일은 지웠습니다)")
        except export.ExportError as e:
            raise SystemExit(str(e))

    if outputs:
        if a.version:
            print("버전 저장:", save_version(ns, a.version, outputs, strip_meta))
        return outputs
    if a.version:
        raise SystemExit("--version 은 저장할 결과물(--stage 1/2/3, --final, --mp4, --gif, --strip, --png)과 함께 써 주세요")

    return play(PieceRenderer(ns), name, a.out or out_dir, max_seconds=a.seconds, backend=a.player)
