"""이미지 → ASCII 작품용 필드 JSON (asciiart.field.make_field 를 부르는 명령).

    python tools/image_to_field.py <이미지> --out pieces/<slug>/field.json --cols 160 --cell-aspect 0.6
    python tools/image_to_field.py <이미지> --out ... --cols 120 --ss 2      칸보다 2배 촘촘 (흔들기·확대용)

담기는 것: 밝기 · 피사체 마스크(alpha) · 윤곽 세기·방향 · 원래 색 · 대표 색 팔레트.
원본 이미지는 저장하지 않는다. 줄인 값만 남는다.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from asciiart.field import FieldError, make_field, save_field  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("image")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cols", type=int, default=160)
    ap.add_argument("--rows", type=int, default=0, help="0 이면 이미지 비율과 칸 비율로 계산")
    ap.add_argument("--cell-aspect", type=float, default=0.6, help="칸 너비/높이 (작품 CELL_ASPECT 와 같게)")
    ap.add_argument("--ss", type=int, default=1, help="칸보다 몇 배 촘촘하게 뽑을지 (1~4)")
    ap.add_argument("--palette", type=int, default=5, help="대표 색 개수")
    ap.add_argument("--bg-threshold", type=float, default=0.12, help="투명도 없는 이미지에서 배경으로 볼 색 차이")
    a = ap.parse_args(argv)
    try:
        f = make_field(a.image, a.cols, a.rows, a.cell_aspect, a.ss, a.palette, a.bg_threshold)
    except FieldError as e:
        print("image_to_field: %s" % e, file=sys.stderr)
        return 1
    save_field(f, a.out)
    print("ok %s  %dx%d 칸 × ss %d, 피사체 마스크: %s, 팔레트 %s"
          % (a.out, f["cols"], f["rows"], f["ss"], f["alpha_from"], " ".join(f["palette"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
