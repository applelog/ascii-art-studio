"""새 작품 폴더 만들기: pieces/<slug>/ 에 piece.py (템플릿) · brief.md · GLOSSARY.md.

    python tools/new_piece.py fishing-boat --title "달빛 아래 낚시배" --request "밤하늘에 달빛을 받아…"

slug 는 영문 소문자·숫자·하이픈 (예: ocean-waves, eye-in-space). 이미 있으면 덮어쓰지 않는다.
"""
import argparse
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
TEMPLATE = os.path.join(ROOT, ".claude", "skills", "ascii", "template.py")

BRIEF = """# {title}

## 진행 상태
- 현재 단계: ① 정지 그림 (작성 중)
- ① 정지 그림: 진행 중
- ② 등장 방식: 대기
- ③ 모션: 대기
- 최종본: 대기

## 요청
{request}

## 답변으로 정한 것
- (질문과 답)

## 기본값으로 정한 것
- (사용자가 "알아서" 라고 한 항목, 질문하지 않고 정한 것)

## 참고한 모습
- 출처: (사용자 사진 / 검색한 URL)
- 비율·실루엣:
- 특징 부위 (설정 변수로 둔 것):
- 빛:
- 본 것 / 추정한 것:

## 설계
- 그리는 방식: (필드 렌더 | 글자 배치 | 3D | 이미지 필드 | 혼합) — 이유
- 막(act) 구성:
- 루프: (phase 0 과 1 이 어떻게 이어지는지)

## 수정 기록
- ({date}) 작품 폴더 만듦

## 미리보기 만드는 법
```bash
python {rel}/piece.py --stage 1 --version s1_v1
python {rel}/piece.py --stage 2 --version s2_v1
python {rel}/piece.py --stage 3 --version s3_v1
python {rel}/piece.py --final --version final
```
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("slug")
    ap.add_argument("--title", required=True)
    ap.add_argument("--request", required=True, help="사용자 원문 그대로")
    ap.add_argument("--summary", default="", help="한 줄 설명")
    ap.add_argument("--root", default=os.path.join(ROOT, "pieces"), help="작품 폴더들이 있는 곳")
    a = ap.parse_args(argv)
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", a.slug):
        print("slug 는 영문 소문자·숫자·하이픈만 (예: ocean-waves): %r" % a.slug, file=sys.stderr)
        return 2
    folder = os.path.join(a.root, a.slug)
    if os.path.exists(folder):
        print("이미 있는 작품입니다 (덮어쓰지 않습니다): %s" % folder, file=sys.stderr)
        return 1
    os.makedirs(folder)
    src = open(TEMPLATE, encoding="utf-8").read()
    src = (src.replace("<제목>", a.title).replace("<한 줄 설명>", a.summary or a.title)
              .replace("<사용자 원문>", a.request.replace('"', "'")))
    piece = os.path.join(folder, "piece.py")
    with open(piece, "w", encoding="utf-8") as f:
        f.write(src)
    rel = os.path.relpath(folder, ROOT)
    if rel.startswith(".."):
        rel = folder
    with open(os.path.join(folder, "brief.md"), "w", encoding="utf-8") as f:
        f.write(BRIEF.format(title=a.title, request=a.request, date=datetime.date.today().isoformat(), rel=rel))
    from tools.glossary import update  # noqa: E402

    update(piece, a.title)
    print("작품 폴더를 만들었습니다: %s" % folder)
    print("  piece.py (템플릿) · brief.md · GLOSSARY.md")
    print("다음: piece.py 의 draw() 를 요청에 맞게 고친 뒤  python %s/piece.py --stage 1 --version s1_v1" % rel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
