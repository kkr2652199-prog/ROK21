# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-27 KST  
📌 사유: K-V 발권 중복제거 구현·검증 (E[k]→100)

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| kweon | `264de3c` 동결 |
| 성적 | `BENCH_PROTOCOL.md` |
| CUTOFF | 기본 ON |
| DEDUP | `ROK21_DEDUP` **기본 ON** |

---

## 1) K-V (PATCHED)

| 항목 | 실측 |
|------|------|
| OFF E[k] | **97.091** (1000회) |
| ON E[k] | **100.000** · unresolved **0** |
| OFF vs ON 왜곡 | 이표본 전 p≥0.97 |
| 뇌 비율 Δ | **0** |
| Δ시간/100장 | **+0.015s** |
| P 배수 | **≈1.030×** (낭비제거·예측력 아님) |

---

## 2) 열린 것

K-T/U OPEN · K-S PATCHED · K-M/N HOLD · K-O~R OPEN

---

## 3) 다음 (형)

1. pattern/balance 제약 공식 채택 여부  
2. K-R / WF 잔여  
3. hyodo 1231 (승인 후)  
