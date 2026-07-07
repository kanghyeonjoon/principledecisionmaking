#!/usr/bin/env python3
"""유튜브 채널의 전체 영상 데이터(제목·조회수·길이·업로드일)를 CSV로 추출합니다.

사용 예시:
    python3 scripts/channel_data.py https://www.youtube.com/@채널핸들
    python3 scripts/channel_data.py <채널URL> --limit 30 --output channel/competitor_A.csv

필요한 도구: yt-dlp  (설치: pip install yt-dlp)
API 키는 필요 없습니다.
"""

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


def format_duration(seconds):
    if seconds is None:
        return ""
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def normalize_channel_url(url):
    """채널 대문 주소가 들어와도 /videos 탭을 보도록 정리한다."""
    url = url.rstrip("/")
    known_tabs = ("/videos", "/shorts", "/streams", "/playlists")
    if url.endswith(known_tabs):
        return url
    if "/watch" in url or "/playlist" in url:
        return url
    return url + "/videos"


def run_ytdlp(url, limit):
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-single-json",
        "--extractor-args", "youtubetab:approximate_date",
        "--no-warnings",
    ]
    if limit:
        cmd += ["--playlist-end", str(limit)]
    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        sys.exit(
            "❌ yt-dlp가 설치되어 있지 않습니다.\n"
            "   설치: pip install yt-dlp  (또는 pip3 install yt-dlp)\n"
            "   클로드에게 'yt-dlp 설치해줘'라고 해도 됩니다."
        )
    except subprocess.CalledProcessError as e:
        sys.exit(f"❌ 채널 정보를 가져오지 못했습니다. 채널 주소를 확인해 주세요.\n{e.stderr[-500:]}")

    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description="유튜브 채널 전체 영상 데이터를 CSV로 추출")
    parser.add_argument("url", help="채널 주소 (예: https://www.youtube.com/@핸들)")
    parser.add_argument("--limit", type=int, default=None, help="최근 N개만 추출 (기본: 전체)")
    parser.add_argument("--output", default="channel/videos.csv", help="저장할 CSV 경로 (기본: channel/videos.csv)")
    parser.add_argument("--sort", choices=["views", "date"], default="views",
                        help="정렬 기준: views(조회수순, 기본) / date(최신순)")
    args = parser.parse_args()

    url = normalize_channel_url(args.url)
    print(f"📡 채널 데이터를 가져오는 중… ({url})")
    data = run_ytdlp(url, args.limit)

    channel_name = data.get("channel") or data.get("uploader") or data.get("title", "")
    entries = [e for e in (data.get("entries") or []) if e]
    if not entries:
        sys.exit("❌ 영상을 찾지 못했습니다. 채널 주소가 맞는지 확인해 주세요.")

    rows = []
    for e in entries:
        upload_date = e.get("upload_date") or ""
        if len(upload_date) == 8:  # YYYYMMDD → YYYY-MM-DD
            upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
        rows.append({
            "제목": e.get("title", ""),
            "조회수": e.get("view_count") or 0,
            "길이": format_duration(e.get("duration")),
            "길이_초": int(e["duration"]) if e.get("duration") else "",
            "업로드일(대략)": upload_date,
            "URL": e.get("url") or f"https://www.youtube.com/watch?v={e.get('id', '')}",
            "영상ID": e.get("id", ""),
        })

    if args.sort == "views":
        rows.sort(key=lambda r: r["조회수"], reverse=True)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig: 엑셀에서 한글이 깨지지 않도록
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    total_views = sum(r["조회수"] for r in rows)
    print(f"✅ 완료: {channel_name} — 영상 {len(rows)}개, 총 조회수 {total_views:,}회")
    print(f"   저장 위치: {out}")
    print(f"   TOP 3: " + " / ".join(f"「{r['제목']}」({r['조회수']:,}회)" for r in rows[:3]))


if __name__ == "__main__":
    main()
