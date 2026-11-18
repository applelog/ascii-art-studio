"""잔상(TRAIL)과 글로우(GLOW) — 글자 이미지 위에 거는 효과.

잔상: 흔적이 매 프레임 같은 양(release)씩 줄어드는 선형 감쇠. 흔적은 (지난 밝기 − 지난 프레임 수 × release)
      이고, 새 화면이 더 밝으면 새 화면이 덮는다. TRAIL 이 클수록 release 가 작아 꼬리가 길다.
글로우: 글자를 흐리게 퍼뜨려 더한다.

잔상은 이전 프레임에 기댄다. 그래도 "같은 프레임 번호 = 같은 그림" 이 되도록,
렌더러는 연속 재생이 아닐 때 warmup_frames() 만큼 앞 프레임부터 다시 그린다.
선형 감쇠라 그만큼 지난 흔적은 정확히 0 이하가 되어 화면에 남지 않으므로 결과가 같다.

바탕이 밝으면(밝은 종이에 어두운 글자) 잉크를 "바탕에서 어두워진 양" 으로 계산해 같은 효과를 낸다.
"""
import math

import numpy as np

GLOW_DOWNSCALE = 4      # 글로우는 1/4 크기에서 흐리게 한 뒤 다시 키운다 (빠름)
INK_MAX = 255.0         # 가장 밝은 흔적 (8비트 화면)
RELEASE_SCALE = 0.5     # release = INK_MAX × (1 − TRAIL) × 이 값 — TRAIL 0.8 이면 프레임마다 25.5 씩, 10 프레임에 사라짐


def trail_release(trail):
    """잔상 흔적이 한 프레임에 줄어드는 양 (0..255 밝기 단위)."""
    return INK_MAX * (1 - trail) * RELEASE_SCALE


def warmup_frames(trail):
    """가장 밝은 잔상 흔적이 완전히 사라지는 데 걸리는 프레임 수."""
    if trail <= 0:
        return 0
    return int(math.ceil(INK_MAX / trail_release(trail)))


class TrailGlow:
    """OpenCV 함수로 계산한다 (numpy 로 큰 이미지에 여러 번 연산하면 프레임당 40ms 가까이 걸렸다)."""

    def __init__(self, background, trail=0.0, glow=0.0, glow_radius_px=8.0):
        import cv2

        self.cv2 = cv2
        self.bg_rgb = tuple(int(round(c)) for c in background)
        self.dark = (0.30 * self.bg_rgb[0] + 0.60 * self.bg_rgb[1] + 0.10 * self.bg_rgb[2]) < 128
        self.trail = float(trail)
        self.release = np.float32(trail_release(self.trail)) if self.trail > 0 else np.float32(0)
        self.glow = float(glow)
        self.radius = float(glow_radius_px)
        self.state = None
        self._bg_u8 = None
        self._bg_f = None

    def reset(self):
        self.state = None

    def _backgrounds(self, shape):
        if self._bg_u8 is None or self._bg_u8.shape != shape:
            self._bg_u8 = np.empty(shape, np.uint8)
            self._bg_u8[...] = self.bg_rgb
            self._bg_f = self._bg_u8.astype(np.float32)
        return self._bg_u8, self._bg_f

    def _blur(self, ink):
        cv2 = self.cv2
        h, w = ink.shape[:2]
        small = cv2.resize(ink, (max(1, w // GLOW_DOWNSCALE), max(1, h // GLOW_DOWNSCALE)), interpolation=cv2.INTER_AREA)
        small = cv2.GaussianBlur(small, (0, 0), sigmaX=max(0.5, self.radius / GLOW_DOWNSCALE))
        return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)

    def apply(self, img_rgb):
        """새 프레임 이미지(uint8 RGB) → 효과를 건 이미지. 잔상 상태가 갱신된다."""
        cv2 = self.cv2
        bg_u8, bg_f = self._backgrounds(img_rgb.shape)
        # 잉크 = 바탕에서 밝아진 양 (밝은 바탕이면 어두워진 양). 0 아래는 0 (포화 뺄셈)
        ink = cv2.subtract(img_rgb, bg_u8) if self.dark else cv2.subtract(bg_u8, img_rgb)
        ink = ink.astype(np.float32)
        if self.trail > 0:
            if self.state is None:
                self.state = ink
            else:
                self.state -= self.release                     # 흔적을 같은 양만큼 줄임 (음수는 아래에서 덮임)
                cv2.max(ink, self.state, dst=self.state)       # 새 화면이 더 밝은 곳은 새 화면 (ink ≥ 0)
            ink = self.state
        if self.glow > 0:
            ink = cv2.scaleAdd(self._blur(ink), self.glow, ink)
        if self.dark:
            out = cv2.add(bg_f, ink)
        else:
            out = cv2.max(cv2.subtract(bg_f, ink), 0.0)
        return cv2.convertScaleAbs(out)                       # 반올림 + 0..255 로 자르기
