#!/usr/bin/env python3
"""영상에서 무음 구간을 자동 감지해 컷편집용 타임코드 목록을 만듭니다.
--cut 옵션을 주면 무음 구간을 실제로 잘라낸 영상까지 만들어 줍니다.

사용 예시:
    python3 scripts/silence_detect.py 내영상.mp4
    python3 scripts/silence_detect.py 내영상.mp4 --cut channel/output/편집본.mp4
    python3 scripts/silence_detect.py 내영상.mp4 --noise -30 --min-silence 1.0

필요한 도구: ffmpeg (macOS: brew install ffmpeg / Windows: winget install ffmpeg)
"""

import argparse
import csv
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def check_ffmpeg():
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        sys.exit(
            "❌ ffmpeg가 설치되어 있지 않습니다.\n"
            "   macOS: brew install ffmpeg / Windows: winget install ffmpeg\n"
            "   클로드에게 'ffmpeg 설치해줘'라고 해도 됩니다."
        )


def timecode(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def get_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def detect_silences(path, noise_db, min_silence):
    print(f"🔍 무음 구간 감지 중… (기준: {noise_db}dB 이하가 {min_silence}초 이상)")
    result = subprocess.run(
        ["ffmpeg", "-i", str(path),
         "-af", f"silencedetect=noise={noise_db}dB:d={min_silence}",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    log = result.stderr
    starts = [float(x) for x in re.findall(r"silence_start:\s*([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([\d.]+)", log)]
    # 영상 끝까지 무음이면 silence_end가 없을 수 있음
    silences = list(zip(starts, ends))
    if len(starts) > len(ends):
        silences.append((starts[-1], None))
    return silences


def build_keep_segments(silences, total, padding):
    """무음의 반대 구간(살릴 구간)을 계산. padding만큼 무음을 남겨 말이 뚝 끊기지 않게 한다."""
    keep = []
    cursor = 0.0
    for start, end in silences:
        seg_end = min(start + padding, total)
        if seg_end - cursor > 0.05:
            keep.append((cursor, seg_end))
        cursor = (end - padding) if end is not None else total
        cursor = max(cursor, 0.0)
    if total - cursor > 0.05:
        keep.append((cursor, total))
    return keep


def cut_video(path, keep, output):
    print(f"✂️ 무음 구간을 잘라낸 영상을 만드는 중… ({len(keep)}개 구간 이어붙이기)")
    parts_v, parts_a, lines = [], [], []
    for i, (s, e) in enumerate(keep):
        lines.append(f"[0:v]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS[v{i}];")
        lines.append(f"[0:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS[a{i}];")
        parts_v.append(f"[v{i}]")
        parts_a.append(f"[a{i}]")
    pairs = "".join(f"{v}{a}" for v, a in zip(parts_v, parts_a))
    lines.append(f"{pairs}concat=n={len(keep)}:v=1:a=1[outv][outa]")

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("\n".join(lines))
        script_path = f.name

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(path),
         "-filter_complex_script", script_path,
         "-map", "[outv]", "-map", "[outa]",
         "-c:v", "libx264", "-preset", "fast", "-crf", "20",
         "-c:a", "aac", "-b:a", "192k",
         str(output)],
    )
    if result.returncode != 0:
        sys.exit("❌ 컷편집 영상 생성에 실패했습니다. 위 에러를 클로드에게 보여주세요.")
    print(f"✅ 컷편집 완료: {output}")


def main():
    parser = argparse.ArgumentParser(description="무음 구간 감지 → 컷편집 타임코드 / 자동 컷")
    parser.add_argument("video", help="영상 파일 경로")
    parser.add_argument("--noise", type=float, default=-35, help="무음 판정 기준 dB (기본: -35)")
    parser.add_argument("--min-silence", type=float, default=0.7, help="이 길이(초) 이상 조용하면 무음 (기본: 0.7)")
    parser.add_argument("--padding", type=float, default=0.15, help="무음 앞뒤로 남길 여유(초) (기본: 0.15)")
    parser.add_argument("--csv", default="channel/output/silences.csv", help="타임코드 목록 CSV 저장 경로")
    parser.add_argument("--cut", metavar="출력파일.mp4", help="무음을 잘라낸 영상을 이 경로로 생성")
    args = parser.parse_args()

    video = Path(args.video)
    if not video.exists():
        sys.exit(f"❌ 파일을 찾을 수 없습니다: {video}")
    check_ffmpeg()

    total = get_duration(video)
    silences = detect_silences(video, args.noise, args.min_silence)

    if not silences:
        print("✅ 감지된 무음 구간이 없습니다. (--noise 값을 -30으로 올려서 다시 시도해 보세요)")
        return

    keep = build_keep_segments(silences, total, args.padding)
    silence_total = sum((e or total) - s for s, e in silences)

    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["구간", "시작", "끝", "길이(초)"])
        for s, e in silences:
            e = e if e is not None else total
            writer.writerow(["무음(잘라낼 곳)", timecode(s), timecode(e), f"{e - s:.2f}"])

    print(f"✅ 무음 구간 {len(silences)}개 감지 (총 {silence_total:.1f}초 / 전체 {total:.1f}초)")
    print(f"   타임코드 목록: {csv_path}")
    print(f"   예상 편집 후 길이: {total - silence_total:.1f}초")

    if args.cut:
        cut_video(video, keep, args.cut)
    else:
        print("   💡 무음을 실제로 잘라내려면: --cut channel/output/편집본.mp4")


if __name__ == "__main__":
    main()
