"""여러 프로세스로 글자 버퍼(grid) 미리 계산하기 — 무거운 작품(3D 등)의 창 재생·저장을 빠르게.

Python 스레드는 순수 Python 반복 부분에서 서로 기다리므로, 레이마칭처럼 무거운 계산은 프로세스로 나눈다.
작업자(asciiart/worker.py)는 작품 파일을 불러와 메인과 같은 설정 값을 덮어쓰고 같은 setup() 을 돌린다
→ 같은 (단계, 번호) 면 메인에서 계산한 것과 같은 grid (테스트로 확인).
multiprocessing 을 쓰지 않으므로 메인 프로그램을 다시 불러오지 않는다 (어떤 방식으로 실행해도 동작).
작업자가 죽거나 늦으면 메인이 직접 계산한다 (재생이 멈추지 않음).
"""
import os
import pickle
import queue
import struct
import subprocess
import sys
import threading

HEAVY_MS = 12.0          # 첫 프레임 계산이 이보다 오래 걸리면 프로세스를 쓴다
MAX_WORKERS = 6          # 작업자 수 상한
INFLIGHT_PER_WORKER = 3  # 작업자당 동시에 맡기는 작업 수
WAIT_SECONDS = 3.0       # 맡긴 작업을 기다리는 최대 시간 (넘으면 메인이 직접 계산)
WORKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "worker.py")


def _plain(v):
    if isinstance(v, (bool, int, float, str, type(None))):
        return True
    if isinstance(v, (tuple, list)):
        return all(_plain(x) for x in v)
    if isinstance(v, dict):
        return all(isinstance(k, str) and _plain(x) for k, x in v.items())
    return False


def settings_snapshot(ns):
    """메인 작품의 설정 값 (대문자 변수 중 그대로 넘길 수 있는 것). --set·범위 보정이 반영된 값."""
    return {k: v for k, v in ns.items() if k.isupper() and _plain(v)}


def worker_count():
    return max(1, min((os.cpu_count() or 2) - 2, MAX_WORKERS))


def _send(f, obj):
    data = pickle.dumps(obj, protocol=4)
    f.write(struct.pack("<Q", len(data)))
    f.write(data)
    f.flush()


def _recv(f):
    head = f.read(8)
    if len(head) < 8:
        return None
    (n,) = struct.unpack("<Q", head)
    return pickle.loads(f.read(n))


class GridPool:
    """renderer 의 캐시를 여러 작업자 프로세스로 미리 채운다."""

    def __init__(self, renderer, workers=None):
        path = renderer.ns.get("__file__")
        if not path or not os.path.isfile(path):
            raise RuntimeError("작품 파일 경로가 없어 작업자 프로세스를 쓸 수 없습니다")
        self.renderer = renderer
        self.workers = workers or worker_count()
        self.init = {"path": os.path.abspath(path), "values": settings_snapshot(renderer.ns)}
        self.tasks = queue.Queue()
        self.inflight = {}                 # (단계, 번호) → threading.Event
        self.lock = threading.Lock()
        self.closed = False
        self.errors = []
        self.alive = 0
        self.procs = []
        self.threads = []
        for k in range(self.workers):
            p = subprocess.Popen([sys.executable, "-I", WORKER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL)
            self.procs.append(p)
            th = threading.Thread(target=self._serve, args=(p,), name="asciiart-worker-%d" % k, daemon=True)
            self.threads.append(th)
            th.start()

    def _serve(self, p):
        try:
            _send(p.stdin, self.init)
            first = _recv(p.stdout)
            if not first or first[0] != "ready":
                self.errors.append("작업자 준비 실패: %r" % (first,))
                return
            with self.lock:
                self.alive += 1
            while not self.closed:
                item = self.tasks.get()
                if item is None:
                    return
                key, n, fps = item
                if self.renderer.cached_key(key):
                    self._finish(key)
                    continue
                _send(p.stdin, (key[0], key[1], n, fps))
                res = _recv(p.stdout)
                if res is None:
                    self.errors.append("작업자가 끝났습니다")
                    self._finish(key)
                    return
                if res[0] == "ok":
                    self.renderer.store_arrays(res[1], res[2], res[3])
                else:
                    self.errors.append(res[2])
                self._finish(key)
        except (BrokenPipeError, OSError, EOFError, pickle.UnpicklingError) as e:
            if not self.closed:
                self.errors.append(repr(e))
        finally:
            with self.lock:
                self.alive = max(0, self.alive - 1) if self.alive else 0
                stuck = [] if self.alive else list(self.inflight)
            for key in stuck:                       # 작업자가 모두 죽으면 기다리던 것을 풀어 준다
                self._finish(key)

    def _finish(self, key):
        with self.lock:
            ev = self.inflight.pop(key, None)
        if ev is not None:
            ev.set()

    def request(self, positions):
        """이 위치들의 grid 를 (아직 없으면) 작업자에게 맡긴다."""
        r = self.renderer
        limit = self.workers * INFLIGHT_PER_WORKER
        for k in positions:
            stage, i, n = r.locate(k)
            key = (stage, i)
            with self.lock:
                if self.closed or len(self.inflight) >= limit:
                    return
                if key in self.inflight or r.cached_key(key):
                    continue
                self.inflight[key] = threading.Event()
            self.tasks.put((key, n, r.fps))

    def wait_for(self, key, timeout=WAIT_SECONDS):
        """맡겨 둔 작업이 있으면 끝날 때까지 기다린다 (같은 계산을 메인에서 또 하지 않게)."""
        with self.lock:
            ev = self.inflight.get(key)
        return ev.wait(timeout) if ev is not None else False

    def close(self):
        with self.lock:
            self.closed = True
            waiting = list(self.inflight)
        for _ in self.threads:
            self.tasks.put(None)
        for key in waiting:
            self._finish(key)
        for p in self.procs:
            try:
                p.stdin.close()
            except OSError:
                pass
        for p in self.procs:
            try:
                p.wait(timeout=1)
            except subprocess.TimeoutExpired:
                p.kill()
