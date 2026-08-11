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

### L2 K-POOL-HIT-LEDGER-SPEC
- 원장 스키마: hits0~6 · hit_nums · bonus · scatter/중복 · 회차×뇌×set_no.
- (+권장) 사후 `best_tier` 모니터 필드(역할 기여 분석용 · 게이트 아님).

### L2b K-TIER-ROLE-SLOTS-SPEC
- role 필드·pass1 생성 규칙·no_bonus_peek 테스트 항목·게이트 초안 확정.
- 근거: 본 분석 보고서. **등수P 문장 금지**.

### L3 K-POOL-HIT-LEDGER-WIRE
- DB 영속 + 결과확정 경로 기록.

### L4 K-REPACK-READ-LEDGER
- 몰아주기(`focus_r1`)가 원장 SSOT 소비.

### L4b K-TIER-ROLE-SLOTS-WIRE — **게이트 후**
- pass0=`skill_native` 유지.
- pass1을 `cover_r3`×3 + `shape_r2`×2 로 분화(뇌 스킬 hint 유지·교차공유 금지).
- repack 메타 `role=focus_r1`.
- 실패 시 HOLD·롤백. 강제BT는 이후.

### L5 K-BRAIN10-SKILL-AUDIT
- 역할 도입 전/후 뇌 스킬 정합 감사.

### L6~L8 뇌별 10세트 스킬 패치
- L5 결함 시에만 (stat / markov / review).

### L9 K-REPACK-PRESERVE-PROBE
### L10 K-TICKET-COVER-LITE
### L11 축 심화 잔여 (중복 스윕 주의)
### L12 발권↔10+5 통합 (형 승인)

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
| **L2** | **NEXT** |
| L2b~L12 | 대기 |

---

## 경로
- **실행 SSOT:** `reports/20260812_KNEXT_LIST_V3.md`
- 분석: `reports/20260812_KTIER_ROLE_SLOTS_ANALYSIS.md`
- 이력: `reports/20260812_KNEXT_LIST_V2.md` · `KNEXT_UPPER_HIT_LIST.md`
