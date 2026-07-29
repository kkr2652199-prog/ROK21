# K-ATTACK-SLICE — 구간(LMH) 승격 시뮬

📅 2026-07-29 KST  
📌 JSON: `docs/benchmarks/20260729_KATTACK_slice.json`  
📌 도구: `tools/_kattack_slice.py`  
📌 선행: PATTERN-1 (4등군 구간일치 35.5% vs 대조 5%)

---

## 0) 형 아이디어 (간략 · 혼동 방지)

| 아이디어 | 판정 |
|----------|------|
| **뇌내 5→몰아+5** | **좋은 방향** — SCATTER로 기회 실측(stat 풀6공 21회). 다만 v0~v2는 **선별**에서 막혀 WIRE 보류·관측 고정. 아이디어 폐기 아님. |
| **자릿수 역추적** | POS로 sticky≈null — **제약·서술용**, 전이 가속 레버는 약함. |
| 이번 SLICE | PATTERN-1 구간 신호를 **사전 승격**에 쓸 수 있는지 검증. |

「간략 보고」= 위처럼 아이디어 짧게 · **작업은 전체 실행** (이번 턴 준수).

---

## 1) 설계

| 정책 | 의미 |
|------|------|
| baseline | WF best_set (실당첨 기준 — 사후 상한에 가까움) |
| oracle_zone | 실제 LMH에 가장 가까운 세트 (치트) |
| prev_zone / bal_222 / recent20 | 맹목 승격 |
| **live_proxy** | conf 최대 vs conf top2 중 222 근접 (발권 현실) |

---

## 2) 결과 (2~1234 · 3698행)

### 사후 best 대비 (참고)

| 정책 | mean | ge3_rate | ge4_rate |
|------|------|----------|----------|
| baseline (match-best) | **1.711** | 12.4% | 0.84% |
| oracle_zone | 0.926 | 3.9% | 0.43% |
| bal_222 (맹목 최선) | 0.821 | 2.6% | 0.16% |

→ 구간만으로 best를 **교체**하면 성적 **악화**.  
PATTERN-1의 “4등일 때 구간이 맞음”은 **결과 상관**이지, **구간 선택이 적중을 만든다**는 뜻이 아님.

### 라이브 대리 (confidence)

| 정책 | mean | ge4_rate |
|------|------|----------|
| conf_only | **0.826** | 0.22% |
| conf top2 → 222 | 0.823 | 0.19% |
| conf top2 → oracle match | **1.226** | 0.41% |

→ 222 타이브레이크 **무이득**.  
top2 안에 더 좋은 세트가 있는 경우는 많음(oracle 1.23) → **confidence 정렬 개선**이 구간보다 우선.

---

## 3) AI 아이디어 적용

- oracle ceiling vs blind 분리  
- prev-draw LMH / 2:2:2 / recent20 mode  
- live conf proxy (발권 공정 비교)  
- GATHER hybrid 힌트는 관측층 유지

---

## 4) 판정

| 항목 | 결과 |
|------|------|
| SLICE 배선 | **보류** (promote_wire=false) |
| 구간 신호 | 서술·사후 설명용으로 유지 |
| 다음 | **K-ATTACK-BAYES** — 3뇌 동적가중 (CREW: Jaccard↓·상관↓ 활용) |

---

## 5) 산출물

- `tools/_kattack_slice.py`
- `docs/benchmarks/20260729_KATTACK_slice.json`
- 본 보고서 → `커서보고서/`
