# 설치 가이드

클로드 코드에게 "설치 도와줘"라고 하면 아래 과정을 대신 해줍니다. 직접 하고 싶은 분을 위한 가이드입니다.

## 1. 클로드 코드 (필수)

Claude 유료 플랜(Pro 이상)이 필요합니다.

```bash
# macOS / Linux
npm install -g @anthropic-ai/claude-code

# 또는 공식 문서 참고: https://code.claude.com/docs
```

설치 후 이 리포지토리 폴더에서 `claude`를 실행하면 됩니다.

## 2. Python 3 (스크립트 실행용)

- **macOS**: 기본 설치되어 있습니다. `python3 --version`으로 확인.
- **Windows**: [python.org](https://www.python.org/downloads/)에서 설치 (설치 시 "Add to PATH" 체크).

## 3. yt-dlp — 채널 데이터 수집 (`/channel-analysis`, `/competitor-analysis`)

```bash
pip install yt-dlp
# 안 되면: pip3 install yt-dlp
```

유튜브 API 키 없이 채널의 공개 데이터를 가져오는 무료 오픈소스 도구입니다.

## 4. ffmpeg — 영상 처리 (`/cut-edit`, `/shorts`, `/subtitle`)

```bash
# macOS
brew install ffmpeg

# Windows
winget install ffmpeg
```

설치 확인: `ffmpeg -version`

## 5. Whisper — 자막 생성 (`/subtitle`)

```bash
pip install openai-whisper
```

- 브루(Vrew)가 쓰는 것과 같은 음성 인식 엔진입니다.
- 처음 실행할 때 모델 파일을 다운로드해서 몇 분 걸립니다.
- 한국어 자막은 `medium` 모델을 권장합니다 (기본은 `small`).

## 문제가 생기면

에러 메시지를 그대로 복사해서 클로드에게 붙여넣으세요. 원인을 설명하고 해결해 줍니다.

| 증상 | 해결 |
|---|---|
| `command not found: pip` | `pip3`로 시도, 그래도 안 되면 Python 재설치 |
| `command not found: brew` (macOS) | [brew.sh](https://brew.sh) 안내대로 Homebrew 먼저 설치 |
| whisper가 너무 느림 | `--model small`이나 `tiny`로 낮추기 (정확도는 떨어짐) |
| yt-dlp가 채널을 못 가져옴 | `pip install -U yt-dlp`로 최신 버전 업데이트 |
