#!/usr/bin/env python3
"""영상/음성 파일에서 Whisper로 자막(SRT)을 자동 생성합니다.

사용 예시:
    python3 scripts/whisper_subtitles.py 내영상.mp4
    python3 scripts/whisper_subtitles.py 내영상.mp4 --model medium --output-dir channel/output/subtitles

필요한 도구:
    ffmpeg   (macOS: brew install ffmpeg / Windows: winget install ffmpeg)
    whisper  (pip install openai-whisper)

모델 크기: tiny < base < small(기본) < medium < large
클수록 정확하지만 느립니다. 한국어는 medium 이상을 권장합니다.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def check_tool(name, install_hint):
    if shutil.which(name) is None:
        sys.exit(
            f"❌ {name}이(가) 설치되어 있지 않습니다.\n"
            f"   설치: {install_hint}\n"
            f"   클로드에게 '{name} 설치해줘'라고 해도 됩니다."
        )


def main():
    parser = argparse.ArgumentParser(description="Whisper로 자막(SRT) 자동 생성")
    parser.add_argument("media", help="영상 또는 음성 파일 경로")
    parser.add_argument("--model", default="small",
                        choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper 모델 크기 (기본: small, 한국어 권장: medium)")
    parser.add_argument("--language", default="ko", help="언어 코드 (기본: ko)")
    parser.add_argument("--output-dir", default="channel/output/subtitles",
                        help="SRT 저장 폴더 (기본: channel/output/subtitles)")
    args = parser.parse_args()

    media = Path(args.media)
    if not media.exists():
        sys.exit(f"❌ 파일을 찾을 수 없습니다: {media}")

    check_tool("ffmpeg", "macOS는 brew install ffmpeg, Windows는 winget install ffmpeg")
    check_tool("whisper", "pip install openai-whisper")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"🎙️ 음성 분석 중… (모델: {args.model}, 언어: {args.language})")
    print("   영상 길이에 따라 몇 분 정도 걸릴 수 있습니다. 처음 실행 시 모델 다운로드로 더 걸립니다.")

    cmd = [
        "whisper", str(media),
        "--model", args.model,
        "--language", args.language,
        "--output_format", "srt",
        "--output_dir", str(out_dir),
        "--verbose", "False",
    ]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit("❌ 자막 생성에 실패했습니다. 위 에러 메시지를 클로드에게 보여주세요.")

    srt_path = out_dir / (media.stem + ".srt")
    print(f"✅ 자막 생성 완료: {srt_path}")
    print("   💡 팁: 클로드에게 '이 자막을 맥락 단위로 줄바꿈 다듬어줘' 또는")
    print("          '타임코드 그대로 영어 자막으로 번역해줘'라고 하면 후처리까지 됩니다.")


if __name__ == "__main__":
    main()
