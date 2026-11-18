"""장면 연출 곡선 (eyeTutorial 의 ss · ease · lid_open · zp 같은 것들).

모두 숫자 하나 또는 numpy 배열을 받는다.

    segment(t, start, end)        t 가 start..end 일 때 0..1 (앞은 0, 뒤는 1)  → 막(act) 진행도
    smoothstep(a, b, x)           a..b 를 부드럽게 0..1
    ease_in / ease_out / ease_in_out
    overshoot(p, back)            끝에서 살짝 넘쳤다가 돌아옴 (눈이 번쩍 뜨이는 느낌)
    keyframes(t, [(시각, 값), …])  키프레임 사이를 곡선으로 잇기
    exp_lerp(a, b, p)             지수 보간 (줌: 같은 시간에 같은 배율만큼 커짐)
    loop_sin(phase, cycles)       phase 0→1 동안 정수 번 도는 사인 (끝과 처음이 이어짐)
"""
import math

import numpy as np


def clamp01(x):
    return np.clip(x, 0.0, 1.0)


def lerp(a, b, p):
    return a + (b - a) * p


def segment(t, start, end):
    """막 진행도: t 가 start 에서 end 로 가는 동안 0→1."""
    if end <= start:
        return np.where(np.asarray(t) >= start, 1.0, 0.0) if np.ndim(t) else float(t >= start)
    return clamp01((np.asarray(t, np.float64) - start) / (end - start))


def smoothstep(a, b, x):
    p = segment(x, a, b)
    return p * p * (3 - 2 * p)


def ease_in(p):
    p = clamp01(p)
    return p ** 3


def ease_out(p):
    p = clamp01(p)
    return 1 - (1 - p) ** 3


def ease_in_out(p):
    p = clamp01(p)
    return np.where(p < 0.5, 4 * p ** 3, 1 - (-2 * p + 2) ** 3 / 2)


def overshoot(p, back=1.70158):
    """끝에서 넘쳤다가 1 로 돌아오는 곡선. back 이 클수록 많이 넘침 (1.70158 ≈ 10%)."""
    p = clamp01(p)
    c3 = back + 1
    return 1 + c3 * (p - 1) ** 3 + back * (p - 1) ** 2


def keyframes(t, keys, ease=ease_in_out):
    """[(시각, 값), …] 키프레임을 ease 곡선으로 잇는다. 처음 전은 첫 값, 끝 뒤는 끝 값."""
    keys = sorted(keys)
    if not keys:
        raise ValueError("키프레임이 비었습니다")
    t = float(t)
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return lerp(v0, v1, float(ease(segment(t, t0, t1))))
    return keys[-1][1]


def exp_lerp(a, b, p):
    """a→b 지수 보간 (a, b > 0). 줌처럼 '같은 시간에 같은 배율' 로 변할 때."""
    return a * (b / a) ** clamp01(p)


def loop_sin(phase, cycles, offset=0.0):
    """phase 0→1 동안 cycles 번 (정수로 반올림) 도는 사인. phase 0 과 1 에서 값이 같다."""
    return np.sin(2 * math.pi * (max(1, int(round(cycles))) * np.asarray(phase) + offset))


def loop_cycles(cycles):
    """루프가 이어지도록 주기 수를 정수(1 이상)로."""
    return max(1, int(round(cycles)))
