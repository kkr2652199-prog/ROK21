# BENCH_REPORT_TEMPLATE — 벤치 리포트 표준 (K-BENCH-05·03)

📅 제정: 2026-07-29 · SSOT=`BENCH_PROTOCOL.md` §6·§7  
📌 모든 survey/WF 마크다운은 이 템플릿 구조를 따른다.

---

## 1) SUMMARY 표 (필수 · baseline 행 포함)

| label | pipeline | mean | ge3_rate | pin | Δge3 vs null | Δge3 vs pin | p (vs null) | 비고 |
|-------|----------|------|----------|-----|--------------|-------------|-------------|------|
| **theory_baseline** | — | **0.8000** | **0.1137** | — | — | — | — | E[match]=6×6/45 · NULL_GE3 |
| **WIRE-V2 pin** | stored | 1.7504 | 0.1447 | ✓ | +0.0310 | — | — | PINNED_BASELINE 참조 |
| (후보 예) | WF live | 1.7614 | 0.1277 | — | +0.0140 | −0.0170 | 0.35 | n_eval=1182 · best-of-5 |

- **baseline 행 누락 금지** (K-BENCH-05).
- `pipeline` 없이 WF·stored 혼합 **금지** (K-BENCH-03).

---

## 2) tier 피벗 표 (ge3와 함께 권장)

### WF live (예시)

| brain | pipeline | r1 | r2 | r3 | r4 | r5 | ge3 | n_sets |
|-------|----------|----|----|----|----|----|-----|--------|
| stat | WF live | 0 | 0 | 1 | 12 | 45 | 58 | 500 |
| markov | WF live | 0 | 0 | 0 | 8 | 38 | 46 | 500 |
| review | WF live | 0 | 0 | 0 | 5 | 22 | 27 | 500 |

- tier 규칙: `BENCH_PROTOCOL.md` §7.2 (`_prediction_rank_tier` 동일).
- ge3 = r3+r4+r5 (≥3 적중 세트 수 / rate는 n_sets 대비).

### stored / pred UI (별도 표 · 혼용 금지)

| brain | pipeline | r1 | r2 | r3 | r4 | r5 | ge3 | window |
|-------|----------|----|----|----|----|----|-----|--------|
| stat | stored | … | … | … | … | … | … | review100 1135–1234 |

---

## 3) 체크리스트

- [ ] SUMMARY에 `theory_baseline` 행 (mean=0.8 · ge3=0.1137)
- [ ] pin 있으면 별도 행 + Δge3
- [ ] `pipeline` 컬럼 또는 표 2개로 WF live / stored 분리
- [ ] ge3 단독 시 tier 표 병기
- [ ] JSON `null_ge3`=0.1137 · `docs/benchmarks/*.json` SSOT 일치

*예측 코드 수정 없음 · survey 실행은 형 GO 후.*
