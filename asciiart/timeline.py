"""시간 → 프레임 번호.

    N      = round(LOOP_SECONDS × FPS)   한 루프의 프레임 수
    i      = 0 .. N-1                   프레임 번호 (끝 프레임 N 은 0 과 같은 장면이라 따로 두지 않음)
    t      = i / FPS                    초
    phase  = i / N                      0 이상 1 미만

그림은 프레임 번호만으로 정해진다. 실제 시간은 "지금 몇 번 프레임을 보여 줄지" 고를 때만 쓴다.
"""
import math


def frame_count(loop_seconds, fps):
    return max(1, int(round(loop_seconds * fps)))


def frame_time(i, fps):
    return i / float(fps)


def frame_phase(i, n):
    return i / float(n)


def frame_at(elapsed, fps, n, loop=True):
    """재생 시작 후 실제 경과 시간(초) → (프레임 번호, 끝났는지).

    루프면 처음으로 돌아가고, 루프가 아니면 마지막 프레임에서 멈춘다.
    """
    raw = int(math.floor(elapsed * fps + 1e-9))
    if loop:
        return raw % n, False
    if raw >= n:
        return n - 1, True
    return max(0, raw), False
