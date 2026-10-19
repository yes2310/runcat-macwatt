# RunCat Neo × macwatt

[English](README.md) | **한국어**

[RunCat Neo](https://github.com/runcat-dev/RunCatNeo) 대시보드에 MacBook의 실시간 충전·전력 정보를 보여주는 **전력** 카드를 추가합니다. 메뉴 막대에는 고양이만 그대로 남습니다.

```text
⚡ 전력
   입력 전력      86.1 W
   배터리        충전 67.5 W
   시스템 소비    18.6 W
   충전기        140 W · 28 V / 5 A
```

> 위 수치는 예시입니다.

---

## 시작하기 전에

- **Apple Silicon MacBook** (M1 이상)
- **RunCat Neo** 설치
- **Python 3.8 이상** — 터미널에서 `python3 --version`으로 확인

---

## 설치 및 적용

### 1단계 — 설치

**터미널**을 열고 아래 블록을 통째로 붙여넣으세요.

```bash
cd ~/Downloads
curl -LO https://github.com/yes2310/runcat-macwatt/releases/download/v1.0.0/runcat-macwatt-v1.0.0.zip
unzip -o runcat-macwatt-v1.0.0.zip
cd runcat-macwatt
bash install.sh
```

**`Installed!`** 가 보이면 끝입니다. 이제 백그라운드에서 동작하고, 로그인할 때마다 자동으로 실행됩니다.

<details>
<summary>직접 다운로드하고 싶다면</summary>

1. [Releases 페이지](https://github.com/yes2310/runcat-macwatt/releases/latest)에서 `runcat-macwatt-v1.0.0.zip`을 받습니다.
2. 더블클릭해 압축을 풉니다 (Safari는 자동으로 풀어주기도 합니다).
3. 터미널에서:
   ```bash
   cd ~/Downloads/runcat-macwatt
   bash install.sh
   ```

</details>

### 2단계 — RunCat Neo에 추가

1. **메뉴 막대의 고양이**를 클릭해 대시보드를 열고 **설정(Settings)** 으로 들어갑니다.
2. **Metrics → Custom Metrics** 에서 **Add Custom Metrics Source** 를 누릅니다.
3. 파일 선택 창에서 **`Command + Shift + G`** 를 누르고 아래 경로를 붙여넣은 뒤 **Return**, 그다음 **열기(Open)** 를 누릅니다.

```text
~/.config/runcat-neo-metrics/macbook-power.json
```

### 3단계 — 확인

메뉴 막대의 고양이를 클릭하세요. 대시보드에 **⚡ 전력** 카드가 보이고 자동으로 갱신됩니다.

> **메뉴 막대를 고양이만으로 유지하려면:** 새 소스는 RunCat의 *Metrics Bar*에서 기본적으로 숨겨져 있습니다. 여기서 이 소스를 켜지 않은 상태로 두세요.

---

## 업데이트

새 버전을 받아 `bash install.sh`를 다시 실행하면 됩니다. 파일 경로가 그대로라 RunCat에서 다시 설정할 필요는 없습니다.

## 제거

1. RunCat Neo → **Settings → Metrics → Custom Metrics** 에서 `macbook-power.json` 소스를 제거합니다.
2. 압축을 푼 폴더에서:
   ```bash
   bash uninstall.sh
   ```

---

## 문제 해결

먼저 압축을 푼 폴더에서 현재 상태를 확인하세요.

```bash
bash status.sh
```

| 증상 | 해결 |
| --- | --- |
| 설치 중 *power telemetry is not available* 로 멈춤 | 이 Mac은 필요한 전력 센서를 제공하지 않습니다. 추정값으로 대신하지 않습니다. |
| `python3` 이 없음 / 버전이 낮음 | Python 3.8 이상을 설치한 뒤 `bash install.sh`를 다시 실행하세요. |
| 카드가 안 보임 | 2단계를 했는지, 경로가 위와 정확히 같은지 확인하세요. |
| 카드에 `측정 불가` 표시 | 센서 읽기가 연속 3번 실패한 상태입니다. 보통 저절로 회복되며, 아니면 `bash status.sh`로 확인하세요. |
| 배터리에 `갱신 대기` 표시 | 충전기를 뽑은 직후 정상 동작입니다. macOS가 값을 새로 고칠 때까지 잠시 기다리세요. |
| macOS나 Homebrew Python 업데이트 후 갱신이 멈춤 | `bash install.sh`를 다시 실행하세요. |

로그 파일은 `~/.local/share/runcat-macwatt/` 에 있습니다 (`last-error.txt`, `service-error.log`).

---

## 작동 방식

<details>
<summary>자세히</summary>

- 작은 백그라운드 서비스(`launchd`, 이름 `dev.runcat.macwatt`)가 [macwatt](https://github.com/ytomasch/macwatt)로 Mac의 전력 센서를 **5초마다** 읽습니다.
- **표시되는 값이 바뀔 때만** JSON 파일을 다시 쓰고, RunCat Neo는 파일이 바뀌면 카드를 갱신합니다.
- macOS 자체의 센서 갱신은 5초보다 느릴 수 있습니다.
- **충전기** 값은 Mac과 어댑터가 협상한 전력 사양입니다. 브랜드·모델명이나 콘센트 실측값이 아닙니다.
- `sudo`, 인터넷, 추가 설치가 필요 없습니다. 필요한 건 모두 ZIP에 들어 있습니다.

설치되는 파일:

| 항목 | 위치 |
| --- | --- |
| 프로그램 | `~/.local/share/runcat-macwatt/` |
| 카드 데이터 (JSON) | `~/.config/runcat-neo-metrics/macbook-power.json` |
| 로그인 서비스 | `~/Library/LaunchAgents/dev.runcat.macwatt.plist` |

</details>

## 개발

```bash
bash scripts/test.sh
```

오프라인 유닛 테스트를 실행하고 `dist/`에 릴리스 ZIP을 만듭니다. [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.

## 라이선스

- 이 프로젝트: [MIT](LICENSE) © 2026 yes2310
- 포함된 **macwatt**: MIT © 2026 Amur Labs LLC — [라이선스](third_party/macwatt/LICENSE), [고지](THIRD_PARTY_NOTICES.md) 참고
- RunCat Neo는 별도 앱이며 포함되어 있지 않습니다.

*비공식 연동입니다. RunCat Neo, macwatt와 관련이 없습니다.*
