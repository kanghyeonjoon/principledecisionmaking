# 유튜브 크리에이터 툴킷 — 클로드 작업 지침

이 리포지토리는 유튜브 크리에이터가 클로드 코드로 채널 운영을 자동화하는 툴킷입니다.
사용자는 대부분 **개발 지식이 없는 크리에이터**입니다.

## 기본 원칙

- **항상 한국어로** 대답한다. 기술 용어는 쉬운 말로 풀어서 설명한다.
- 에러가 나면 원인을 개발자 용어가 아니라 일반인이 이해할 수 있는 말로 설명하고, 해결을 직접 해준다.
- 사용자의 톤과 브랜드를 최우선으로 한다. 산출물을 만들기 전에 `channel/BRAND.md`가 있으면 반드시 먼저 읽는다.
- 산출물(기획안, 대본, 분석 등)은 반드시 파일로 저장한다. 채팅으로만 보여주고 끝내지 않는다.

## 파일 규칙

모든 사용자 데이터는 `channel/` 폴더에 저장한다 (gitignore 됨):

| 파일 | 내용 | 만드는 스킬 |
|---|---|---|
| `channel/BRAND.md` | 브랜드 문서 (모든 작업의 기준) | /brand-doc |
| `channel/videos.csv` | 내 채널 전체 영상 데이터 | /channel-analysis |
| `channel/FORMULA.md` | 잘된 영상의 썸네일·제목·대본 공식 | /channel-analysis |
| `channel/COMPETITORS.md` | 경쟁 채널 분석 + 갭 분석 | /competitor-analysis |
| `channel/SCRIPT_STRUCTURE.md` | 대본 공통 골격 | /script |
| `channel/CALENDAR.md` | 발행 캘린더 | /schedule |
| `channel/plans/YYYY-MM-DD-주제.md` | 영상별 기획안 | /video-plan |
| `channel/plans/YYYY-MM-DD-주제-답변.md` | 인터뷰 질문 답변 원문 (대본 재료, 다듬지 않고 보존) | /script |
| `channel/plans/YYYY-MM-DD-주제-대본.md` | 완성 대본 | /script |
| `channel/output/` | 자막(SRT), 쇼츠 클립, 썸네일 이미지 등 산출물 | 각 스킬 |

폴더가 없으면 `mkdir -p`로 만들고 진행한다.

## 스크립트 사용법

`scripts/` 폴더의 파이썬 스크립트는 모두 `python3 scripts/<이름>.py --help`로 사용법을 확인할 수 있다.

- `channel_data.py` — 채널 URL → 전체 영상 메타데이터 CSV (yt-dlp 필요)
- `whisper_subtitles.py` — 영상/음성 → SRT 자막 (whisper, ffmpeg 필요)
- `silence_detect.py` — 영상 → 무음 구간 타임코드 목록, `--cut`으로 자동 컷편집 (ffmpeg 필요)
- `shorts_cut.py` — 영상 + 타임코드 → 쇼츠 클립 추출, `--vertical`로 9:16 크롭 (ffmpeg 필요)
- `script_timer.py` — 대본 파일 → 섹션별 글자수·예상 러닝타임·누적 타임코드 (설치 필요 없음)

필요한 도구(yt-dlp, ffmpeg, whisper)가 설치 안 되어 있으면 사용자에게 물어보고 직접 설치해 준다.
설치 명령은 `docs/INSTALL.md` 참고.

## 산출물 품질 기준

- 썸네일·제목 후보는 `templates/THUMBNAIL_FORMULAS.md`의 5대 심리 공식에 근거하고, 각 후보에 어떤 공식을 썼는지 표시한다.
- 기획안은 `templates/PLANNING_TEMPLATE.md` 양식을 따른다.
- 대본은 사용자의 기존 말투·톤을 유지한다. `channel/SCRIPT_STRUCTURE.md`와 `channel/BRAND.md`의 톤 정의를 따른다.
- 대본은 `templates/SCRIPT_TEMPLATE.md` 양식을 따르고, 저장 전에 `scripts/script_timer.py`로 러닝타임을 기획안의 예상 길이와 맞춘다.
- 일반론이 아니라 이 채널의 데이터(FORMULA.md, COMPETITORS.md)에 근거해서 제안한다.
