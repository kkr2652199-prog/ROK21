# K-POOL-HIT-LEDGER-SPEC — LIST_V3 L2

시각: 2026-08-12 KST · **DOC_OK** · wire=**False** · **1237아님** · ge3미클레임  
선행: L1 **SMOKE_OK** · LIST_V3  
다음 코드: **L3 WIRE만** (본 문서는 스키마·계약만)

---

## 0) 목적

과거 회차에서 뇌별 **10세트(+repack5 선택)** 의 적중을 **1~6개·보너스·분산·중복**까지 남기고,  
다음 타깃 몰아주기(`focus_r1`)가 **EMA 재계산만이 아닌 DB SSOT**를 읽게 한다.

- **쓰기:** 결과 확정 후 (draws[N] 존재 · as_of=N)
- **읽기:** 타깃 M 예측 시 **draw_no &lt; M** 만 (no_peek)
- **금지:** 타깃 M의 당첨번호로 M회차 원장을 만들어 같은 회차 몰아주기에 넣기

---

## 1) 현재 갭 (실측)

| 경로 | 상태 |
|------|------|
| `RollingSignalLearner` | 메모리 EMA · 매 빌드 `warm_learner`로 재계산 · 세트별 번호/보너스/분산 **미저장** |
| `testlotto_evolve_log.pool_hits_json` | 칸만 있음 · 강제BT 후 **n=0** · 세트 grain 계약 미고정 |
| `pool_view_cache` | 완성 10+5 JSON만 · 채점 원장 아님 |

→ **신규 전용 테이블**을 SSOT로 둔다. evolve_log는 요약 미러(선택)일 뿐 원장 아님.

---

## 2) 등수·채점 정의 (기존 코드와 동일)

`tier_utils.prediction_rank_tier`:
- hits=본번호 교집합 개수 (0~6)
- bonus_hit = 보너스가 세트 6번호 안에 있으면 1
- tier: 6→1등 · 5+bonus→2등 · 5→3등 · 4→4등 · ≥3→5등

원장은 **hits/bonus를 전부 저장**. tier는 **모니터 필드**(게이트·성적클레임 금지).

---

## 3) 테이블 스키마안 (L3에서 CREATE)

### 3-1. 세트 grain — `testlotto_pool_hit_ledger` (SSOT)

```sql
CREATE TABLE IF NOT EXISTS testlotto_pool_hit_ledger (
  draw_no       INTEGER NOT NULL,          -- 채점 회차 (결과 확정)
  brain_tag     TEXT    NOT NULL,          -- stat|markov|review
  kind          TEXT    NOT NULL,          -- pool|repack
  set_no        INTEGER NOT NULL,          -- pool 1..10 · repack 1..5
  nums_json     TEXT    NOT NULL,          -- [6 ints] sorted
  hits          INTEGER NOT NULL,          -- 0..6 본번호
  hit_nums_json TEXT    NOT NULL,          -- 맞은 본번호 목록 sorted
  miss_nums_json TEXT   NOT NULL,          -- 세트 중 비적중 본번호
  bonus         INTEGER NOT NULL DEFAULT 0,
  bonus_hit     INTEGER NOT NULL DEFAULT 0,-- 0|1
  tier_rank     INTEGER NOT NULL DEFAULT 0,-- 모니터 0..5
  role          TEXT,                      -- skill_native|cover_r3|shape_r2|focus_r1|NULL(도입전)
  seed          INTEGER NOT NULL DEFAULT 42,
  schema_version INTEGER NOT NULL DEFAULT 1,
  note          TEXT DEFAULT '',
  created_at    TEXT DEFAULT (datetime('now','localtime')),
  PRIMARY KEY (draw_no, brain_tag, kind, set_no)
);
CREATE INDEX IF NOT EXISTS idx_pool_hit_ledger_draw
  ON testlotto_pool_hit_ledger(draw_no);
CREATE INDEX IF NOT EXISTS idx_pool_hit_ledger_brain
  ON testlotto_pool_hit_ledger(brain_tag, draw_no);
```

### 3-2. 회차×뇌 요약 — `testlotto_pool_hit_scatter` (파생)

10세트에 흩어진 적중번호 집약. L3에서 ledger INSERT 직후 upsert.

```sql
CREATE TABLE IF NOT EXISTS testlotto_pool_hit_scatter (
  draw_no         INTEGER NOT NULL,
  brain_tag       TEXT    NOT NULL,
  kind            TEXT    NOT NULL DEFAULT 'pool', -- pool 요약 기본
  union_hit_nums_json TEXT NOT NULL,  -- 10세트 합집합 적중번호
  num_set_count_json  TEXT NOT NULL,  -- {"12":3,"18":1,...} 번호→출현세트수
  dup_hit_nums_json   TEXT NOT NULL,  -- 2세트 이상에 등장한 적중번호
  sets_with_hits      INTEGER NOT NULL, -- hits>=1 인 세트 수
  max_hits_in_set     INTEGER NOT NULL,
  sum_hits            INTEGER NOT NULL, -- 세트 hits 합(중복 카운트)
  bonus_hit_set_count INTEGER NOT NULL DEFAULT 0,
  schema_version  INTEGER NOT NULL DEFAULT 1,
  updated_at      TEXT DEFAULT (datetime('now','localtime')),
  PRIMARY KEY (draw_no, brain_tag, kind)
);
```

---

## 4) JSON 계약 (벤치/API 공용)

파일 SSOT: [`docs/benchmarks/20260812_KPOOL_HIT_LEDGER_SCHEMA.json`](../docs/benchmarks/20260812_KPOOL_HIT_LEDGER_SCHEMA.json)

### 4-1. set_row
```json
{
  "draw_no": 1236,
  "brain_tag": "markov",
  "kind": "pool",
  "set_no": 3,
  "nums": [7, 12, 20, 28, 30, 31],
  "hits": 2,
  "hit_nums": [12, 28],
  "miss_nums": [7, 20, 30, 31],
  "bonus": 10,
  "bonus_hit": 0,
  "tier_rank": 0,
  "role": null,
  "seed": 42,
  "schema_version": 1
}
```

### 4-2. scatter_row
```json
{
  "draw_no": 1236,
  "brain_tag": "markov",
  "kind": "pool",
  "union_hit_nums": [12, 18, 28, 34],
  "num_set_count": {"12": 3, "18": 1, "28": 2, "34": 1},
  "dup_hit_nums": [12, 28],
  "sets_with_hits": 6,
  "max_hits_in_set": 3,
  "sum_hits": 11,
  "bonus_hit_set_count": 1,
  "schema_version": 1
}
```

규칙:
- `hits` ∈ 0..6 · `len(hit_nums)==hits` · `hit_nums ∪ miss_nums == nums` · 교집합 공집합
- `bonus_hit==1` ⇒ `bonus ∈ nums`
- 1·2개만 저장하지 않음 · **0~6 전부** 행으로 남김(hits=0도 행 유지 → 분산 분석 가능)

---

## 5) 쓰기·읽기 시점

```text
[결과 N 확정]
  pool/repack(캐시 또는 재생성, seed=MC_SEED)
  → 각 세트 score vs draws[N]
  → INSERT ledger (+ scatter upsert)
  → (선택) evolve_log.pool_hits_json 요약 미러

[타깃 M 예측]  (M > 모든 읽은 draw_no)
  SELECT ... WHERE draw_no < M
  → 집계/가중 → repack focus_r1 (L4)
  → RollingSignalLearner는 과도기 병행 가능, L4 후 SSOT=ledger
```

no_peek 검증 (L3 테스트):
1. ledger.max(draw_no) &lt; target 또는 읽기 쿼리에 `draw_no < target`
2. 쓰기 함수에 actual을 target 재료로 넘기는 경로 없음

---

## 6) 강제리셋·재적재

| 이벤트 | 동작 |
|--------|------|
| `_k_predict_reset` / 강제BT | ledger·scatter **삭제 대상에 포함**(예측 산출물) · draws 보존 |
| 재적재 | WF로 1137~1236 등 구간 재채점 INSERT (L3 도구) |
| 패치 중 | 강제BT **보류**(LIST_V3) · L3 안정 후 |

---

## 7) L3 완료조건 (미리 고정 · 본 턴 미실행)

- [ ] models.py CREATE + init
- [ ] writer: draw_no 확정 후 3뇌×(pool10[+repack5])
- [ ] 샘플 1회차 원장 실측 JSON
- [ ] no_peek unit
- [ ] reset 목록에 테이블 포함
- [ ] **repack 소비는 L4** (L3에서 읽기 stub만 허용)

---

## 8) 판정

**DOC_OK** · wire=**False** · 코드/DB 스키마 미적용(의도).

---

## 경로
- `reports/20260812_KPOOL_HIT_LEDGER_SPEC.md`
- `docs/benchmarks/20260812_KPOOL_HIT_LEDGER_SCHEMA.json`
- LIST: `reports/20260812_KNEXT_LIST_V3.md`
