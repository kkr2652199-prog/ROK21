# K-PAST-LEARN-SCORE-RULE-DIAG — 과거학습 뇌 튜닝 정밀진단 (논문 방법론)

📅 2026-08-08 KST · **NO_SKILL_VS_NULL** · wire=**False** · 수치 SSOT=`20260808_KPAST_LEARN_SCORE_RULE_DIAG.json`

---

## 0) 한 줄

셀 15개 전부 log-score가 null(균등, 3.806662)보다 **나쁘다** (최선 `L0.0005_S0.02`=3.887453 · 현행=3.898167). 균등이탈–점수 상관 r=0.9854 → 최근가중은 정보가 아니라 **자기부과 벌점**이다. decay 재튜닝으로 null을 넘길 수 없으므로 **KEEP_BASE 유지**가 맞고, 개선은 적중축이 아니라 EV(인기회피)축에서만 가능하다.

---

## 1) 대상 · 범위

| 항목 | 값 |
|------|-----|
| 뇌 | **과거학습**(tag=`stat`) = 테스트로또 3예측뇌 중 1번 |
| 모듈 | `app/testlotto/brains/stat_brain/engine.py` · `past_learn.py` |
| 틀(FRAME) | short_win=**26** · short_mix=**0.8** (ENGINE-APPLY 확정 · 이번 미변경) |
| 현행 decay | long=**0.005** · short=**0.05** (DETAIL_KEEP · 형 GO) |
| 평가구간 | 736~1235 · n=**500** |
| 변경 | **없음** (READ-ONLY 진단 · 발권/quota/engine 상수 불변) |

> R34 주의: 여기서 '1번 뇌'는 테스트로또 내부 뇌 순번이며, memoy 관할 1~3군과 무관하다.

---

## 2) 왜 지금 방식이 약한가

`DETAIL_TUNE` 은 ge3(≥3맞음) 비율로 9칸을 비교했다.

| 항목 | 값 | 문제 |
|------|-----|------|
| base score | 0.5772 | tune 0.28 / hold 0.14 |
| best score | 0.5780 | tune 0.24 / hold 0.16 |
| 차이 | **0.0008** | hold n=50에서 **적중 1건** 차이 |
| fusion Δ | **0.000** | live 반영 없음 |
| 시드 | HIGH_SENSITIVITY | `K-STAT-SEED-DIAG` stat range **0.14** |

ge3 는 0/1 절단 지표라 정보량이 작고(n=50), 시드 분산이 신호보다 크다.
적정채점규칙은 확률벡터 전체를 쓰므로 같은 표본에서 검정력이 크게 높다 (Gneiting & Raftery 2007).

---

## 3) 균등성 검정 — 상한이 있는가

| 항목 | 값 |
|------|-----|
| n_draws | **1235** · 번호별 기대 164.667 |
| naive χ² | 28.7368 |
| 보정 χ² (×44/39) | **32.4211** (df=44) |
| p (근사) | **0.901615** |
| 0.05 기각 | **아니오** (임계 60.4809) |
| 최다 | 34(184), 27(181), 12(179), 13(179), 18(176) |
| 최소 | 9(136), 32(144), 22(145), 23(147), 41(150) |

방법: Pearson χ² × (M−1)/(M−m) — 비복원 보정 (Genest·Lockhart·Stephens 2002 · Joe 1993 · Haigh 1997).
귀무=모든 번호 등확률. 기각 못하면 번호별 편향 근거 없음 → decay 튜닝 상한도 없음

---

## 4) 적정채점규칙 그리드 (log-score · Brier)

- null log-score = **3.806662** (=−log(1/45)) · null Brier = **0.115556**
- 셀 수 = **15** · long_decay [0.0005, 0.002, 0.005, 0.01, 0.02] × short_decay [0.02, 0.05, 0.1]
- skill = 1 − score/null (양수면 null 우위 · 낮은 score가 좋음)

| 순위 | cell | log-score | log skill | Brier | Brier skill | 균등이탈 L1 |
|------|------|-----------|-----------|-------|-------------|-------------|
| 1 | `L0.0005_S0.02` | 3.887453 | -0.021224 | 0.11819 | -0.0228 | 0.29754 |
| 2 | `L0.002_S0.02` | 3.888858 | -0.021593 | 0.118226 | -0.023108 | 0.299845 |
| 3 | `L0.005_S0.02` | 3.892596 | -0.022575 | 0.118317 | -0.023899 | 0.30559 |
| 4 | `L0.0005_S0.05` | 3.892945 | -0.022666 | 0.118442 | -0.024983 | 0.308503 |
| 5 | `L0.002_S0.05` | 3.894368 | -0.02304 | 0.118479 | -0.025297 | 0.310747 |
| … | `L0.02_S0.1` (최악) | 3.945393 | -0.036444 | 0.120027 | -0.038696 | 0.388826 |

현행 셀 `L0.005_S0.05` = log-score **3.898167** · skill **-0.024038** · 균등이탈 **0.316418**

### 4.0 메커니즘 — 이탈이 곧 벌점

- 균등이탈(L1) ↔ log-score 상관 **r=0.9854** (셀 15개)
- 균등분포 이탈이 클수록 log-score 악화 = 최근가중이 정보가 아니라 자기부과 벌점
- 진실이 균등이면 기대: r ≈ +1 (이탈=순손실)

### 4.1 대응검정 (per-draw 차이)

| 비교 | mean Δ | t | p(양측) | 승률 |
|------|--------|---|---------|------|
| 현행 vs null | +0.091505 | 11.779 | 0.0 | 0.308 |
| 최적 vs null | +0.080791 | 11.0708 | 0.0 | 0.328 |
| 최적 vs 현행 | -0.010714 | -6.2831 | 0.0 | 0.594 |

(Δ<0 = 앞쪽이 더 좋음 · log-score는 낮을수록 좋다)

---

## 5) 선택편의 · 과적합 확률

| 항목 | 값 |
|------|-----|
| 시행 셀수 N | 15 |
| 셀 평균의 분산 | 0.000297927 |
| 우연 기대최대 이득 | **0.030563** |
| 실측 최적−현행 이득 | **0.010714** |
| PBO (CSCV) | **0.0** · combos 70 · S=8 |

- PBO 해석: PBO>=0.5 → 최적셀 선택이 우연 수준(과적합 위험)
- 실측 이득 ≤ 우연 기대최대면 그리드 최적셀은 **선택편의로 설명 가능**.
- 근거: Bailey & López de Prado (2014) Deflated Sharpe / false-strategy theorem · Bailey, Borwein, López de Prado & Zhu (2014) J. Computational Finance

---

## 6) 문헌 → 우리 적용

| 문헌 | 핵심 | ROK21 적용 |
|------|------|------------|
| [Genest, Lockhart & Stephens (2002) 'χ² and the lottery', JRSS-D](https://doi.org/10.1111/1467-9884.00315) | 비복원 추첨은 naive Pearson χ² 가 χ² 분포를 안 따름 → 가중합/보정 필요 | 6/45 보정 (M-1)/(M-m)=44/39 · df=44 로 번호 균등성 검정 (§3) |
| [Joe (1993) 'Tests of uniformity for sets of lotto numbers', SPL](https://doi.org/10.1016/0167-7152(93)90141-5) | 단일번호·쌍·삼중 균등성 및 회차간 독립 검정 도출 | 번호축 먼저 검정 · 쌍/삼중은 기존 KSIGNAL L3 PMI 트랙과 연결 |
| [Gneiting & Raftery (2007) 'Strictly Proper Scoring Rules', JASA 102(477)](https://doi.org/10.1198/016214506000001437) | log/Brier 등 적정채점규칙은 참분포에서 기대점수 최적 → 파라미터 추정에 사용 가능 | decay 를 ge3(0/1) 대신 확률벡터 log-score 로 선택 (§4) · 시드 무관·검정력↑ |
| [Bailey, Borwein, López de Prado & Zhu (2014) 'The Probability of Backtest Overfitting'](https://davidhbailey.com/dhbpapers/backtest-prob.pdf) | CSCV 로 '최적 IS 셀이 OOS 중위 이하일 확률'(PBO) 추정 · 0.5↑면 선택=우연 | decay 그리드 선택의 과적합 확률 직접 계산 (§5) |
| [Bailey & López de Prado (2014) 'The Deflated Sharpe Ratio', JPM 40(5)](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) | 시행수 N·시행간 분산으로 기대최대 성과를 계산해 선택편의 차감 | 9~15칸 그리드의 '우연 최대이득' 과 실제 이득 비교 (§5) |
| [Bodenham & Adams / Plasse & Adams — forgetting factors (categorical streams)](https://doi.org/10.1007/s11222-019-09858-0) | 망각계수는 우도(likelihood) 기반으로 온라인 튜닝 · 고정망각은 특수사례 | decay=망각계수 → 우도(log-score)로 고르는 게 표준. 적응형은 신호 확인 후에만 |
| [Suetens, Galbo-Jørgensen & Tyran (2016) JEEA 14(3) 584-607](https://doi.org/10.1111/jeea.12147) | 플레이어는 직전 당첨번호를 피하고(도박사오류) 최근 연속출현 번호로 몰린다(핫핸드) | past_learn 의 '미출30+'·'1yHot' 태그는 플레이어 인기축과 겹침 → 공유당첨 EV 주의 (§6) |
| [Cook & Clotfelter (1993) / Baker & McHale (2011) JRSS-A 174(4) — conscious selection](https://doi.org/10.1111/j.1467-985x.2011.00693.x) | 당첨P는 고정 · 비인기 조합은 분배 감소로 기대값(EV)↑ | ROK21 기존 EV축(적중축 폐기)과 정합 · 인기페널티(KSIGNAL L4)로 연결 |

### 6.1 행동경제 경고 (튜닝 방향에 직결)

Suetens et al.(2016)은 플레이어가 **직전 당첨번호를 회피**(도박사 오류)하고 **최근 자주 나온 번호로 몰린다**(핫핸드 오류)는 것을 개인 패널로 보였다.

우리 `past_learn.soft_delta_for_set` 은 지금

```
overdue  : gap >= 30      → +0.35/개 (최대 1.5)
hot1y    : rate_1y > 1.15×null → +0.25/개 (최대 1.0)
cold1y   : rate_1y < 0.75×null → +0.10/개 (최대 0.5)
```

즉 **hot1y 가점 = 대중 인기축 가점**이다. 당첨확률은 안 변하는데(균등) 공유당첨 확률은 올라가므로 EV에는 역방향이다 (Cook & Clotfelter 1993 · Baker & McHale 2011).
반대로 overdue(미출) 가점은 대중이 **피하는** 쪽이라 EV에 유리한 방향이다.

→ 결론: soft 태그는 '적중↑' 근거가 아니라 **EV(인기회피) 축으로 재해석**해야 한다. 이는 이미 있는 KSIGNAL **L4 popularity penalty**(w=0)와 같은 축이다.

---

## 7) 결론 · 채택/기각

### 결론

- 균등성: 보정 χ²=32.4211 (df=44, p≈0.901615) → 번호별 편향 근거 없음
- 셀 전체 중 null 초과(skill>0) 존재 = False · 균등이탈↔log-score 상관 r=0.9854
- 현행 decay(0.005/0.05) vs null: mean Δ=+0.091505 · p=0.0 → null보다 유의하게 나쁨
- 최적셀 `L0.0005_S0.02` vs 현행: p=0.0 · PBO=0.0 · 우연 기대최대 0.030563 ≥ 실측 0.010714 = True
- ge3(n=50) 대신 log-score 를 쓰면 시드 분산 없이 같은 데이터에서 훨씬 촘촘히 비교된다
- 실질 개선 후보는 decay 미세조정이 아니라 soft 태그의 EV(인기회피) 재정의

### 채택 (진단·평가 방법 교체 · wire 없음)

1. decay/망각계수 튜닝 지표를 **ge3 → log-score(적정채점규칙)** 로 교체
2. 그리드 선택에는 항상 **PBO + 기대최대** 동반 보고
3. 번호축 주장 전 **보정 χ² 균등성 검정** 선행
4. soft 태그(hot/overdue)는 **EV·인기축**으로 라벨 재정의 (KSIGNAL L4 연결)

### 기각

1. hold n=50 ge3 1건 차이로 상수 변경
2. hot1y 가중 상향 (인기축 = EV 역방향)
3. 적응형 망각계수 즉시 배선 (신호 확인 전)
4. LSTM/시퀀스 예측 부활 · random.choices 개조

---

생성: `tools/_k_past_learn_score_rule_diag.py` · verdict **NO_SKILL_VS_NULL**
