#!/usr/bin/env python3
"""롱폼 영상에서 지정한 구간을 잘라 쇼츠 클립을 만듭니다.
--vertical 옵션을 주면 세로(9:16, 1080x1920) 화면으로 가운데를 크롭합니다.

사용 예시:
    python3 scripts/shorts_cut.py 내영상.mp4 00:01:23-00:02:10 00:05:00-00:05:58
    python3 scripts/shorts_cut.py 내영상.mp4 --json 쇼츠목록.json --vertical

JSON 형식 (클로드가 /shorts 스킬에서 자동으로 만들어 줍니다):
    [{"start": "00:01:23", "end": "00:02:10", "title": "훅 문장"}, ...]

필요한 도구: ffmpeg (macOS: brew install ffmpeg / Windows: winget install ffmpeg)
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def parse_time(t):
    """'00:01:23', '1:23', '83', '83.5', SRT식 '00:01:23,456' 모두 초 단위 숫자로 변환."""
    t = str(t).strip().replace(",", ".")
    if re.fullmatch(r"[\d.]+", t):
        return float(t)
    parts = t.split(":")
    parts = [float(p) for p in parts]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    h, m, s = parts
    return h * 3600 + m * 60 + s


def safe_name(text, fallback):
    text = re.sub(r'[\\/:*?"<>|\s]+', "_", str(text)).strip("_")
    return text[:40] if text else fallback


def main():
    parser = argparse.ArgumentParser(description="롱폼에서 쇼츠 클립 잘라내기")
    parser.add_argument("video", help="원본 영상 파일 경로")
    parser.add_argument("segments", nargs="*", help="구간 목록 (예: 00:01:23-00:02:10)")
    parser.add_argument("--json", dest="json_file", help="구간 목록 JSON 파일 경로")
    parser.add_argument("--vertical", action="store_true", help="세로 9:16(1080x1920)로 크롭")
    parser.add_argument("--output-dir", default="channel/output/shorts", help="클립 저장 폴더")
    args = parser.parse_args()

    video = Path(args.video)
    if not video.exists():
        sys.exit(f"❌ 파일을 찾을 수 없습니다: {video}")
    if shutil.which("ffmpeg") is None:
        sys.exit("❌ ffmpeg가 설치되어 있지 않습니다. 클로드에게 'ffmpeg 설치해줘'라고 하세요.")

    clips = []
    if args.json_file:
        data = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
        for item in data:
            clips.append((parse_time(item["start"]), parse_time(item["end"]), item.get("title", "")))
    for seg in args.segments:
        if "-" not in seg:
            sys.exit(f"❌ 구간 형식이 잘못됐습니다: {seg} (예: 00:01:23-00:02:10)")
        start, end = seg.split("-", 1)
        clips.append((parse_time(start), parse_time(end), ""))

    if not clips:
        sys.exit("❌ 잘라낼 구간이 없습니다. 구간을 직접 넘기거나 --json 파일을 지정해 주세요.")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, (start, end, title) in enumerate(clips, 1):
        if end <= start:
            print(f"⚠️ {i}번 구간은 끝이 시작보다 빨라서 건너뜁니다.")
            continue
        name = safe_name(title, f"shorts_{i:02d}")
        output = out_dir / f"{i:02d}_{name}.mp4"
        length = end - start
        print(f"✂️ [{i}/{len(clips)}] {output.name} ({length:.0f}초) 만드는 중…")

        cmd = ["ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", str(video), "-t", f"{length:.3f}"]
        if args.vertical:
            cmd += ["-vf", "crop=ih*9/16:ih,scale=1080:1920"]
        cmd += ["-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-c:a", "aac", "-b:a", "192k", str(output)]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ {i}번 클립 생성 실패:\n{result.stderr[-300:]}")
        else:
            print(f"   ✅ {output}")

    print(f"\n완료! 클립 저장 폴더: {out_dir}")
    if not args.vertical:
        print("💡 세로 화면 쇼츠로 만들려면 --vertical 옵션을 추가하세요.")


if __name__ == "__main__":
    main()
