# K-ATTACK-OPEN — 다음 공격 레버 서베이

📅 2026-07-29 KST  
📌 JSON: `docs/benchmarks/20260729_KOPEN_survey.json`  
📌 도구: `tools/_k_attack_open_survey.py` · READ-ONLY · **149.6s**

---

## 0) 검토

NEXT=`K-ATTACK-OPEN` 정합 · 레버 선정 관측(승인=배선 아님) · 진행.

---

## 1) 3레버 비교

| 레버 | 핵심 지표 | PASS 조건 | 결과 | verdict |
|------|-----------|-----------|------|---------|
| **A analog** | overlap spearman **−0.0023** | r>0.03 | FAIL | 관측종료 |
| **B markov tune** | best mean **0.8176** (80, decay0.05) | mean>1.7428 or ge3>0.1337 | FAIL | 관측종료 |
| **C conf rebuild** | spearman 0.024/0.024/0.003 · bin_spread=5 | spread≥3 **AND** sp>0.05×2뇌 | FAIL (sp 미달) | 관측종료 |

**recommended_next = 없음**

---

## 2) 해석

- A: analog 추천∩세트 overlap과 적중 **무상관**(음수).
- B: steps×decay 결정론 top6는 ≈null(0.82). RR(1.74)·기존 markov best_set 축과 다름 — **조합 생성 품질**이 아니라 방문 top6 신호만 측정. 그래도 RR 초과 없음.
- C: 순위 기반 new_conf로 bin은 퍼지나 spearman 여전히 <0.05. CONF-CAL과 동일 결론(세트순위 레버 약함).

→ 「고르기」·「약한 conf 재점수」·「analog overlap」 모두 RR/tier를 넘을 힌트 없음.

---

## 3) 다음

형·동생에게 **새 축** 재선정 요청.  
NEXT=`K-ATTACK-HOLD` (OPEN 서베이 종료 · 승인 후 다음 1건).
