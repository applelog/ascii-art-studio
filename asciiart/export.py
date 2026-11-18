"""저장: PNG · MP4 · GIF · 프레임 띠.

모든 저장은 renderer.image_at(i) (정확한 그림) 를 프레임 번호 순서대로 쓴다.
창 재생과 달리 실제 시간에 맞추지 않으므로 프레임을 하나도 건너뛰지 않는다.

루프 작품의 MP4 는 0 … N-1 번 프레임을 loops 번 이어 붙인다. 끝 프레임(phase=1)은 0 번과 같은 장면이라
넣지 않으므로, 영상을 반복 재생해도 이음매에서 같은 장면이 두 번 나오지 않는다.
"""
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .atlas import save_png

MP4_CRF = 18                 # 화질 (낮을수록 좋음, 18 ≈ 눈으로 구분 어려움)
MP4_PRESET = "medium"        # 인코딩 속도/압축 균형
PREFETCH_AHEAD = 48          # 무거운 작품을 저장할 때 미리 맡겨 둘 프레임 수
GIF_FPS = 10                 # GIF 기본 초당 프레임 (GIF 는 10ms 단위라 10·20·25·50 이 정확)
GIF_SCALE = 0.5              # GIF 크기 배율 (파일이 커지는 것을 막음)
STRIP_SCALE = 0.5            # 프레임 띠 한 장의 크기 배율
STRIP_GAP = 10               # 프레임 띠 사이 간격 (px)
STRIP_BG = (40, 40, 40)      # 프레임 띠 간격 색
LABEL_RGB = (255, 255, 255)  # 프레임 띠 시각 글씨 색


class ExportError(RuntimeError):
    pass


def find_tool(name):
    """ffmpeg / ffprobe 찾기: 환경 변수 → 지금 Python 옆 (conda 환경) → PATH."""
    env = os.environ.get("ASCIIART_" + name.upper())
    if env:
        return env
    here = os.path.join(os.path.dirname(sys.executable), name)
    if os.path.isfile(here) and os.access(here, os.X_OK):
        return here
    found = shutil.which(name)
    if found:
        return found
    raise ExportError("%s 를 찾지 못했습니다. conda activate min 후 실행하거나 ASCIIART_%s 에 경로를 넣어 주세요."
                      % (name, name.upper()))


def video_frames(renderer, loops=1):
    """MP4 에 넣을 위치들 (렌더러 시간축을 따름: 원형이면 한 바퀴 × loops, 등장이 있으면 등장 + 모션 × loops)."""
    return renderer.video_frames(loops)


def _progress_bar(done, total, label, _last={}):
    """진행 표시. 터미널이면 한 줄을 고쳐 쓰고(칸이 바뀔 때만), 아니면 10% 마다 한 줄."""
    width = 30
    k = int(width * done / max(1, total))
    pct = int(100 * done / max(1, total))
    tty = sys.stdout.isatty()
    key = (label, total)
    step = k if tty else pct // 10
    if _last.get(key) == step and done < total:
        return
    _last[key] = step
    if tty:
        sys.stdout.write("\r%s [%s%s] %d/%d" % (label, "#" * k, "." * (width - k), done, total))
        if done >= total:
            sys.stdout.write("\n")
    else:
        sys.stdout.write("%s %d%% (%d/%d)\n" % (label, pct, done, total))
    sys.stdout.flush()


def write_mp4(renderer, path, loops=1, crf=MP4_CRF, preset=MP4_PRESET, progress=_progress_bar, use_processes=True):
    """MP4 (H.264, yuv420p) 저장. 가로·세로가 홀수면 오른쪽·아래에 바탕색 한 줄을 덧대 짝수로 맞춘다.

    Ctrl+C 나 오류로 멈추면 만들다 만 파일을 지운다.
    """
    frames = video_frames(renderer, loops)
    first = renderer.image_at(frames[0])
    h, w = first.shape[:2]
    pw, ph = w + (w % 2), h + (h % 2)
    bg = tuple(int(c) for c in renderer.ns["BACKGROUND"])
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    tmp = path + ".part.mp4"
    cmd = [find_tool("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (pw, ph), "-r", str(renderer.fps), "-i", "-",
           "-an", "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", tmp]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    pad = np.empty((ph, pw, 3), np.uint8)
    pad[...] = bg
    pooled = renderer.start_pool() if use_processes else False   # 무거운 작품이면 여러 프로세스로 미리 계산
    try:
        for k, i in enumerate(frames):
            if pooled:
                renderer.pool.request(frames[k + 1:k + 1 + PREFETCH_AHEAD])
            img = first if k == 0 else renderer.image_at(i)
            pad[:h, :w] = img
            proc.stdin.write(pad.tobytes())
            if progress:
                progress(k + 1, len(frames), "MP4")
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "replace")
        if proc.wait() != 0:
            raise ExportError("ffmpeg 실패: " + err.strip()[-500:])
        os.replace(tmp, path)
    except BaseException:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    finally:
        if pooled:
            renderer.stop_pool()
    return path


def probe(path):
    """영상 정보 (ffprobe): 가로, 세로, 프레임 수, 길이(초), 초당 프레임."""
    out = subprocess.run([find_tool("ffprobe"), "-v", "error", "-select_streams", "v:0", "-count_frames",
                          "-show_entries", "stream=width,height,nb_read_frames,r_frame_rate:format=duration",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    info = json.loads(out)
    st = info["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    return {"width": int(st["width"]), "height": int(st["height"]), "frames": int(st["nb_read_frames"]),
            "duration": float(info["format"]["duration"]), "fps": float(num) / float(den)}


def gif_timing(fps, gif_fps=GIF_FPS):
    """(몇 프레임마다 한 장, 한 장 시간 ms). GIF 시간은 10ms 단위라 그에 맞춘다."""
    step = max(1, int(round(fps / float(gif_fps))))
    delay = int(round(step * 1000.0 / fps / 10.0)) * 10
    return step, max(10, delay)


def write_gif(renderer, path, gif_fps=GIF_FPS, scale=GIF_SCALE, progress=_progress_bar):
    """GIF 저장 (한 루프). 크기를 scale 배로 줄이고, 프레임마다 256색 팔레트."""
    step, delay = gif_timing(renderer.fps, gif_fps)
    picks = list(range(0, renderer.n, step))
    frames = []
    for k, i in enumerate(picks):
        im = Image.fromarray(renderer.image_at(i))
        if scale != 1:
            im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
        frames.append(im.quantize(colors=256, method=Image.MEDIANCUT, dither=Image.NONE))
        if progress:
            progress(k + 1, len(picks), "GIF")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=delay,
                   loop=0 if renderer.loop else 1, disposal=1, optimize=False)
    return path


def strip_frames(renderer, count=6):
    """프레임 띠에 쓸 프레임 번호 (한 루프를 고르게 나눔)."""
    count = max(1, min(int(count), renderer.n))
    return sorted({int(round(k * renderer.n / float(count))) % renderer.n for k in range(count)})


def write_strip(renderer, path, frames=None, columns=3, scale=STRIP_SCALE):
    """시간순 프레임 여러 장을 한 장으로 이어 붙이고 왼쪽 위에 시각을 적는다."""
    frames = strip_frames(renderer) if frames is None else list(frames)
    shots = [Image.fromarray(renderer.image_at(i)) for i in frames]
    w, h = int(shots[0].width * scale), int(shots[0].height * scale)
    cols = min(columns, len(shots))
    rows = (len(shots) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w + (cols - 1) * STRIP_GAP, rows * h + (rows - 1) * STRIP_GAP), STRIP_BG)
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=max(10, h // 24))
    except TypeError:  # 오래된 Pillow
        font = ImageFont.load_default()
    for k, (i, im) in enumerate(zip(frames, shots)):
        x, y = (k % cols) * (w + STRIP_GAP), (k // cols) * (h + STRIP_GAP)
        sheet.paste(im.resize((w, h), Image.LANCZOS), (x, y))
        draw.text((x + 6, y + 4), "%.2fs  #%d" % (i / float(renderer.fps), i), fill=LABEL_RGB, font=font)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    sheet.save(path)
    return path


def write_png(renderer, path, frame=0):
    return save_png(renderer.image_at(frame), path)
