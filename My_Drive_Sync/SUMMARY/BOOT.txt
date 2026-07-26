# BOOT — 외부 AI 30초 복원 (kweon / R36)

## 0) 한 줄
4군 앱 + 테스트로또 + 효도로또(1.5군). SSOT=kweon main · 로컬 `D:\3kweon`.
1~3군은 memoy 관할 — 여기 기록 금지(R34). 앱 지도=SUMMARY/MAP.md

## 1) 현재 스레드 (매턴 3줄만 갱신)
- 지금: FINDINGS K-01/K-03/K-04 CLOSED + K-06/K-07 등록 · STATUS 갱신
- 직전: UI패치 `22ac617` · R36 인프라 `0a1a55c`
- 다음: K-00 app/lotto4/ 정밀분석 착수 · K-07 fetch-latest 수동복구

## 2) 숫자 (근거 없으면 미확인)
lotto_predictions=1,245행 / 83회차 / stat·markov·review 각 415
lotto4 draws MAX=1234 · testlotto/hyodo draws MAX=1231 (20260726 실측)
boost 상한 carry 0.2 / ending 0.3 / overdue 0.2
git HEAD 작업 전: `616db13`

## 3) 열린 과제 -> FINDINGS.md (ID로 지시)
K-00·K-02·K-05·K-06·K-07 OPEN. K-01/K-03/K-04 CLOSED.

## 4) 주의 (이 레포의 알려진 병)
- STATUS_LATEST 20260726 갱신 — RESUME_HERE와 병행 시 BOOT 우선
- STATUS_LATEST / RESUME_HERE 가 .md·.txt 이중 사본 — 갱신 시 양쪽 동기화
- public 레포 · 약 90MB · data/*.db 추적 중 (K-05)

## 5) 더 필요하면
RESUME_HERE / RULES_FIXED / CURSOR_RULES / HYODO_PLAN / DECISION_LOG / reports
