#!/usr/bin/env python3
"""대본(마크다운)의 글자수를 세서 예상 러닝타임을 계산합니다.
섹션(## 제목)별로 몇 분 몇 초쯤 되는지, 누적 타임코드는 어디쯤인지 보여줍니다.

사용 예시:
    python3 scripts/script_timer.py channel/plans/2026-07-07-주제-대본.md
    python3 scripts/script_timer.py 대본.md --target 10        # 목표 10분과 비교
    python3 scripts/script_timer.py 대본.md --target 8:30      # 목표 8분 30초
    python3 scripts/script_timer.py 대본.md --cpm 330          # 말이 빠른 편이면 분당 글자수 조절
    python3 scripts/script_timer.py 대본.md --chapters         # 유튜브 챕터 타임스탬프 초안 출력

계산에서 빠지는 것: 제목(#), 인용문(>), 표(|), 체크박스, [대괄호 안 화면 지시],
'촬영 메모' 이후 섹션. 즉 실제로 입으로 말하는 글자만 셉니다.

필요한 도구: 없음 (파이썬만 있으면 됩니다)
"""

import argparse
import re
import sys
from pathlib import Path

# 이 제목이 나오면 그 섹션부터는 말하지 않는 내용으로 본다
SKIP_SECTION_KEYWORDS = ("촬영 메모", "체크리스트", "메모")


def parse_target(value):
    """'10' → 600초, '8:30' → 510초, '8분 30초' → 510초"""
    value = value.strip()
    m = re.fullmatch(r"(\d+):(\d{1,2})", value)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m = re.fullmatch(r"(\d+)\s*분(?:\s*(\d+)\s*초?)?", value)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2) or 0)
    try:
        return float(value) * 60
    except ValueError:
        sys.exit(f"❌ 목표 길이를 이해하지 못했어요: '{value}' (예: 10, 8:30, 8분 30초)")


def find_target_in_text(text):
    """대본 머리말의 '예상 러닝타임: 10분' 또는 기획안의 '예상 길이: 10분'을 찾는다."""
    m = re.search(r"예상\s*(?:러닝타임|길이)\s*[:：]\s*(\d+)\s*분(?:\s*(\d+)\s*초)?", text)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2) or 0)
    return None


def spoken_chars(line):
    """한 줄에서 실제로 말하는 글자수(공백 제외)를 센다. 말하지 않는 줄이면 0."""
    stripped = line.strip()
    if not stripped:
        return 0
    # 제목·인용·표·구분선·체크박스·HTML 주석은 말하지 않는다
    if stripped.startswith(("#", ">", "|", "---", "- [ ]", "- [x]", "<!--", "-->")):
        return 0
    # [대괄호] 안은 화면·자막 지시 → 제외
    text = re.sub(r"\[[^\]]*\]", "", stripped)
    # 남은 마크다운 기호(굵게, 목록 표시 등) 제거
    text = re.sub(r"[*_`]", "", text)
    text = re.sub(r"^\s*[-•]\s+", "", text)
    return len(re.sub(r"\s+", "", text))


def timecode(seconds):
    m, s = divmod(int(round(seconds)), 60)
    return f"{m:d}:{s:02d}"


def chapter_title(title):
    """섹션 제목에서 챕터용 텍스트만 남긴다: (시간 표시)·🎬·[지시]·'본문 N —' 제거"""
    t = re.sub(r"\([^)]*\)", "", title)
    t = t.replace("🎬", "")
    t = re.sub(r"\[[^\]]*\]", "", t)
    t = re.sub(r"^본문\s*\d+\s*[—–\-]\s*", "", t)
    t = t.strip(" -—–")
    return t or title.strip()


def analyze(path, cpm):
    text = Path(path).read_text(encoding="utf-8")
    # 코드펜스 표시(```)만 지우고 내용은 살린다 (기획안 인트로가 펜스 안에 있는 경우)
    lines = [l for l in text.splitlines() if not l.strip().startswith("```")]

    sections = []  # (제목, 글자수)
    current_title = "(머리말)"
    current_chars = 0
    skipping = False
    in_comment = False

    for line in lines:
        # <!-- 여러 줄 주석 --> 은 통째로 건너뛴다
        stripped = line.strip()
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if stripped.startswith("<!--"):
            if "-->" not in stripped:
                in_comment = True
            continue
        m = re.match(r"^##\s+(.*)", line.strip())
        if m:
            if current_chars:
                sections.append((current_title, current_chars))
            current_title = m.group(1).strip()
            current_chars = 0
            skipping = any(k in current_title for k in SKIP_SECTION_KEYWORDS)
            continue
        if not skipping:
            current_chars += spoken_chars(line)
    if current_chars:
        sections.append((current_title, current_chars))

    return text, sections


def main():
    parser = argparse.ArgumentParser(
        description="대본 글자수 → 예상 러닝타임 계산",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file", help="대본 마크다운 파일 경로")
    parser.add_argument("--cpm", type=int, default=300,
                        help="분당 말하는 글자수 (기본 300, 말이 빠르면 330~350)")
    parser.add_argument("--target", default=None,
                        help="목표 길이 (예: 10, 8:30, 8분 30초). 안 주면 파일 안의 '예상 러닝타임'을 찾아서 씁니다")
    parser.add_argument("--chapters", action="store_true",
                        help="유튜브 설명란에 붙일 챕터 타임스탬프 초안을 출력합니다")
    args = parser.parse_args()

    if not Path(args.file).exists():
        sys.exit(f"❌ 파일을 찾을 수 없어요: {args.file}")

    text, sections = analyze(args.file, args.cpm)
    if not sections:
        sys.exit("❌ 말하는 내용을 찾지 못했어요. 대본 본문이 비어 있지 않은지 확인해 주세요.")

    total_chars = sum(c for _, c in sections)
    total_sec = total_chars / args.cpm * 60

    if args.chapters:
        print("\n📎 챕터 타임스탬프 초안 (설명란에 붙여넣기)")
        print("   ⚠️  대본 기준 추정치예요. 편집 후 실제 영상 시간에 맞게 조정하세요.\n")
        cum = 0.0
        for title, chars in sections:
            print(f"{timecode(cum)} {chapter_title(title)}")
            cum += chars / args.cpm * 60
        print()
        return

    print(f"\n📖 {args.file}  (분당 {args.cpm}자 기준)\n")
    print(f"{'시작':>6}  {'섹션':<28} {'글자수':>6}  {'길이':>6}")
    print("-" * 56)
    cum = 0.0
    for title, chars in sections:
        sec = chars / args.cpm * 60
        title_short = title if len(title) <= 26 else title[:25] + "…"
        print(f"{timecode(cum):>6}  {title_short:<28} {chars:>6,}  {timecode(sec):>6}")
        cum += sec
    print("-" * 56)
    print(f"{'':>6}  {'합계':<28} {total_chars:>6,}  {timecode(total_sec):>6}")

    target_sec = parse_target(args.target) if args.target else find_target_in_text(text)
    if target_sec:
        diff = total_sec - target_sec
        sign = "+" if diff >= 0 else "-"
        pct = abs(diff) / target_sec * 100
        print(f"\n🎯 목표 {timecode(target_sec)} 대비 {sign}{timecode(abs(diff))} ({pct:.0f}%)")
        if abs(pct) <= 10:
            print("   ✅ 목표 길이와 거의 맞아요.")
        elif diff > 0:
            need = int(diff / 60 * args.cpm)
            print(f"   ✂️  약 {need:,}자 줄이면 목표에 맞습니다.")
        else:
            need = int(-diff / 60 * args.cpm)
            print(f"   ➕ 약 {need:,}자 보태면 목표에 맞습니다.")
    print()


if __name__ == "__main__":
    main()
