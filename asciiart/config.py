"""작품 맨 앞 설정 변수 모으기 · 범위 검사 · --set 덮어쓰기.

설정 변수 = 작품 파일에서 '# ===== 코드 =====' 줄 위에 있는 대문자 변수.
작품마다 범위를 정하고 싶으면 설정 블록 안에 RANGES = {"SPEED": (0.25, 4)} 를 둔다.
범위를 벗어난 값은 고쳐서 쓰고, 무엇을 고쳤는지 경고로 알려 준다.
"""
import ast
import difflib
import numbers

CODE_MARK = "# ===== 코드 ====="

# 모든 작품에 공통인 설정의 범위
BASE_RANGES = {
    "COLS": (16, 400),
    "ROWS": (8, 240),
    "FONT_PX": (6, 48),
    "CELL_ASPECT": (0.35, 1.2),
    "LOOP_SECONDS": (0.5, 120),
    "INTRO_SECONDS": (0.2, 60),
    "INTRO_HOLD": (0, 10),
    "FINAL_LOOPS": (1, 20),
    "TRAIL": (0, 0.97),
    "GLOW": (0, 1),
    "GLOW_RADIUS": (0.1, 5),
    "SEED": (0, 2 ** 32 - 1),
}
INTEGER_KEYS = {"COLS", "ROWS", "FONT_PX", "SEED", "FINAL_LOOPS"}
FPS_ALLOWED = (12, 24, 30, 60)


def setting_names(path):
    """작품 파일의 설정 블록에서 대문자 변수 이름을 순서대로 모은다 (RANGES 는 제외)."""
    src = open(path, encoding="utf-8").read()
    head, mark, _ = src.partition(CODE_MARK)
    if not mark:
        raise SystemExit("작품 파일에 '%s' 줄이 없습니다: %s" % (CODE_MARK, path))
    names = []
    for node in ast.parse(head).body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            elts = target.elts if isinstance(target, ast.Tuple) else [target]
            for e in elts:
                if isinstance(e, ast.Name) and e.id.isupper() and e.id != "RANGES" and e.id not in names:
                    names.append(e.id)
    return names


def _is_number(v):
    return isinstance(v, numbers.Real) and not isinstance(v, bool)


def _is_rgb(v):
    return isinstance(v, (tuple, list)) and len(v) == 3 and all(_is_number(c) for c in v)


def _clamp(v, lo, hi):
    return min(hi, max(lo, v))


def check(ns, names=None):
    """설정 값을 검사하고, 범위를 벗어나면 ns 안에서 고친다. 고친 내용을 경고 목록으로 돌려준다."""
    names = names if names is not None else [k for k in ns if k.isupper()]
    ranges = dict(BASE_RANGES)
    ranges.update(ns.get("RANGES") or {})
    warnings = []

    def fix(key, old, new, why):
        if old != new:
            ns[key] = new
            warnings.append("%s: %r → %r (%s)" % (key, old, new, why))

    for key in names:
        if key not in ns:
            continue
        v = ns[key]
        if key == "FPS":
            if not _is_number(v) or v not in FPS_ALLOWED:
                near = min(FPS_ALLOWED, key=lambda f: abs(f - v) if _is_number(v) else 0)
                fix(key, v, near, "지원 FPS %s" % "/".join(map(str, FPS_ALLOWED)))
            continue
        if key in ranges:
            lo, hi = ranges[key]
            if _is_number(v):
                new = _clamp(v, lo, hi)
                if key in INTEGER_KEYS:
                    new = int(round(new))
                fix(key, v, new, "허용 %s~%s" % (lo, hi))
            elif isinstance(v, (tuple, list)) and all(_is_number(c) for c in v):
                fix(key, v, type(v)(_clamp(c, lo, hi) for c in v), "허용 %s~%s" % (lo, hi))
            continue
        # 색: 이름이 RGB / BACKGROUND / PALETTE 인 것은 0~255 정수 3개
        if key.endswith("RGB") or key == "BACKGROUND":
            if not _is_rgb(v):
                raise SystemExit("%s 는 (R, G, B) 형식이어야 합니다: %r" % (key, v))
            fix(key, v, tuple(int(_clamp(round(c), 0, 255)) for c in v), "색 0~255")
        elif key == "PALETTE":
            if not isinstance(v, (tuple, list)) or not v or not all(_is_rgb(c) for c in v):
                raise SystemExit("PALETTE 는 (R, G, B) 목록이어야 합니다: %r" % (v,))
            fix(key, v, [tuple(int(_clamp(round(x), 0, 255)) for x in c) for c in v], "색 0~255")
        elif key.endswith("RAMP"):
            if not isinstance(v, str) or len(v) < 2:
                raise SystemExit("%s 는 두 글자 이상의 문자열이어야 합니다: %r" % (key, v))
    return warnings


def _parse(text):
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return text


def apply_set(ns, pairs, names):
    """--set KEY=VALUE 를 적용한다. 없는 이름이나 형식이 다른 값은 멈추고 알려 준다."""
    changed = []
    for pair in pairs or []:
        if "=" not in pair:
            raise SystemExit("--set 은 KEY=VALUE 형식이어야 합니다: %s" % pair)
        key, raw = [x.strip() for x in pair.split("=", 1)]
        if key not in names:
            near = difflib.get_close_matches(key, names, n=3)
            raise SystemExit("이 작품에 없는 설정입니다: %s%s" % (key, ("  (혹시: %s)" % ", ".join(near)) if near else ""))
        old, new = ns[key], _parse(raw)
        if isinstance(old, str):
            new = raw if not isinstance(new, str) else new
        elif _is_number(old):
            if not _is_number(new):
                raise SystemExit("%s 는 숫자여야 합니다: %s" % (key, raw))
        elif isinstance(old, bool):
            if not isinstance(new, bool):
                raise SystemExit("%s 는 True/False 여야 합니다: %s" % (key, raw))
        elif isinstance(old, (tuple, list)):
            if not isinstance(new, (tuple, list)) or (len(new) != len(old) and key != "PALETTE"):
                raise SystemExit("%s 는 %d개 값이어야 합니다: %s" % (key, len(old), raw))
            new = type(old)(new)
        ns[key] = new
        changed.append(key)
    return changed
