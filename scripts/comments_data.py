#!/usr/bin/env python3
"""유튜브 영상의 댓글(답글 포함)을 CSV로 추출합니다.

사용 예시:
    python3 scripts/comments_data.py https://www.youtube.com/watch?v=XXXXXXXXXXX
    python3 scripts/comments_data.py <영상URL> --limit 500 --sort new

필요한 도구: yt-dlp  (설치: pip install yt-dlp)
API 키는 필요 없습니다.
"""

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def format_date(timestamp):
    if not timestamp:
        return ""
    return datetime.fromtimestamp(int(timestamp), tz=timezone.utc).strftime("%Y-%m-%d")


def run_ytdlp(url, limit, sort):
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--dump-single-json",
        "--write-comments",
        "--no-warnings",
        "--extractor-args",
        f"youtube:comment_sort={sort};max_comments={limit},all,{limit},10",
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        sys.exit(
            "❌ yt-dlp가 설치되어 있지 않습니다.\n"
            "   설치: pip install yt-dlp  (또는 pip3 install yt-dlp)\n"
            "   클로드에게 'yt-dlp 설치해줘'라고 해도 됩니다."
        )
    except subprocess.CalledProcessError as e:
        sys.exit(f"❌ 영상 정보를 가져오지 못했습니다. 영상 주소를 확인해 주세요.\n{e.stderr[-500:]}")

    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description="유튜브 영상 댓글을 CSV로 추출")
    parser.add_argument("url", help="영상 주소 (예: https://www.youtube.com/watch?v=...)")
    parser.add_argument("--limit", type=int, default=200,
                        help="가져올 댓글 수, 답글 포함 (기본: 200)")
    parser.add_argument("--sort", choices=["top", "new"], default="top",
                        help="정렬 기준: top(인기순, 기본) / new(최신순)")
    parser.add_argument("--output", default=None,
                        help="저장할 CSV 경로 (기본: channel/output/comments/<영상ID>.csv)")
    args = parser.parse_args()

    print("📡 댓글을 가져오는 중… (댓글이 많으면 몇 분 걸릴 수 있어요)")
    data = run_ytdlp(args.url, args.limit, args.sort)

    video_id = data.get("id", "video")
    title = data.get("title", "")
    comments = data.get("comments") or []
    if not comments:
        sys.exit("❌ 댓글을 찾지 못했습니다. 댓글이 없거나 댓글 기능이 꺼진 영상일 수 있어요.")

    # 원댓글과 답글을 나누고, 답글은 원댓글 아래에 붙인다
    parents = [c for c in comments if c.get("parent", "root") == "root"]
    replies = {}
    for c in comments:
        parent_id = c.get("parent", "root")
        if parent_id != "root":
            replies.setdefault(parent_id, []).append(c)

    parents.sort(key=lambda c: c.get("like_count") or 0, reverse=True)

    def to_row(c, kind, reply_count=""):
        return {
            "종류": kind,
            "작성자": c.get("author", ""),
            "내용": (c.get("text") or "").replace("\n", " ").strip(),
            "좋아요": c.get("like_count") or 0,
            "답글수": reply_count,
            "작성일(대략)": format_date(c.get("timestamp")) or c.get("_time_text") or "",
            "제작자하트": "❤" if c.get("is_favorited") else "",
            "채널주인": "본인" if c.get("author_is_uploader") else "",
        }

    rows = []
    for p in parents:
        kids = sorted(replies.get(p.get("id", ""), []),
                      key=lambda c: c.get("like_count") or 0, reverse=True)
        rows.append(to_row(p, "댓글", len(kids)))
        rows.extend(to_row(r, "└답글") for r in kids)

    out = Path(args.output) if args.output else Path(f"channel/output/comments/{video_id}.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig: 엑셀에서 한글이 깨지지 않도록
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ 완료: 「{title}」 — 댓글 {len(parents)}개 + 답글 {len(rows) - len(parents)}개")
    print(f"   저장 위치: {out}")
    for c in parents[:3]:
        preview = (c.get("text") or "").replace("\n", " ")[:40]
        print(f"   👍{c.get('like_count') or 0:,}  {preview}")


if __name__ == "__main__":
    main()
