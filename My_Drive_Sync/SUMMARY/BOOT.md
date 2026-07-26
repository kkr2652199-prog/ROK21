# BOOT — 외부 AI 30초 복원 (kweon / R36)

## 0) 한 줄
4군 앱 + 테스트로또 + 효도로또(1.5군). SSOT=kweon main · 로컬 `D:\3kweon`.
1~3군은 memoy 관할 — 여기 기록 금지(R34). 앱 지도=SUMMARY/MAP.md

## 1) 현재 스레드 (매턴 3줄만 갱신)
- 지금: 테스트로또 UI 패치 커밋 (tier-wins 모달·적중요약·routes) push `22ac617`
- 직전: R36 인프라 BOOT/FINDINGS/hooks/rules/gitignore push `0a1a55c`
- 다음: K-00 4군 정밀분석 · per-draw fan-out · fetch-latest 수동복구

## 2) 숫자 (근거 없으면 미확인)
lotto_predictions=1,245행 / 83회차(1120~1232 일부) / stat·markov·review 각 415
stat 동적 WF(1132~1231, 회차별 seed) avg=1.75 · 고정 boost 0.5^3=1.71
boost 상한 carry 0.2 / ending 0.3 / overdue 0.2
백업 `backups/20260725_재기록전_DB전체/` · 배선전 커밋 fae01f67

## 3) 열린 과제 -> FINDINGS.md (ID로 지시)
K-00~K-05 OPEN. 4군 정밀분석 미착수.

## 4) 주의 (이 레포의 알려진 병)
- STATUS_LATEST(07-18)보다 RESUME_HERE(07-25)가 최신 — BOOT가 단일 진입점
- STATUS_LATEST / RESUME_HERE 가 .md·.txt 이중 사본 — 갱신 시 양쪽 동기화
- public 레포 · 약 90MB · data/*.db 추적 중 (K-05)

## 5) 더 필요하면
RESUME_HERE / RULES_FIXED / CURSOR_RULES / HYODO_PLAN / DECISION_LOG / reports
