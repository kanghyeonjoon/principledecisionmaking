---
name: channel-analysis
description: 내 유튜브 채널 전체 영상 데이터를 추출하고 잘된 영상의 썸네일·제목·대본 패턴을 분석해 성공 공식(channel/FORMULA.md)을 만듭니다. "내 채널 분석해줘" 할 때 사용.
---

# 내 채널 분석

감이 아니라 데이터로. 내 채널에서 잘된 영상의 공통 패턴을 추출해 `channel/FORMULA.md`로 저장한다.

## 진행 순서

1. **데이터 추출**: 사용자에게 채널 URL을 받아 실행:
   ```
   python3 scripts/channel_data.py <채널URL> --output channel/videos.csv
   ```
   yt-dlp가 없으면 설치해 준다 (`pip install yt-dlp`).

2. **CSV 읽고 전체 현황 브리핑**: `channel/videos.csv`를 읽고 요약한다.
   - 전체 영상 수, 총/평균 조회수
   - 조회수 TOP 10 표
   - 최근 10개 영상 성과 (평균 대비 몇 %인지)
   - 길이별 성과 경향 (짧은 영상 vs 긴 영상)

3. **잘된 영상 심층 분석** (TOP 5 기준):
   - **썸네일**: 영상 ID로 썸네일 이미지를 내려받아 직접 본다.
     ```
     mkdir -p channel/output/thumbnails
     curl -sL "https://i.ytimg.com/vi/<영상ID>/maxresdefault.jpg" -o channel/output/thumbnails/<영상ID>.jpg
     ```
     (maxresdefault가 없으면 hqdefault로 재시도.) Read 도구로 이미지를 열어 문구·색·구도·인물 유무를 분석한다.
   - **제목**: TOP 영상들의 제목에서 공통 패턴 추출 (`templates/THUMBNAIL_FORMULAS.md`의 5대 심리 카테고리로 분류).
   - **대본**: 자동 자막을 받아 도입부 구조를 분석한다.
     ```
     yt-dlp --write-auto-subs --sub-langs ko --skip-download --convert-subs srt -o "channel/output/subs/%(id)s" <영상URL>
     ```
     첫 8초에 뭘 약속하는지, 전개 구조가 어떤지 본다.

4. **공식 정리**: 분석 결과를 `channel/FORMULA.md`로 저장한다. 구성:
   - 잘된 영상 TOP 5 요약표 (제목/조회수/썸네일 특징/제목 공식/도입부 패턴)
   - **썸네일 공식**: 이 채널에서 먹히는 문구 스타일·색·구도
   - **제목 공식**: 잘 터진 제목의 구조 (심리 카테고리 표시)
   - **대본 공식**: 도입 8초 → 약속 → 전개 → 마무리 패턴
   - **결론**: 다음 영상에 그대로 적용할 체크리스트 5줄

5. **마무리**: 핵심 발견 3가지를 브리핑하고 `/competitor-analysis`를 추천한다.

## 주의

- `channel/BRAND.md`가 있으면 먼저 읽고, 분석 결론이 브랜드 방향과 어긋나는 지점이 있으면 짚어준다.
- 영상이 10개 미만인 초기 채널이면 패턴 분석 대신 "지금은 데이터가 부족하니 경쟁/레퍼런스 채널 분석부터 하자"고 안내한다.
- 자동 자막이 없는 영상도 있다. 실패해도 에러로 멈추지 말고 있는 것만으로 분석한다.
