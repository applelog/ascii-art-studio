"""단계 연결 검사: ① 완성 화면 = ② 등장 끝 = ③ 모션 처음 = ③ 모션 끝.

이 네 화면이 같아야 등장 → 모션, 모션 끝 → 처음이 튀지 않고 이어진다. 글자와 색까지 비교한다.
"""
from .grid import Grid


def link_report(ns):
    """[(설명, 같은지, 다른 칸 수), …]. intro·motion 이 없는 항목은 빠진다."""
    from .player import PieceRenderer

    r = PieceRenderer(ns)
    if r.kind != "staged":
        return []
    state = r.state

    def grid(fn):
        g = Grid(ns["COLS"], ns["ROWS"])
        fn(g)
        return g

    scene = grid(lambda g: ns["scene"](state, g))
    checks = []
    if callable(ns.get("intro")):
        checks.append(("② 등장 끝 (p=1)", grid(lambda g: ns["intro"](state, 1.0, g))))
    if callable(ns.get("motion")):
        loop_s = ns.get("LOOP_SECONDS", 1)
        checks.append(("③ 모션 처음 (phase=0)", grid(lambda g: ns["motion"](state, 0.0, 0.0, g))))
        checks.append(("③ 모션 끝 (phase=1)", grid(lambda g: ns["motion"](state, float(loop_s), 1.0, g))))
    out = []
    for name, g in checks:
        diff = int(((g.ch != scene.ch) | (g.rgb != scene.rgb).any(axis=-1)).sum())
        out.append((name, diff == 0, diff))
    return out


def print_report(ns, log=print):
    """검사 결과를 출력하고, 모두 같으면 True."""
    rep = link_report(ns)
    if not rep:
        return True
    ok = all(same for _, same, _ in rep)
    log("단계 연결 검사 (① 완성 화면과 비교): " + ("모두 같음" if ok else "다른 곳 있음"))
    for name, same, diff in rep:
        log("  %s %s" % ("✓" if same else "✗", name) + ("" if same else "  — 다른 칸 %d개" % diff))
    return ok
