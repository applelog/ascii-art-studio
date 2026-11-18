"""seed 로 정해지는 값 노이즈 (eyeTutorial 의 tex2d · noise1d 와 같은 역할).

격자점마다 해시로 0..1 값을 정하고 부드럽게 보간한다. 좌표 범위 제한이 없고, 같은 seed 면 언제나 같다.

    noise1(t)                        1D (시선 흔들림, 깜박임 시각 등)
    noise2(x, y) / noise3(x, y, z)   2D·3D
    fbm(x, y, z, octaves)            여러 크기의 노이즈를 겹친 것 (구름·성운·물결 질감)
    loop_noise(x, y, phase, radius)  phase 0 과 1 에서 같은 값 → 루프가 이어지는 흐름
"""
import math

import numpy as np

from .ramp import cell_hash

_Z_X, _Z_Y = 7919, 104729      # z 축을 2D 해시로 접어 넣는 소수 (서로 겹치지 않게)


def _fade(t):
    return t * t * (3 - 2 * t)


def _lattice(ix, iy, iz, seed):
    return cell_hash(ix + iz * _Z_X, iy - iz * _Z_Y, seed)


def noise3(x, y, z, seed=0):
    """3D 값 노이즈, 결과 0..1."""
    x, y, z = np.broadcast_arrays(np.asarray(x, np.float64), np.asarray(y, np.float64), np.asarray(z, np.float64))
    xi, yi, zi = np.floor(x), np.floor(y), np.floor(z)
    fx, fy, fz = _fade(x - xi), _fade(y - yi), _fade(z - zi)
    xi, yi, zi = xi.astype(np.int64), yi.astype(np.int64), zi.astype(np.int64)
    out = np.zeros(x.shape, np.float64)
    for dz in (0, 1):
        wz = fz if dz else 1 - fz
        for dy in (0, 1):
            wy = fy if dy else 1 - fy
            for dx in (0, 1):
                wx = fx if dx else 1 - fx
                out += wx * wy * wz * _lattice(xi + dx, yi + dy, zi + dz, seed)
    return out


def noise2(x, y, seed=0):
    """2D 값 노이즈 (z 를 쓰지 않아 3D 보다 4배 빠름), 결과 0..1."""
    x, y = np.broadcast_arrays(np.asarray(x, np.float64), np.asarray(y, np.float64))
    xi, yi = np.floor(x), np.floor(y)
    fx, fy = _fade(x - xi), _fade(y - yi)
    xi, yi = xi.astype(np.int64), yi.astype(np.int64)
    a = _lattice(xi, yi, 0, seed) * (1 - fx) + _lattice(xi + 1, yi, 0, seed) * fx
    b = _lattice(xi, yi + 1, 0, seed) * (1 - fx) + _lattice(xi + 1, yi + 1, 0, seed) * fx
    return a * (1 - fy) + b * fy


def noise1(t, seed=0):
    """1D 값 노이즈, 결과 0..1."""
    return noise2(t, 0.0, seed)


def fbm(x, y, z=None, octaves=4, lacunarity=2.0, gain=0.5, seed=0):
    """여러 크기를 겹친 노이즈 (fractal Brownian motion). 결과 대략 0..1.

    octaves 겹 수, lacunarity 다음 겹의 촘촘함 배수, gain 다음 겹의 세기 배수.
    """
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for k in range(int(octaves)):
        s = seed + k * 1013
        if z is None:
            total = total + amp * noise2(np.asarray(x) * freq, np.asarray(y) * freq, s)
        else:
            total = total + amp * noise3(np.asarray(x) * freq, np.asarray(y) * freq, np.asarray(z) * freq, s)
        norm += amp
        amp *= gain
        freq *= lacunarity
    return total / norm


def loop_noise(x, y, phase, radius=1.0, octaves=3, seed=0):
    """루프용 노이즈: 시간을 원 위에서 돈다 → phase 0 과 1 에서 정확히 같은 값.

    radius 가 클수록 한 루프 동안 더 많이 변한다.
    """
    a = 2 * math.pi * float(phase)
    return fbm(np.asarray(x) + radius * math.cos(a), y, radius * math.sin(a), octaves=octaves, seed=seed)
