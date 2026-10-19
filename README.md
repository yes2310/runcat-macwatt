# RunCat Neo × macwatt

**RunCat Neo용 MacBook 충전·전력 메트릭** — 메뉴 막대에는 고양이만 두고, RunCat 대시보드에서 필요한 전력만 확인하세요.

An unofficial, offline-installable Custom Metrics integration powered by [macwatt](https://github.com/ytomasch/macwatt). [English README](README_EN.md).

## 화면에 표시되는 항목

| 항목 | 표시 예시 | 설명 |
| --- | --- | --- |
| 입력 전력 | `86.1 W` | 충전기에서 Mac으로 들어오는 측정 전력 |
| 배터리 | `충전 67.5 W` / `방전 18.6 W` | 배터리로 들어가거나 나오는 전력 |
| 시스템 소비 | `18.6 W` | 시스템 소비 전력 |
| 충전기 | `140 W · 28 V / 5 A` | Mac에서 읽힌 **협상된** 충전기 사양 |

> 예시 수치입니다. 충전기 사양은 브랜드·모델명이나 콘센트 실측 소비전력이 아닙니다. Apple의 비공개 전력 텔레메트리에 의존하므로 Mac/OS에 따라 일부 값이 없거나 늦게 갱신될 수 있습니다.

카드 제목은 **전력**이고, 메뉴 막대에 전력 숫자는 추가하지 않습니다. RunCat Neo의 **Metrics Bar**가 켜져 있다면 꺼두거나 해당 소스를 숨겨야 고양이만 남습니다.

## 요구 사항

- **Apple Silicon MacBook** + `AppleSmartBattery`의 `PowerTelemetryData` 제공 (설치 전 자동 검사)
- [RunCat Neo](https://github.com/runcat-dev/RunCatNeo) (사용자 정의 메트릭 지원 버전)
- `python3` **3.8 이상**, 표준 라이브러리만 사용
- macOS 사용자 세션에서 실행 (`sudo` 불필요)

설치 중 인터넷 연결은 **필요하지 않습니다**. `macwatt.py`와 MIT 라이선스를 설치 ZIP에 포함했습니다. 실행 중에도 네트워크 연결이나 계정 권한을 요청하지 않습니다.

## 설치

GitHub Releases에서 `runcat-macwatt-v1.0.0.zip`을 다운로드하고 압축 해제한 뒤:

```bash
cd ~/Downloads/runcat-macwatt
bash install.sh
```

> 다른 경로에 압축을 풀었다면 그 폴더로 이동해 `bash install.sh`를 실행하세요.

설치가 완료되면 RunCat Neo에서 **Settings → Metrics → Custom Metrics → Add Custom Metrics Source**를 열고 다음 파일을 추가합니다.

```text
~/.config/runcat-neo-metrics/macbook-power.json
```

파일 선택 창에서 `Command + Shift + G`로 경로를 입력할 수 있습니다. **Metrics Bar는 비활성화**하면 메뉴 막대에는 고양이만 표시됩니다.

### 기존 v2/v3 사용자

동일한 `bash install.sh` 명령어로 업그레이드합니다. 기존 `dev.runcat.macwatt` 서비스를 중지한 후 새 프로그램으로 다시 등록합니다. 메트릭 JSON의 **경로가 동일하므로 RunCat에 다시 추가할 필요는 없습니다.** 설치 전 실측 데이터 검사를 수행하고, 설치 실패 시 이전 설치를 복원하도록 시도합니다.

## 작동 방식

1. macOS `launchd`가 로그인 시 **Python 상주 프로세스 하나**를 실행합니다.
2. [macwatt](https://github.com/ytomasch/macwatt)가 `ioreg`의 전력 텔레메트리를 **5초마다 조회**합니다.
3. 표시 내용이 바뀌었을 때만 RunCat용 JSON 파일을 **원자적으로 교체**합니다.
4. RunCat Neo가 파일 변경을 감지해 사용자 정의 메트릭 카드를 갱신합니다.

**5초마다 새 센서 샘플이 생긴다는 뜻은 아닙니다.** 실제 macOS 센서 데이터 갱신 주기는 환경에 따라 훨씬 길 수 있습니다. 분리 직후 배터리 충전 표시가 잠시 오래된 상태라면 `갱신 대기`로 표시하며, 전원 미연결 시 충전기 입력은 `0.0 W`로 표시합니다. 읽기 실패가 반복되면 카드는 `측정 불가`로 바뀌고 회복 시 자동 갱신됩니다.

이 프로그램은 별도 그래픽 앱이 아니라 RunCat용 로컬 JSON 데이터를 만드는 백그라운드 도구입니다.

## 상태 확인 / 문제 해결

압축을 해제한 폴더에서:

```bash
bash status.sh
```

또는 직접 확인:

```bash
python3 -m json.tool ~/.config/runcat-neo-metrics/macbook-power.json
python3 ~/.local/share/runcat-macwatt/power_metrics.py --check
launchctl print "gui/$(id -u)/dev.runcat.macwatt"
```

로그 파일:

```text
~/.local/share/runcat-macwatt/last-error.txt
~/.local/share/runcat-macwatt/service-error.log
```

- `측정 불가` / 설치 시 telemetry unavailable: 해당 Mac에 `PowerTelemetryData`가 노출되는지 확인하세요. 다른 센서를 추정치로 대체하지 않습니다.
- `python3 not found`: Python 3.8 이상을 설치하고 다시 실행하세요.
- RunCat에 카드가 보이지 않음: 파일 경로와 RunCat의 Custom Metrics 등록 여부를 확인하세요.
- macOS 또는 Homebrew Python을 변경한 뒤 자동 갱신되지 않음: `bash install.sh`를 다시 실행해 launchd의 Python 경로를 갱신하세요.

## 제거

RunCat 설정에서 해당 Custom Metrics 소스를 제거한 다음:

```bash
bash uninstall.sh
```

설치된 코드·서비스·해당 JSON만 제거하고 다른 RunCat 메트릭에는 영향을 주지 않습니다.

## 개발 및 테스트

```bash
bash scripts/test.sh
```

macOS 센서 없이도 실행되는 유닛 테스트, Bash 문법 검사, 릴리스 ZIP 무결성 검사를 수행합니다. 설치 ZIP은 `dist/runcat-macwatt-v1.0.0.zip`에, SHA-256 검증 파일은 `dist/SHA256SUMS.txt`에 생성됩니다. GitHub 공개 방법은 [PUBLISH_WITH_CLAUDE.md](PUBLISH_WITH_CLAUDE.md) 및 [CLAUDE.md](CLAUDE.md)를 참고하세요.

## 오픈소스 · 저작권

- 이 RunCat 연동 코드와 설치 스크립트: [MIT License](LICENSE) · Copyright (c) 2026 yes2310
- **macwatt**: Copyright (c) 2026 Amur Labs LLC, MIT License — 반드시 [원본 라이선스](third_party/macwatt/LICENSE)와 [고지](THIRD_PARTY_NOTICES.md)를 유지하세요.
- **RunCat Neo**: 별도 프로젝트입니다. 앱 자체는 재배포하지 않습니다. [Custom Metrics JSON Schema](https://github.com/runcat-dev/RunCatNeo/blob/main/docs/CustomMetricsSchema.md)

*Unofficial integration. Not affiliated with or endorsed by RunCat Neo or macwatt.*
