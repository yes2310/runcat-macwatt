# v1.0.0 — Initial public release

RunCat Neo의 사용자 정의 메트릭으로 Apple Silicon MacBook의 전력 정보를 표시하는 비공식 오픈소스 연동입니다.

- 입력 전력, 배터리 충·방전, 시스템 소비, 충전기 협상 사양을 **전력** 카드 하나로 표시
- **5초마다 확인**, 값이 달라질 때만 JSON 갱신
- RunCat 메뉴 막대에는 **고양이만** 표시하도록 별도 Metrics Bar 값을 넣지 않음
- 로그인 시 자동 실행하는 macOS `launchd` 서비스
- 기존 v2/v3 설치 시 JSON 경로를 유지하는 업그레이드
- 설치 ZIP에 MIT 라이선스 macwatt 소스를 포함하여 오프라인 설치 지원
- 설치·제거·상태 확인 스크립트 및 오프라인 테스트 포함

### Requirements

Apple Silicon MacBook with `PowerTelemetryData`, RunCat Neo Custom Metrics, Python 3.8+.

### Notes

Underlying power samples may update more slowly than the 5-second polling interval. Adapter figures are negotiated values, not wall power measurements. Neither RunCat Neo nor macwatt officially maintains this integration.
