# BENCH_REPORT_TEMPLATE — 벤치 리포트 표준 (숙제 제출형)

📅 개정: 2026-07-30 · SSOT=`BENCH_PROTOCOL.md` §6·§7·§9  
📌 모든 survey/WF 마크다운은 **아래 6섹션**을 반드시 포함한다. 수치는 `docs/benchmarks/*.json`만 인용.

---

## 보고서 읽는 법 (30초)

| 순서 | 섹션 | 누가·왜 |
|------|------|---------|
| 1 | 📋 선생님이 준 숙제 | **형/지시서** — 무엇을 물었는지, PASS/FAIL 기준 |
| 2 | 🔧 학생이 한 일 | **커서** — 코드·배선 건드렸는지, 파라미터 |
| 3 | 📊 풀이 (결과표) | **숫자 SSOT** — mean·ge3·p·tier(있으면) |
| 4 | ✅/❌ 맞은·틀린 것 | **판정** — gate 항목별 O/X |
| 5 | 📝 복습 | **다음 액션** — 고칠 것 1~3줄 + recommended ID |
| 6 | 📎 근거 | **재현** — JSON 경로·seed·n·elapsed |

> **원칙:** 보고서 본문 숫자 ≠ JSON 이면 **보고서가 틀림**. tier·pipeline 혼용 금지(K-BENCH-03).

---

# {ID} — {한 줄 제목}

날짜 {YYYY-MM-DD} · gate={quick|full} · verdict={PASS|FAIL|…}

---

## 1. 📋 선생님이 준 숙제

| 항목 | 내용 |
|------|------|
| **ID** | `{K-XXXX-NN}` |
| **질문 (한 문장)** | {예: 3뇌×10 pool에서 어떤 선별 축이 null/pin 대비 ge3를 올리는가?} |
| **PASS 기준** | {예: QUICK — any selector ge3>0.1137 AND p<0.15} |
| **FAIL 기준** | {예: 모든 selector가 null 이하 또는 p≥0.15} |
| **금지사항** | {예: coordinator wire 금지 · predict_* 수정 금지 · DB 쓰기 금지} |
| **선행 완료** | {있으면 ID} |

---

## 2. 🔧 학생이 한 일

### 코드·배선 (wire)

| 항목 | Y/N | 비고 |
|------|-----|------|
| coordinator / predict_* 수정 | **N** | JSON `coordinator_modified` |
| production wire (형 GO) | **N** | |
| DB 쓰기 | **N** | JSON `db_code_write` |
| pipeline | **WF live** / stored | 혼용 금지 — 표 2개로 분리 |

### 실행 파라미터

| key | value | 출처 |
|-----|-------|------|
| n_eval | {200} | JSON |
| draw_range | {1035–1234} | JSON |
| sample_mode | tail / full | JSON |
| seed | {42} | JSON `mc_seed` |
| pool_sets_per_brain | {10} | JSON |
| selected_n | {5} | JSON |
| window_hint | {…} | JSON (해당 시) |
| selectors / variants | {목록} | JSON |

---

## 3. 📊 풀이 (결과표)

> baseline 행 **필수**: theory null ge3=0.1137 · WIRE-V2 pin ge3=0.1447 (K-BENCH-05).

### SUMMARY (필수)

| label | pipeline | mean | ge3_rate | ge3_cnt | Δge3 vs null | Δge3 vs pin | p (vs null) | verdict |
|-------|----------|-----:|---------:|--------:|-------------:|------------:|------------:|---------|
| **theory_baseline** | — | **0.8000** | **0.1137** | — | — | — | — | null |
| **WIRE-V2 pin** | stored | **1.7504** | **0.1447** | — | +0.0310 | — | — | pin |
| {control} | WF live | … | … | … | … | … | … | … |
| **best {variant}** | WF live | … | … | … | … | … | … | PASS/FAIL |

### variant / selector 전체 (ge3 내림)

| {axis} | mean | ge3_rate | ge3_cnt | ge4_rate | Δpin | Δnull | p | verdict |
|--------|-----:|---------:|--------:|---------:|-----:|------:|--:|---------|
| … | … | … | … | … | … | … | … | … |

### tier 피벗 (수집 시만 · JSON에 r1~r5 있을 때)

| brain | pipeline | r1 | r2 | r3 | r4 | r5 | ge3 | n_sets |
|-------|----------|---:|---:|---:|---:|---:|----:|-------:|
| … | WF live | … | … | … | … | … | … | … |

- tier 없으면 **「tier: 미수집 (본 survey)」** 한 줄 명시.
- ge3 = r3+r4+r5 (`BENCH_PROTOCOL.md` §7.2).

---

## 4. ✅ 맞은 것 / ❌ 틀린 것

### PASS gate 체크 (항목별 O/X)

| # | gate 조건 | 결과 | O/X |
|---|-----------|------|-----|
| G1 | {예: any selector ge3 > null (0.1137)} | {best ge3=…} | ✅ / ❌ |
| G2 | {예: p < 0.15 (QUICK)} | {p=…} | ✅ / ❌ |
| G3 | {예: coordinator_modified = false} | {false} | ✅ / ❌ |
| G4 | {full only: ge3 > pin AND p < 0.05} | … | ✅ / ❌ / N/A |

**종합 verdict:** `{QUICK PASS | FAIL | …}` — JSON `pass_gate` / `verdict`

### 해석 (한 줄)

- {예: combined만 null·pin 동시 통과 후보 · overlap/bin 단독은 FAIL}

---

## 5. 📝 복습 (다음에 고칠 것)

- {bullet 1 — 무엇이 약했는지}
- {bullet 2 — full gate에서 확인할 것}
- {bullet 3 — wire 전 형 확인 사항}

**recommended_next:** `{K-XXXX-FULL}` — {한 줄}

---

## 6. 📎 근거

| 항목 | 값 |
|------|-----|
| JSON SSOT | `docs/benchmarks/{YYYYMMDD}_{ID}_survey.json` |
| seed | {42} |
| n_eval | {200} |
| elapsed_sec | {18.1} |
| pass_gate (JSON) | {true/false} |
| script | `tools/_{…}.py` (해당 시) |

### 팩트체크 (JSON ↔ 보고서)

| 필드 | JSON | 보고서 | 일치 |
|------|------|--------|------|
| n_eval | … | … | ✅ |
| best ge3 | … | … | ✅ |
| pass_gate | … | … | ✅ |
| coordinator_modified | … | … | ✅ |

---

## 작성 체크리스트 (커서용)

- [ ] 6섹션 모두 존재 (순서 고정)
- [ ] SUMMARY에 theory_baseline + WIRE-V2 pin 행
- [ ] pipeline 컬럼 또는 WF/stored 표 분리
- [ ] gate O/X 표 + 종합 verdict
- [ ] 수치 전부 JSON과 일치 (기억·추정 금지)
- [ ] `My_Drive_Sync/커서보고서/` 동일 파일 복사

*예측 코드 수정·coordinator wire = 형 GO 전 금지.*
