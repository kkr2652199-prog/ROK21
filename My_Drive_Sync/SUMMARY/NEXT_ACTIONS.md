# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-PAST-LEARN-NEXT-PICK
- 할일: EV-RELABEL 결과(인기편향 FW p=0.0004 실증 · **태그축 무신호 → soft 재정의 지지 안 됨**) 형 확인 후 다음 1건 선택 — **①seed 민감도 full-range 재측정** (권장 · 잡음 하한 미확정 상태로 그동안 판정해왔음) / ②회차 1236+ 전향적 EV 로그(개입 없음) / ③`cycle_gap_boost` 단독 A/B / ④트랙정지
- 완료조건: 형이 ①~④ 중 1건 지정
- 선행완료: docs/benchmarks/20260808_KPAST_LEARN_EV_RELABEL.json · docs/benchmarks/20260808_KPAST_LEARN_AUDIT_DIMS.json · reports/20260808_KPAST_LEARN_EV_RELABEL.md · reports/20260808_KPAST_LEARN_AUDIT_DIMS_ADVISORY.md · 커서보고서 동기
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
- **한국 실측(20260808 EV-RELABEL)**: 문헌 방향을 한국 데이터로 직접 검증. `t_hot1y` β=+0.0243 = **실제로 인기 방향**(4개 시대 전부) → hot1y 를 EV 레버로 재정의할 근거 없음
- **유일한 유의 인기축 = 저번호·저합**(sum β−0.0575 · le22 β+0.0463 · FW p=0.0004). 현재 과거학습 뇌에 **이 축이 아예 없다**. 단 전반구간 약함(구간2 z≈0) → 전향적 검증 전 발권 반영 금지
- **차원 사실**: 셀당 관측 1차 164.7 / 2차 18.7 / **3차 1.74** → 3차원 순위화 불가. pair/triple NOISE 판정은 정상
- **잡음 하한 미확정**: stat seed ge3 range **0.14** 를 n=100 에서만 측정. 이보다 작은 차이는 판정 불가
- 상수·배선 불변: engine decay 0.005/0.05 · FRAME win26/mix0.8 · ASSOC/transition/LSTM OFF
