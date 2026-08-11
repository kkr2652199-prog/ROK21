# K-TIER-ROLE-SLOTS-SPEC — LIST_V3 L2b

시각: 2026-08-12 KST · **DOC_OK** · wire=**False** · **1237아님** · ge3/등수 **성적클레임 금지**  
선행: L2 원장SPEC **DOC_OK** · 분석 `20260812_KTIER_ROLE_SLOTS_ANALYSIS.md`  
코드 APPLY: **L4b만** (본 문서=계약·게이트·테스트 항목)

---

## 0) 한 줄

형 「5+3등용3+2등용2 / 몰아주기=1등5」→ 앱에서는 **역할 슬롯**으로만 구현.  
**등수 확률↑ 게이트·보너스 맞춤 2등 하드옵트는 PASS.**

---

## 1) 역할 ID (고정 문자열)

| role | 장수 | set_no | 생성 패스 | 성공 정의 (게이트) | 금지 |
|------|------|--------|-----------|-------------------|------|
| `skill_native` | 5 | 1~5 | pass0 | 현행 `predict_sets` 동일 · prefer/prize 비악화 | 스킬 교차공유 |
| `cover_r3` | 3 | 6~8 | pass1a | 포트폴리오 커버(겹침↓·본5 지향) · **모니터** | P(3등)↑ 클레임 |
| `shape_r2` | 2 | 9~10 | pass1b | 5+보너스 **형태 공간**만 · **모니터** | bonus를 입력으로 사용 |
| `focus_r1` | 5 | repack 1~5 | repack | 원장+signal_union 압축 · prefer/prize 비악화 | BT등수로 APPLY |

기계 스키마: [`docs/benchmarks/20260812_KTIER_ROLE_SLOTS_SCHEMA.json`](../docs/benchmarks/20260812_KTIER_ROLE_SLOTS_SCHEMA.json)

---

## 2) pool JSON 필드 계약

각 pool/repack 세트 객체에 필수:

```json
{
  "set_no": 7,
  "nums": [3, 16, 19, 22, 27, 41],
  "brain_tag": "stat",
  "kind": "pool",
  "role": "cover_r3",
  "role_pass": "pass1a"
}
```

| 필드 | 규칙 |
|------|------|
| `role` | 위 4종 중 하나 (도입 전 null 허용 · L4b 이후 필수) |
| `role_pass` | `pass0` \| `pass1a` \| `pass1b` \| `repack` |
| ledger | L2 `testlotto_pool_hit_ledger.role` 과 동일 문자열 |

---

## 3) 생성 규칙 (L4b 구현 계약 · 이번 턴 미코드)

### 3-1. pass0 — `skill_native` (set 1~5)
- 현행: `expand_pool` pass_idx=0 · `predict_sets(draws, 5)` · 뇌별 시드리셋 유지.
- **행동 변경 없음** (라벨만 부착 가능).

### 3-2. pass1a — `cover_r3` (set 6~8)
- 같은 뇌 · 같은 draws · **타깃 정답 미사용**.
- 목적: 세트 간 번호 겹침을 `skill_native`보다 낮추거나, 부분커버에 유리한 다양성(뇌 hint는 **해당 뇌만**).
- 구현 후보(L4b에서 1개만 선택·게이트):  
  - (A) pass1 시드 오프셋 + diversity 강화 픽 3장  
  - (B) skill 10후보 중 Jaccard 낮은 3장 재선별  
- **금지:** 실제 당첨 5맞 최적화 목적함수 · ge3 게이트.

### 3-3. pass1b — `shape_r2` (set 9~10)
- 목적: “5맞+보너스” **형태** — 예: 핵심5 고정 후보 + 6번째 슬롯 가변(다양성).  
- **`bonus` / 미래 보너스 번호 입력 금지** (`no_bonus_peek`).
- 보너스가 세트에 들어가는지는 **사후 원장**으로만 관측.

### 3-4. repack — `focus_r1` (1~5)
- `repack_by_brain` 결과에 `role=focus_r1` 부착.
- L4 이후: 원장 SSOT 소비가 주신호 · EMA는 과도기 병행.
- assemble=`signal_union` 유지(변경 시 별도 게이트).

### 3-5. 뇌 독립
- stat / markov / review **각각** 위 10+5를 가짐.
- hint·점수·role 생성에 **타뇌 상태 공유 금지** (quota 상대정규화만 예외·발권 경로).

---

## 4) no_bonus_peek 테스트 항목 (L4b 필수)

| ID | 내용 | 기대 |
|----|------|------|
| T-NB1 | `shape_r2` 생성 함수 시그니처에 bonus/actual 없음 | 정적/단위 |
| T-NB2 | monkeypatch로 bonus를 주입해도 `shape_r2` nums 불변 | 단위 |
| T-NB3 | cover/shape/focus 경로에서 `_get_draws_before(target)`만 사용 · target 당첨행 미조회 | 코드·스모크 |
| T-NB4 | ledger 쓰기만 actual 사용 · 같은 draw의 role 생성과 분리 | 아키텍처 |

---

## 5) 게이트 초안 (L4b APPLY 조건)

| 조건 | 기준 |
|------|------|
| knobs precheck | L1과 동일 잠금값 |
| preferΔ | >0 · split 양수 (기존 건강) |
| prizeΔ | <0 · cn≥2/3 |
| V2/L1 대비 | drift **모니터** · 단독 APPLY 근거 아님 |
| 발권경로 | mean/hits 병기 모니터 |
| r1/r2/r3 count | **모니터만** · 게이트 금지 |
| 라벨 | pool10 전부 role 채움 · set_no↔role 표 일치 |
| 실패 | **HOLD + 롤백** · 강제BT 금지 상태 유지 |

---

## 6) 파일 터치 예정 (L4b · 참고만)

| 파일 | 변경 |
|------|------|
| `app/testlotto/signal_pool.py` | `expand_pool` role 분기 · repack role 메타 |
| `app/testlotto/pool_view_cache.py` | schema bump 시 role 포함 |
| ledger writer (L3) | `role` 컬럼 채움 |
| coordinator | **기본 미수정** (발권 통합=L12) |

동결: `random.choices` · `_get_draws_before` · boost 상한 미수정.

---

## 7) PASS 재확인

- 등수P↑ / “3등 전용=3등 잘됨” 문장
- 보너스 맞춤 2등
- 10장 covering 1등 보장
- L2b에서 models/expand_pool **코드 APPLY**

---

## 8) 판정

**DOC_OK** · wire=**False**.

다음 실행 순서: **L3 원장 WIRE** → (L5 감사 권장) → L4 원장소비 → **L4b 역할 WIRE+게이트**.

---

## 경로
- `reports/20260812_KTIER_ROLE_SLOTS_SPEC.md`
- `docs/benchmarks/20260812_KTIER_ROLE_SLOTS_SCHEMA.json`
- 분석: `reports/20260812_KTIER_ROLE_SLOTS_ANALYSIS.md`
