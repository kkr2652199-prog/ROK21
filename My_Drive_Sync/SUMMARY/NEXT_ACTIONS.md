# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-PAST-LEARN-EV-RELABEL-GO
- 할일: SCORE-RULE-DIAG 결과(적중축 상한 없음) 형 확인 — soft 태그(hot1y/overdue)를 **EV 인기회피축**으로 라벨 재정의할지 결정 · 결정 전 코드·가중 변경 금지
- 완료조건: 형 GO (재정의 진행 or 트랙정지)
- 선행완료: docs/benchmarks/20260808_KPAST_LEARN_SCORE_RULE_DIAG.json · reports/20260808_KPAST_LEARN_SCORE_RULE_DIAG.md · 커서보고서 동기
- 승인필요: 미확인
- 선행조건: 없음
- 최종갱신: 2026-08-08

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **범위 확정(형 2026-08-08):** 대상 = **ROK21 테스트로또 과거학습 뇌(stat)** 만. 다른 앱·프로그램 수정 금지.
  memoy(`D:\MONEY lol` 1~3군) · kweon(`D:\3kweon`) **미접촉** · 작업루트 `D:\ROK21` 단일
- decay 15셀 전부 null(3.8067) 미달 · 현행 3.8982 · 최선 3.8875 → **적중축 튜닝 상한 없음**
- 균등이탈L1 ↔ log-score r=**0.9854** → 최근가중 = 자기부과 벌점
- 보정χ²=32.42 (df44 · p≈0.90) → 번호 편향 근거 없음 (Genest 2002 · Joe 1993)
- PBO=0.0 · 기대최대 0.0306 ≥ 실측 0.0107 (Bailey et al. 2014)
- Suetens et al.(2016 JEEA): hot=대중 몰림 / 직전번호=대중 회피 → hot1y 가점은 EV 역방향
- 상수·배선 불변: engine decay 0.005/0.05 · FRAME win26/mix0.8 · ASSOC/transition/LSTM OFF
