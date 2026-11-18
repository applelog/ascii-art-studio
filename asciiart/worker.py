"""미리 계산 작업자 프로세스 (asciiart.pool 이 띄운다. 직접 실행하지 않는다).

메인과 표준 입출력 파이프로 [8바이트 길이 + pickle] 묶음을 주고받는다.
작품이 print 해도 통신이 섞이지 않게, 통신용 출력은 따로 떼고 화면 출력은 stderr 로 돌린다.
"""
import importlib.util
import os
import pickle
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def recv(f):
    head = f.read(8)
    if len(head) < 8:
        return None
    (n,) = struct.unpack("<Q", head)
    return pickle.loads(f.read(n))


def send(f, obj):
    data = pickle.dumps(obj, protocol=4)
    f.write(struct.pack("<Q", len(data)))
    f.write(data)
    f.flush()


def main():
    inp = sys.stdin.buffer
    out = os.fdopen(os.dup(1), "wb")          # 통신 전용
    os.dup2(2, 1)                              # 작품의 print 는 stderr 로
    sys.stdout = sys.stderr
    init = recv(inp)
    try:
        from asciiart.grid import Grid
        from asciiart.player import draw_stage

        spec = importlib.util.spec_from_file_location("asciiart_worker_piece", init["path"])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        ns = vars(mod)
        ns.update(init["values"])
        state = ns["setup"]()
        grid = Grid(ns["COLS"], ns["ROWS"])
        send(out, ("ready", None))
    except Exception as e:  # noqa: BLE001
        send(out, ("fail", repr(e)))
        return
    while True:
        msg = recv(inp)
        if msg is None:
            return
        stage, i, n, fps = msg
        try:
            draw_stage(ns, state, grid, stage, i, n, fps)
            send(out, ("ok", (stage, i), grid.ch.copy(), grid.rgb.copy()))
        except Exception as e:  # noqa: BLE001
            send(out, ("err", (stage, i), repr(e), None))


if __name__ == "__main__":
    main()
