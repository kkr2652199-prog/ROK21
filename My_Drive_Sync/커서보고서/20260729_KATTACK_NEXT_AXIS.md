# K-ATTACK-NEXT-AXIS — HOLD 하 다음 공격축 선정 + SETNO 관측

📅 2026-07-29 · DB/coordinator **미수정** · `db_code_write=false`  
선정축 ID: **K-SETNO-HITMAP**  
도구: `tools/_k_setno_hitmap_survey.py`  
JSON: `docs/benchmarks/20260729_KSETNO_hitmap.json`  
V2 pin: `docs/benchmarks/20260729_KMARKOV_WIRE_V2_verify.json` (ge3=**0.1447**)

---

## 0) 선정 요약

| 항목 | 값 |
|------|-----|
| **선정축** | **K-SETNO-HITMAP** |
| 가설 | V2 뇌쿼터(m3+s1+r1) 고정 시, 뇌내 **set_no 적중 분포가 비균등**하면 동일 5장 비용으로 set_no 재배치가 ge3를 개선한다 |
| V2와 직교 | 예 — 뇌 믹스·파라미터 불변 · **발권 슬롯(set_no)만** |
| 관측 | **실행완료** (0.3s · brain_review JSON matched_count) |
| 판정 | **FAIL(WIRE금지)** — best Δge3=+0.0034 < 의미임계 0.005 |
| 실패시 | **HOLD · V2 유지** |

---

## 1) 후보 2~4개 → 1건

| # | 후보 ID | 가설 스케치 | 기각 사유 |
|---|---------|-------------|-----------|
| A | **K-SETNO-HITMAP** ✅ | 뇌×set_no 히트맵 → V2 쿼터 내 슬롯 재배치 | **선정** |
| B | K-STATP (stat×pattern) | PATTERN2 조건부 잔여 | 전역 pattern/STRUCT FAIL 인접 · AUX 재가중 재탕 위험 |
| C | K-MARKOV-LEARN (K-F) | markov에 learn_state boost 소비 | PROBVEC carry/ending≈null · 동결 boost 상한 인접 |
| D | K-ZONE-SLICE 재개 | PATTERN1 구간일치 필터 | SLICE/COVER 경로 이미 보류·FAIL · 동일가설 재탕 |

**왜 A:** PATTERN1 tier4에서 set3=12/31(39%) 힌트 + V2는 set_no **오름만** 고정 → 미개척·범위 좁음·READ-ONLY 즉시·구현비용 낮음(쿼터 dict만).

---

## 2) 관측 방법 (실행됨)

1. `testlotto_brain_review` draw 53~1234 · 3뇌 · 세트별 `matched_count` 로드  
2. hitmap: 뇌×set_no mean/ge3/ge4  
3. named policies + 격자: markov C(5,3) × stat∈{1,2,3} × review∈{1,2,3}  
4. baseline = V2 `{m:1,2,3 / s:1 / r:1}`  

**PASS 기준 (사전):**  
(1) best ge3 > V2 0.1447 **AND** (2) binom p vs null_n5(0.1137) < 0.05 **AND** (3) Δge3 ≥ **+0.005**  
→ 전부 충족 시만 `K-SETNO-WIRE` 검토 후보. 아니면 HOLD.

---

## 3) 핵심 숫자 (JSON)

### 3-1) 뇌×set_no ge3 (솔로 1장)

| 뇌 | set_no ge3 순위 (상위) |
|----|------------------------|
| **stat** | **s3 0.0262** > s1 0.0237 > s5 0.0228 |
| **markov** | **m3 0.0364** > m1 0.0338 > m5/m2 0.0305 |
| **review** | **r1 0.0372** > r2 0.0254 (r1이 최강) |

→ PATTERN1 set3 힌트는 **stat·markov 솔로 ge3**에서 부분 재현. review는 set1 유지가 유리.

### 3-2) 발권 정책 (5장 best)

| policy | mean | ge3 | Δge3 vs V2 | p vs null |
|--------|------|-----|------------|-----------|
| **v2_asc** (현행) | **1.7504** | **0.1447** | 0 | 0.000679 |
| markov_skip2 {1,3,5} | 1.7394 | 0.1438 | −0.0009 | — |
| markov_mid/hi | — | ≤0.1379 | ↓ | — |
| slot_both3 | 1.7420 | 0.1345 | −0.0102 | — |
| **grid best: m{1,2,3}+s3+r1** | **1.7623** | **0.1481** | **+0.0034** | **0.000197** |

격자 top: V2 대비 ge3 +4건(171→175)·ge4 12→16·mean +0.0119.  
**의미임계 +0.005 미달** → gates.PASS=**false**.

---

## 4) Verdict

| gate | 결과 |
|------|------|
| any_beats_v2_ge3 | **true** (+0.0034) |
| best_pass_vs_null | **true** |
| best_delta_ge3 ≥ 0.005 | **false** |
| **PASS → WIRE** | **FAIL** |

**결론:** set_no 축은 V2와 직교로 **관측 가치 있음**. 다만 개선폭이 작아 **coordinator 수정·WIRE 금지**. V2 set_no_asc 유지.  
형 GO로 `stat` 슬롯만 set3 실험 배선은 가능하나, 본 게이트상 **비권고**.

---

## 5) 실패시 HOLD / NEXT

- **WIRE/coordinator 수정 금지**  
- LIVE V2 (`MARKOV_WIRE_ENABLED=True` · set_no 쿼터) **유지**  
- NEXT=`K-ATTACK-HOLD` — 다음 축은 형·커서 재선정 (SETNO 재탕 금지 · Δ 미소)

---

## 6) 산출물

- `tools/_k_setno_hitmap_survey.py`
- `docs/benchmarks/20260729_KSETNO_hitmap.json`
- 본 보고서 · `My_Drive_Sync/커서보고서/` 복사
