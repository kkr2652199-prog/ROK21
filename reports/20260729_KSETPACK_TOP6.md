# K-SETPACK-TOP6 — 번호점수 top6 → set1 강제 재조립 (READ-ONLY)

📅 2026-07-29 · DB/코드 배선 수정 없음 · `db_code_write=false`  
도구: `tools/_k_setpack_top6_survey.py`  
JSON: `docs/benchmarks/20260729_KSETPACK_top6.json`

---

## 요약

출현횟수 top6을 set1에 몰아준 **SETPACK**은 현행 5세트 best ge3를 **전 뇌·풀에서 하회**.  
pool pack ge3=**0.1010** < base **0.1227**, null p=**0.99** → **FAIL**.  
`recommended_next=없음` (NEXT/BOOT/STATUS는 본 Part에서 미갱신 · 형 확인 후).

---

## 전제

| 항목 | 값 |
|------|-----|
| 풀 | `testlotto_brain_review` · brains **stat/markov/review** |
| 구간 | draw **53~1234** · n_eval/뇌=**1182** · pool n=**3546** |
| null_n5 | ge3=**0.1137** |
| 점수(주) | 5세트 **출현횟수** (동점=번호 오름) |
| 점수(민감) | 번호가 속한 세트 **confidence 합** |
| set1 | 점수 top6 |
| set2~5 | 기존 set_no 2~5에서 set1 번호 제거 → set1 비중복 우선·점수↓로 6개 보충 |
| vs GATHER | GATHER=교차세트 스티치/독립집합 · **SETPACK=set1만 몰아주기** |

---

## 결과표 (primary = 출현횟수)

### 뇌별

| 뇌 | base best_mean | pack best_mean | base ge3 | pack ge3 | pack set1_mean | pack ge4 | p vs null | PASS |
|----|----------------|----------------|----------|----------|----------------|----------|-----------|------|
| stat | 1.7124 | 1.6574 | 0.1091 | 0.1083 | 0.7733 | 0.0118 | 0.734 | **FAIL** |
| markov | 1.7115 | 1.5914 | **0.1362** | 0.0998 | 0.8426 | 0.0051 | 0.941 | **FAIL** |
| review | 1.7014 | 1.5914 | 0.1227 | 0.0948 | 0.8139 | 0.0042 | 0.984 | **FAIL** |

### 전체(3뇌 풀)

| 지표 | 현행5 best | SETPACK best | Δ |
|------|------------|--------------|---|
| mean | **1.7084** | 1.6134 | −0.095 |
| ge3_rate | **0.1227** | 0.1010 | −0.0217 |
| ge4_rate | 0.0082 | 0.0071 | −0.0011 |
| set1_mean | 0.8209 | 0.8099 | −0.011 |
| binom p vs null | 0.0499 | **0.9929** | — |

### 민감도 (conf_sum)

| 뇌 | pack ge3 | PASS |
|----|----------|------|
| stat | 0.1100 | FAIL |
| markov | 0.0838 | FAIL |
| review | 0.1024 | FAIL |

→ 점수 정의를 conf 합으로 바꿔도 동일 방향(악화).

---

## Gates

| gate | 정의 | 결과 |
|------|------|------|
| best_ge3_gt_baseline | pack best ge3 > 현행5 | **false** (뇌·풀 전부) |
| binom_p_vs_null_lt_0.05 | p(ge3≥관측 \| null=0.1137) < 0.05 | **false** |
| PASS | 위 둘 AND | **FAIL** |

---

## Verdict

**FAIL.** set1에 고빈도(출현) 번호를 몰아도 best-of-5·set1 모두 개선되지 않음.  
markov에서 악화가 가장 큼(ge3 0.1362→0.0998).  
GATHER(흩어진 승자 스티치)와 달리 SETPACK은 **이미 자주 나온 번호 집중**이라, 다양성 파괴로 best 지표가 깎인 관측.

## recommended_next (제안문 · 문서만 · NEXT 미갱신)

**없음** → 현행 `K-ATTACK-HOLD` 유지 권고.  
SETPACK-WIRE 금지. 형이 확인 후 다음 축 재선정.

---

## Part B 요약 앵커 (본 보고서 부록 아님 · 채팅 응답 본문)

뇌=규칙/통계/마르코프 휴리스틱(+채점) · LLM/NN 아님(활성 3+4 경로).  
모듈 구조 유지 · 이름(뇌)만 논의 권고. 폐기 패치 없음.
