# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-29 KST  
📌 사유: K-STAT-TUNE-WIRE · **FAIL** · ge3=0.1176 · 롤백완료 · NEXT=K-ATTACK-HOLD

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| K-STAT-TUNE-WIRE | **FAIL** · live verify · **롤백완료** |
| verify ge3 | **0.1176** · ge3_count=**139** · n=**1182** |
| Δ / p | **-0.0271** / **0.349617** vs pin 0.1447 |
| WIRE-V2 pin | ge3=**0.1447** · mean=**1.7504** (유지·미배선) |
| 권고 | **K-ATTACK-HOLD** · 승인필요=**예** |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-STAT-TUNE-WIRE** | gap20/hot10 배선 시도 · live verify | **FAIL** · 롤백 |
| K-STAT-TUNE | stat recency/gap/hot 격자 · stored markov/review | PASS(격자) |
| K-ATTACK-HOLD-MAP | 닫힌축·실레버공백 | HOLD맵 |
| K-MARKOV-WIRE-V2 | set_no 쿼터 | PASS(핀) |

---

## 2) STAT-WIRE 핵심

| 항목 | 값 |
|------|-----|
| n_eval | **1182** |
| live ge3 | **0.1176** (< pin 0.1447) |
| survey best (참고) | 0.1523 (stored markov/review + stat) |
| params 시도 | gap20/hot10 · pairs30/cap0.5 |
| rollback | gap30/50 · hot5 복원 |
| recommended_next | **K-ATTACK-HOLD** |

근거: `docs/benchmarks/20260729_KSTAT_WIRE_verify.json` · `reports/20260729_KSTAT_WIRE.md`

### 재탕금지 (누적)

STAT-WIRE(gap20/hot10) · SETPACK-TOP6 · MARKOV-TUNE · SETNO-HITMAP · EV-POP · BAND-SELECT · SUM-SELECT · conf-quota구WIRE · HISIM/STRUCT/COVER wheel · GATHER전면 · GENDIV · AUX-BLEND · GENMIX · 슬롯재선택 일체

---

## 3) 다음

K-ATTACK-HOLD — STAT-WIRE FAIL · 롤백완료 · 다음 공격축 **형 결정 대기**.

---

## 4) 산출물

- docs/benchmarks/20260729_KSTAT_WIRE_verify.json
- reports/20260729_KSTAT_WIRE.md
- My_Drive_Sync/커서보고서/20260729_KSTAT_WIRE.md
- tools/_k_stat_wire_verify.py

## 팩트체크

| 항목 | JSON | 보고서 | STATUS/NEXT |
|------|------|--------|-------------|
| ge3_rate | 0.1176 | 0.1176 | 0.1176 |
| Δ | -0.0271 | -0.0271 | -0.0271 |
| p | 0.349617 | 0.349617 | 0.349617 |
| verdict | FAIL | FAIL | FAIL |
| recommended_next | K-ATTACK-HOLD | K-ATTACK-HOLD | K-ATTACK-HOLD |
