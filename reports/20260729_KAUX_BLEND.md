# K-AUX-BLEND — AUX_WEIGHTS / aux_score*40 점수 레버 관측

📅 2026-07-29 · DB/coordinator **미수정** · `db_code_write=false`  
선정축 ID: **K-AUX-BLEND**  
도구: `tools/_k_aux_blend_survey.py`  
JSON: `docs/benchmarks/20260729_KAUX_BLEND_survey.json`  
V2 pin: ge3=**0.1447** · mean=**1.7504**

---

## 0) 선정 요약

| 항목 | 값 |
|------|-----|
| **선정축** | **K-AUX-BLEND** |
| 가설 | V2 set_no 발권 고정 시, 발권전 AUX 합성점수(live 0.25×4 · warrant 재가중 · `*40`)가 matched와 유의 양상관이면 `AUX_WEIGHTS`/`aux_score*40` 이 실재 레버 |
| V2와 직교 | 예 — 뇌쿼터·set_no_asc **불변** · 점수만 관측 |
| 슬롯재선택 | **아님** — 대체점수 픽 0건 |
| 관측 | **실행완료** (~59s · brain_review + aux `score_set`) |
| 판정 | **FAIL(WIRE금지)** — 전 blend/성분 |r|<0.03 또는 양상관 게이트 미달 |
| 실패시 | **HOLD · V2 유지** |

**왜 슬롯/GENDIV가 아닌가:** 발권은 V2 `set_no_asc` 고정이고, 관측은 AUX 점수↔적중 상관·팩 mean_aux 오분위만 본다. diversify/Jaccard·슬롯 재픽 없음.

---

## 1) 후보 2~4개 → 1건

| # | 후보 ID | 가설 스케치 | 기각/선정 |
|---|---------|-------------|-----------|
| A | **K-AUX-BLEND** ✅ | `AUX_WEIGHTS`·`aux_score*40` 점수↔적중 | **선정** |
| B | K-SETS-MIX15 | 뇌별 생성개수(7/5/3) | brain_review 뇌당5 고정 · SETCOUNT/재생성 인접 · V2 fillable trunc 시 티켓동일 |
| C | K-AUX-THRESH | 문턱으로 슬롯픽 | BAND에서 기각 · 슬롯재선택=금지 |
| D | K-STATP | stat×pattern | PATTERN2/STRUCT 인접 |

**코드 앵커:** `coordinator.AUX_WEIGHTS=[0.25]*4` · `final_conf … + aux_score*40` · 4모듈 `score_set`.

---

## 2) 관측 방법

1. `testlotto_brain_review` draw 53~1234 · 3뇌×5 · n=**1182** · pool sets=**17730**
2. 각 세트에 miss/pattern/balance/referee `score_set` (as_of=target · draws before)
3. blend: live / warrant_emp / pattern_heavy / balance_heavy / miss_off / equal_emp3
4. 발권 = V2 `{m:1,2,3 / s:1 / r:1}` set_no_asc **고정** (재픽 없음)
5. spearman(점수, matched) · V2팩 mean_aux 오분위(보조)

**PASS 기준 (사전):**  
live 또는 best blend (또는 성분) spearman **r≥0.03 AND p<0.05 AND r>0**  
→ 충족 시만 `K-AUX-BLEND-WIRE` **후보 보고**(형 GO 전 coordinator 패치 금지). 아니면 HOLD.  
Q5는 보조관측(비단조면 무시).

---

## 3) 핵심 숫자

### 3-1) V2 baseline 재확인

| 지표 | 값 |
|------|-----|
| n | **1182** |
| mean / ge3 | **1.7504** / **0.1447** |
| p vs null(0.1137) | **0.000679** |

### 3-2) 성분 상관 (pool 17730)

| 성분 | r | p | 비고 |
|------|---|---|------|
| miss | 0 | 1 | **constant** (본 표본) |
| pattern | **0.0139** | 0.063 | FAIL |
| balance | 0.0085 | 0.257 | FAIL |
| referee | 0 | 1 | **constant**=0.5 |

### 3-3) blend 상관

| blend | r | p | 게이트 |
|-------|---|---|--------|
| live_025 | 0.0134 | 0.075 | FAIL |
| warrant_emp | 0.0134 | 0.075 | FAIL |
| **pattern_heavy** (best) | **0.0152** | **0.043** | FAIL (|r|<0.03) |
| balance_heavy | 0.0117 | 0.121 | FAIL |
| live×40 | 0.0134 | 0.075 | FAIL (단조변환) |
| stored confidence | 0.0058 | 0.440 | FAIL |
| V2티켓 live aux | **0.0272** | 0.037 | FAIL (|r|<0.03) |

### 3-4) V2팩 mean_aux 오분위 (live · 보조)

| Q | mean_aux | ge3 | Δ vs V2 |
|---|----------|-----|---------|
| Q1 | 0.717 | 0.1483 | +0.0036 |
| Q4 | 0.743 | **0.1780** | +0.0333 |
| Q5 | 0.752 | 0.1561 | +0.0114 |

Q5−Q1=+0.0078이나 **Q4>Q5** → 고aux 단조 우세 **아님**. 상관 게이트와 합쳐 FAIL.

---

## 4) Verdict

| gate | 결과 |
|------|------|
| any_positive_corr_pass | **false** |
| live_corr_pass | **false** |
| best_blend_corr_pass | **false** |
| **PASS → WIRE** | **FAIL** |

**결론:** AUX 가중/스케일 점수는 matched를 설명하지 못함. **AUX_WEIGHTS·`*40` WIRE 금지**. V2·균등 0.25 유지.

---

## 5) 실패시 HOLD / NEXT

- **WIRE/coordinator 수정 금지**
- LIVE V2 유지
- NEXT=`K-ATTACK-HOLD` — AUX-BLEND 재탕금지 · 다음 축 재선정
- 재탕금지 추가: **AUX-BLEND** (기존 GENDIV/SUM/BAND/EV/SETNO/SETPACK/TUNE/conf-quota/HISIM·STRUCT·COVER/GATHER에 합류)

---

## 6) 산출물

- `tools/_k_aux_blend_survey.py`
- `docs/benchmarks/20260729_KAUX_BLEND_survey.json`
- 본 보고서 · `My_Drive_Sync/커서보고서/` 복사

---

## 팩트체크

| 항목 | JSON | 보고서 | STATUS/BOOT/NEXT | 판정 |
|------|------|--------|------------------|------|
| 축ID | K-AUX-BLEND | 동상 | K-AUX-BLEND | OK |
| 가설 | AUX점수↔matched → WEIGHTS/scale 레버 | 동상 | 동상 | OK |
| n / V2 ge3 / mean | 1182 / 0.1447 / 1.7504 | 동상 | 동상 | OK |
| 최근접신호 | pattern_heavy r=0.0152 · V2티켓 r=0.0272 | 동상 | 동상 | OK |
| gates.PASS | false | FAIL | FAIL·HOLD | OK |
| recommended_next | null | 없음(HOLD·V2유지) | K-ATTACK-HOLD | OK |
| db_code_write / coordinator | false / 미수정 | 동상 | WIRE금지 | OK |
| 슬롯재선택 아님 | not_slot_reselect=true | 1줄 명시 | — | OK |
