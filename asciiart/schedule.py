"""무작위 사건 일정표 (별똥별·혜성·번개 같은 것).

eyeTutorial 은 재생 중에 무작위로 별똥별을 만들지만, 여기서는 setup() 에서 seed 로 일정표를 미리 만든다.
그래서 다시 재생하든, 프레임을 건너뛰든, 영상으로 저장하든 같은 순간에 같은 사건이 나온다.

    events = make_schedule(seed=SEED, count=6, span=LOOP_SECONDS, duration=(0.6, 1.2))
    for ev, p in active(events, t, span=LOOP_SECONDS):   # p = 사건 진행도 0..1
        ...ev["rand"][0] 같은 값으로 위치·방향을 정한다
"""
import numpy as np

RAND_VALUES = 8     # 사건마다 미리 뽑아 두는 0..1 난수 개수 (위치·각도·밝기 등에 씀)


def make_schedule(seed, count, span, duration=(0.5, 1.0), min_gap=0.0):
    """span 초 안에 count 개 사건. 시작 시각은 무작위, 사건끼리 min_gap 초 이상 떨어뜨린다.

    각 사건: {"start": 초, "dur": 길이 초, "rand": 0..1 난수 RAND_VALUES 개}
    """
    rng = np.random.RandomState(seed)
    starts = []
    tries = 0
    while len(starts) < count and tries < count * 200:
        tries += 1
        s = rng.uniform(0, span)
        if all(min(abs(s - o), span - abs(s - o)) >= min_gap for o in starts):
            starts.append(s)
    starts.sort()
    lo, hi = duration
    return [{"start": float(s), "dur": float(rng.uniform(lo, hi)), "rand": rng.uniform(0, 1, RAND_VALUES)}
            for s in starts]


def active(events, t, span=None, loop=True):
    """시각 t 에 진행 중인 사건과 진행도 p (0..1) 목록.

    loop=True 면 span 초마다 반복된다 (끝에서 시작한 사건이 처음으로 이어짐).
    """
    out = []
    for ev in events:
        age = (t - ev["start"]) % span if (loop and span) else t - ev["start"]
        if 0 <= age < ev["dur"]:
            out.append((ev, age / ev["dur"]))
    return out
