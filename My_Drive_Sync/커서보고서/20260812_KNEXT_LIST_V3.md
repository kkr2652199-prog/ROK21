# K-NEXT-LIST-V3 — 실행 SSOT (역할슬롯 보강)

시각: 2026-08-12 KST · HEAD≈`5f924d0` · **양산前** · **1237아님** · ge3/등수 **성적클레임 금지**  
승계: V2 + 형 「5 skill + 3(3등지향) + 2(2등지향) / 몰아주기5=1등지향」  
분석: `reports/20260812_KTIER_ROLE_SLOTS_ANALYSIS.md` (**등수P↑ PASS · 역할슬롯 채택**)

---

## 0) 설계 합의 (누적)

### 0-1. 적중 원장
- 세트당 **1~6 + 보너스**, 번호는 **10세트에 분산** 가능 → 과거 확정 후 DB 저장 → 다음 예측 반영.
- 컨닝 아님(타깃 정답 미사용).

### 0-2. 두 기둥
| 기둥 | 내용 |
|------|------|
| A | 뇌별 **10세트** — 스킬 엔진 (stat/markov/review) |
| B | **몰아주기 5** — 원장+신호 압축 (1등 지향 역할) |

### 0-3. 역할 슬롯 (형 추가 · 리팩터 확정)

| 구간 | 장수 | role | 의미 |
|------|------|------|------|
| set 1~5 | 5 | `skill_native` | **현행 프로세스 그대로** (pass0) |
| set 6~8 | 3 | `cover_r3` | **3등 지향 포트폴리오**(본5 구조·커버). P(3등)↑ 비주장 |
| set 9~10 | 2 | `shape_r2` | **2등 지향 형태만**(5+보너스 공간). **보너스 직접예측 PASS** |
| repack 1~5 | 5 | `focus_r1` | **1등 지향 압축**(원장·signal_union 강화) |

**PASS 확정:** 등수 확률↑ 클레임 · 보너스맞춤 2등 하드옵트 · 10장 covering으로 1등보장 · 스펙 전 코드 APPLY.

### 0-4. 지표
- APPLY 게이트 = prefer / prize (+커버 모니터).
- BT pool등수·r1/r2/r3 count = **모니터만**.
- 발권5 ≠ pool10+repack5 (이미 METRIC_OK).

### 0-5. 프로세스
```text
과거채점→원장DB → 타깃N: skill5 + cover_r3×3 + shape_r2×2
                 → 몰아주기 focus_r1×5
클릭발권(현행)은 분리 · 통합은 L12(형승인)
```

---

## 1) 완료 패치 (재탕 금지)

뇌독립·HINT·SCORE cand_B·BLEND/W_CROWD·union·oversample m5·referee·min_each1·K-I·K-G·K-C·①TIER45·②ISSUE_PATH·LIST_V2.  
동결3종·kweon쓰기·1237양산 금지.

---

## 2) 실행 순서 (1건씩 · 정밀)

> 강제BT: 원장+역할슬롯 안정 전 **보류**.

### L0a LIST_V2 · **DOC_OK**
### L0b LIST_V3+역할슬롯분석 · **DOC_OK (본턴)**
- `20260812_KTIER_ROLE_SLOTS_ANALYSIS.md` · 본 문서.

### L1 K-POST-REFILL-JOINT-SMOKE — **SMOKE_OK**
- refill_v2 후 prefer/prize 합동 smoke (역할·원장 손대기 **전** 베이스).

### L2 K-POOL-HIT-LEDGER-SPEC — **DOC_OK**
- 원장 스키마: hits0~6 · hit_nums · bonus · scatter/중복 · 회차×뇌×set_no.
- (+권장) 사후 `best_tier` 모니터 필드(역할 기여 분석용 · 게이트 아님).

### L2b K-TIER-ROLE-SLOTS-SPEC — **DOC_OK**
- role 필드·pass1 생성 규칙·no_bonus_peek 테스트 항목·게이트 초안 확정.
- 근거: 본 분석 보고서. **등수P 문장 금지**.

### L3 K-POOL-HIT-LEDGER-WIRE — **WIRE_OK**
- DB 영속 + 결과확정 경로 기록.
- 실측: 1236 ledger45·scatter6 · no_peek · reset목록 · `pool_hit_ledger.py`.

### L4 K-REPACK-READ-LEDGER — **WIRE_OK**
- 몰아주기(`focus_r1` 경로=`repack_by_brain`)가 원장 SSOT 소비.
- 실측: blend0.5 · seed1234~1235 → target1236 consume · no_peek · 1236계약45/6.

### L4b K-TIER-ROLE-SLOTS-WIRE — **WIRE_OK**
- pass0=`skill_native` 유지.
- pass1을 `cover_r3`×3 + `shape_r2`×2 로 분화(뇌 스킬 hint 유지·교차공유 금지).
- repack 메타 `role=focus_r1`.
- 실측: prefer+0.2947 · prize−0.1144 · no_bonus_peek · L4계약유지.

### L5 K-BRAIN10-SKILL-AUDIT — **AUDIT_OK**
- 역할 도입 전/후 뇌 스킬 정합 감사.
- 실측: HARD PASS · SOFT결함0 → L6~L8 스킵 · 다음 L9.

### L6~L8 뇌별 10세트 스킬 패치
- L5 결함 시에만 (stat / markov / review) — **본턴 스킵**.

### L9 K-REPACK-PRESERVE-PROBE — **HOLD**
- 소형 스윕 신호0 · slots2·cap4 불변.

### L9a K-BRAIN-SKILL-DATA-PERSIST-AUDIT — **AUDIT_OK** (본턴)
- 뇌별 과거분석·예측前 DATA 저장/활용 실측.
- 갭: live→review 미러 · 스킬 hint persist · EMA/ledger SSOT.
- `reports/20260812_KBRAIN_SKILL_DATA_PERSIST_AUDIT.md`

### L9b K-LIVE-FEEDBACK-REVIEW-MIRROR — **WIRE_OK** (본턴)
- click/`_auto_feedback` → `testlotto_brain_review` UPSERT + CUTOFF 캐시 무효화.
- learn 중복가드와 무관하게 review 미러.

### L9c K-SKILL-HOMEWORK-PERSIST — **WIRE_OK** (본턴)
- `testlotto_skill_homework` · 뇌별 skill_kind 분리 저장/소비.
- stat=`miss_pattern` · markov=`crowd_prefer` · review=`crowd_prize`.
- 쓰기=결과확정 · 읽기=`as_of < target` · `build_hint_by_brain` consume.

### L9d K-EMA-OR-LEDGER-SSOT — **DOC_OK** (본턴)
- 몰아주기 SSOT=원장(ledger) · EMA=메모리 warm only · EMA 테이블 신설 보류.

### L10 K-TICKET-COVER-LITE — **HOLD** (본턴)
- 발권5 Jaccard/union 소형 스윕 · 신호는 있으나 prefer/prize 비악화 실패 → knobs OFF 유지.
- `TICKET_COVER_LITE` 코드경로만 준비(기본 False).

### L11 K-REVIEW-EV-DEEPEN — **HOLD** (본턴)
- shape 세기(`PRIZE_SHAPE_STRENGTH`)만 스윕 · BLEND0.85/W_CROWD0.90 **재탕안함**.
- prize |Δ| 미달 · base prize양수 → HOLD.

### L11b K-MARKOV-PREFER-ALIGN — **HOLD** (본턴)
- 생일대 세기(`PREFER_BDAY_STRENGTH`)만 스윕 · BLEND0.55/W_CROWD0.90 **재탕안함**.
- 전후보 prefer↓ → HOLD(0.0).

### L11c K-STAT-HOMEWORK-QUALITY — **HOLD** (본턴)
- `past_learn.WIN_1Y`만 스윕 · HINT52/WEIGHT0.15/J0.85/ov×3 **재탕안함**.
- hit |Δ|≪0.005 · prefer/prize iso0 → HOLD(52).

### L12 K-TICKET-POOL-UNIFY-SPEC — **DOC_OK**
- 강제병합 **안 함**. 발권5 vs pool10+repack5 이중경로 실측.
- C8 pool1~5=predict_sets5 **PASS** · quota 발권5 ≠ 10+5 저장.
- 옵션 A~E · 권고 **E**(생성1회·캐시동기). WIRE는 형 선택 후 L12b.

### L12b K-TICKET-POOL-UNIFY-WIRE — **WIRE_OK** (본턴 · 옵션 E)
- 클릭: 생성 1회 → skill15 → quota **5** → 같은 회차 pool 캐시 10+5.
- C8 PASS · BT/`run_prediction` 불변 · `TICKET_POOL_SYNC=True`.
- LIST_V3 L0~L12b **완료**. 다음=형 다음 1건.

### L13 K-ROLE-TIER-LEARN-WIRE — **WIRE_OK** (stat만)
- 1~5 불변. 6~8/9~10 **원장 복습** (`testlotto_role_homework`).
- 소비 뇌=`stat`만. 타깃 보너스 미입력. ge3미클레임.
- 다음 뇌=markov 는 형 1건.

### L13b K-STAT-ROLE-LEARN-BT200 — **PASS**
- 리셋+stat만 200회. 1~5 ON==OFF. COVER_MIN_HITS **3** 패치(v1 표빔).
- 다음=형 1건(markov).

### L13c K-BT200-PROCESS-LEARN-AUDIT — **PASS** (READ)
- 지금 DB 200회 프로세스 5+3+2 HARD0. 학습=stat cover n_pos 증가. UI강제백테표 0=SOFT.
- 다음=형 1건(markov).

### L13d K-BT200-SCORE-CARD — **DOC_OK**
- 지금200 성적 모니터. 발권0. 1~5 mean_all **0.798**≈이론0.80. ge3미클레임.

### L13e K-BT200-TIER-COUNTS — **DOC_OK**
- 고유 1·2·3등 **0** · 4등 **1**(1117) · 5등 **55**. 발권0.

---

## 3) 매핑

| 이전 | V3 |
|------|-----|
| V2 L0~L12 | 유지 + **L0b·L2b·L4b** 삽입 |
| 형 5+3+2 / 몰아주기1등 | → role 표 (0-3) · P↑ PASS |

---

## 4) 금지 체크리스트 (추가)

- [ ] “3등 전용 = 3등 확률↑” 문장/게이트
- [ ] 예측 시 보너스 번호를 2등 슬롯 입력으로 사용
- [ ] 역할슬롯을 L1·L2 전에 코드 APPLY
- [ ] BT r1/r2/r3로 APPLY
- (기존 V2 금지항 전부 유지)

---

## 5) 진행 상태

| ID | 판정 |
|----|------|
| L0a/L0b | **DOC_OK** |
| L1 | **SMOKE_OK** |
| L2 / L2b | **DOC_OK** |
| L3 / L4 / L4b | **WIRE_OK** |
| L5 | **AUDIT_OK** |
| L6~L8 | 스킵 |
| L9 | **HOLD** |
| L9a | **AUDIT_OK** |
| L9b / L9c | **WIRE_OK** |
| L9d | **DOC_OK** |
| L10 | **HOLD** |
| L11 | **HOLD** |
| L11b | **HOLD** |
| L11c | **HOLD** |
| L12 | **DOC_OK** |
| L12b | **WIRE_OK** (E) |
| L13 | **WIRE_OK** (stat 6~8/9~10 복습) |
| L13b | **PASS** (stat BT200 · COVER_MIN_HITS=3) |
| L13c | **PASS** (지금200 프로세스·학습 AUDIT) |
| L13d | **DOC_OK** (200회 성적 모니터 안내) |
| L13e | **DOC_OK** (200회 등수 1·2·3=0 4=1 5=55) |

---

## 경로
- **실행 SSOT:** `reports/20260812_KNEXT_LIST_V3.md`
- 분석: `reports/20260812_KTIER_ROLE_SLOTS_ANALYSIS.md`
- 이력: `reports/20260812_KNEXT_LIST_V2.md` · `KNEXT_UPPER_HIT_LIST.md`
