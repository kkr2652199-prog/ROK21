# K-SIGNAL-TAXONOMY-V1 — 설계 논의 (wire 금지)

📅 2026-08-05 KST · **DOC** · 수치 SSOT = `20260805_KSIGNAL_TAXONOMY_V1.json`

---

## 0) 문제

fusion ge3≈0.135 정체. 뇌별(stat≈0.165)이 fusion에 흡수되지 않음.  
원인 가설: **quota 절단만 있고 세트 단위 신호 합산이 없음** · 신호 종류 부족.

---

## 1) 레이어 (진단 → 정책)

| ID | 내용 | 이번 턴 |
|----|------|---------|
| L1 | 조합군 이론 w vs 실측 deviation | **표·survey** |
| L2 | EMA H=8/26/78 발산 | 설계만 |
| L3 | 쌍 PMI · set_pmi_score | **survey** |
| L4 | 인기 페널티 (생일/합/연속) | **스펙** |
| L5 | CUSUM regime | 설계만 · 별도 GO |

정책층: 모든 가중치 초기 **0**. 발권·quota·engine.py 미변경.

---

## 2) L4 인기 페널티 스펙

목적: **공유 당첨 회피(EV)** · 당첨P↑ 아님.

| 항 | 규칙 | 비고 |
|----|------|------|
| birthday | `# {n≤31} ≥ 4` → +1 | 생일 편향 |
| sum_low | `sum ≤ 120` → +1 | 이론 mean≈138 · IQR 하측 근사 |
| consec_3 | `max_run≥3` → +0.5 | rare_tag 재사용 |

`popularity_penalty = sum(항)` · `score`에 `-w4*penalty` (w4=0 진단).

---

## 3) 신호등 통합 스코어

```
score(set) = w1*deviation_score + w2*ema_divergence
           + w3*pmi_score + w4*(-popularity_penalty)
w1=w2=w3=w4 = 0   # 진단만
```

흐름(나중 GO):

```
뇌 세트 생성 → L1~L4 annotate → score 정렬 → (선택) quota 보완
```

금지: auto-tune · random.choices · `_get_draws_before` 변조 · engine.py.

---

## 4) L2·L5 메모

- **L2:** 번호별 EMA_8/26/78 → rank · 단기−장기 불일치 = divergence · markov 보조만 · quota 미수정  
- **L5:** 최근50 vs 전체 빈도 CUSUM · 임계 초과 시 최근 가중 · **별도 형 GO**

---

## 5) 산출

- survey: `tools/_k_signal_taxonomy_v1_survey.py` → JSON/MD  
- 본 DESIGN · TAG/필터 준비(`K-RARE-FILTER-PREP`)와 병렬 트랙

판정: **DOC** · wire 없음
