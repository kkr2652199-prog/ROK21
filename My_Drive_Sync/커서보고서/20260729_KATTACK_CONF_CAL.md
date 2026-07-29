# K-ATTACK-CONF-CAL — 뇌내 conf 보정·세트순위

📅 2026-07-29 KST  
📌 JSON: `docs/benchmarks/20260729_KCONFCAL_results.json`  
📌 도구: `tools/_k_attack_conf_cal.py`  
📌 데이터: `testlotto_brain_review` (세트별 conf·matched) · walk-forward isotonic · DB/코드 **미수정**

---

## 0) 검토

NEXT=`K-ATTACK-CONF-CAL` 정합 · READ-ONLY · 진행.

---

## 1) Calibration (전체 창 · 세트 단위)

| 뇌 | spearman_r | conf_mean | match_mean |
|----|------------|-----------|------------|
| stat | **+0.019** | (bins JSON) | ~null |
| markov | **+0.012** | | |
| review | **−0.006** | | |

→ 양수 2/3 (게이트 통과 수준이나 **신호 매우 약함**).

---

## 2) 세트순위 (n_eval=1182 · within=3546 picks)

| 정책 | mean | ge3_rate |
|------|------|----------|
| max orig conf | 0.8252 | 0.0271 |
| max conf_cal | 0.8274 | 0.0290 |
| **tier best_set (현행)** | **1.7084** | **0.1227** |
| cross max-conf | 0.8418 | 0.0237 |
| cross conf_cal | 0.8342 | 0.0262 |
| RR + tier (BAYES 축) | **1.7428** | **0.1337** |

| delta | mean |
|-------|------|
| cal − orig | **+0.0022** (미미) |
| cal − tier | **−0.881** |
| cross_cal − RR | **−0.909** |

---

## 3) 판정

| 게이트 | 결과 |
|--------|------|
| spearman>0 ≥2뇌 | PASS (약함) |
| cal > orig | PASS (+0.002) |
| cal > RR | **FAIL** |
| cal > tier | **FAIL** |

**verdict = 보류** (실질: conf 세트순위 경로 **관측종료**에 가깝다)  
→ **WIRE 금지**. 현행 tier best_set이 conf 정렬보다 압도.

핵심: max-conf 선택은 ≈null(0.82). conf는 세트 순위에 거의 쓸모없고, isotonic도 구제 못 함.

---

## 4) 다음

`K-ATTACK-OPEN` — CONF-CAL 경로 닫고 다음 공격 레버 1건 선정 (READ-ONLY 우선).
