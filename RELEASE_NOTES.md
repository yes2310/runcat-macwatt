# v1.0.0 — Initial public release

An unofficial open-source integration that shows Apple Silicon MacBook power information as a RunCat Neo Custom Metric.

- Input power, battery charge/discharge, system consumption and negotiated charger specs in a single **Power** card
- **Checks every 5 seconds** and rewrites the JSON only when values change
- No separate Metrics Bar value, so RunCat's menu bar shows **only the cat**
- macOS `launchd` agent that starts automatically at login
- Upgrades from v2/v3 keep the same JSON path
- Install ZIP bundles the MIT-licensed macwatt source for offline installation
- Install, uninstall and status scripts plus offline tests

### Requirements

Apple Silicon MacBook with `PowerTelemetryData`, RunCat Neo Custom Metrics, Python 3.8+.

### Notes

Underlying power samples may update more slowly than the 5-second polling interval. Adapter figures are negotiated values, not wall power measurements. Neither RunCat Neo nor macwatt officially maintains this integration.

---

<details>
<summary>한국어</summary>

RunCat Neo의 사용자 정의 메트릭으로 Apple Silicon MacBook의 전력 정보를 표시하는 비공식 오픈소스 연동입니다.

- 입력 전력, 배터리 충·방전, 시스템 소비, 충전기 협상 사양을 **전력** 카드 하나로 표시
- **5초마다 확인**, 값이 달라질 때만 JSON 갱신
- RunCat 메뉴 막대에는 **고양이만** 표시하도록 별도 Metrics Bar 값을 넣지 않음
- 로그인 시 자동 실행하는 macOS `launchd` 서비스
- 기존 v2/v3 설치 시 JSON 경로를 유지하는 업그레이드
- 설치 ZIP에 MIT 라이선스 macwatt 소스를 포함하여 오프라인 설치 지원
- 설치·제거·상태 확인 스크립트 및 오프라인 테스트 포함

**요구 사항:** `PowerTelemetryData`를 제공하는 Apple Silicon MacBook, RunCat Neo 사용자 정의 메트릭, Python 3.8 이상.

**참고:** 실제 전력 샘플은 5초 조회 주기보다 느리게 갱신될 수 있습니다. 충전기 수치는 협상된 값이며 콘센트 실측 전력이 아닙니다. RunCat Neo와 macwatt 어느 쪽도 이 연동을 공식 관리하지 않습니다.

</details>
