# [CURSOR 작성] K-TRANSITION 방향성·논의 종합 브리핑 — 외부 AI 판독용

> **작성자:** Cursor Agent (ROK21 실행 AI) · **NOT** 젠스파크 · **NOT** 형 직접 작성  
> **작성일:** 2026-08-05 KST · **HEAD(작성 시점):** `88ba6bd`  
> **목적:** 형·젠스파크·외부 AI가 **혼동 없이** K-TRANSITION 논의 전체를 읽도록 **커서 단독 종합본**  
> **수치 SSOT:** `docs/benchmarks/*.json` — **본 MD는 해설·링크만** (수치 확정은 JSON raw fetch)

---

## 0) 외부 AI 판독 규칙 (필수)

| 규칙 | 내용 |
|------|------|
| **작성 주체** | 본 파일 = **Cursor가 작성·commit·push**한 실행 기록 |
| **젠스파크와 구분** | 젠스파크 = 전략·검토·초안. **코드·벤치·push = Cursor** |
| **수치 신뢰 순위** | ① `docs/benchmarks/*.json` raw ② 본 MD ③ 채팅 기억 **(불신)** |
| **wire/GO** | 본 MD에 "즉시착수" = **설계 착수**이지 engine wire **아님** |
| **형 GO** | stat 교체·quota·wire 전부 **형 명시 GO 전 금지** |

압축 복구 시: `GENSPARK_COMPRESS_RECOVER.md` → 본 파일 → JSON 1~2개 fetch → 팩트체크.

---

## 1) 한 줄 방향 (North Star · 형 확정 · **Cursor 2026-08-05 정정**)

**「과거 회차는 단서다」** — 회차 N과 번호 **2+ 겹치는** 과거 회차들의 **다음 회차 빈도** + **이월(carry)** 패턴을 **먼저 수집·기록**하고, 재검증 후 약한 뇌(stat)를 **그 패턴 엔진으로 재설계**, 성공 시 **1236~ 자동 학습**.

- 독립 추첨 전제 · 1등 보장 **없음**
- **지금 단계 = 패턴 수집 설계** (발권·wire·뇌 교체 **아님**)
- 정정 SSOT: `reports/20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR.md` (**Cursor**)

---

## 2) 진행 단계 (어디까지 왔는지 · **정정**)

| # | 단계 | 상태 | 산출물 (Cursor 작성) |
|---|------|------|----------------------|
| 1 | 1234→1235 ad-hoc 분석 | ✅ | 채팅 + 팩트체크 MD |
| 2 | 전회차 rolling 101~1235 | ✅ STRONG | `20260805_KTRANSITION_FULL.json` |
| 3 | 팩트체크·무작위 sanity·로드맵 | ✅ | FACTCHECK · RANDOM_SAMPLE · ROADMAP MD |
| 4 | 종합 브리핑 | ✅ | **본 파일** |
| 4b | **방향 정정 브리핑** | ✅ | `DIRECTION_BRIEF_CURSOR` · JSON |
| 5 | **패턴 수집(DB/로그) 설계** | ⏳ | **형 GO** ← **지금** |
| 6 | 수집 데이터 재검증 | ⏳ | 수집 후 |
| 7 | stat 뇌 재설계 | ⏳ | 재검증·형 GO 후 |
| 8 | engine wire / 발권 / 자동학습 | 🚫 | 확실 전 금지 |

---

## 3) 형 요청 흐름 (대화에서 확정된 논리)

1. **1234 회차** — 과거 유사(2+ 겹침) → 다음 회차 빈도 + carry
2. **1235**와 대조 — “이 패턴으로 다음 회차 힌트”
3. **1233·1234·임의 회차** 동일 분석 → **전 회차 rolling** = `K-TRANSITION-FULL`
4. **최종 목표** — 전 회차 저장 → 미래 회차 **자동 적용** (stat 뇌 경유)

Cursor가 seed=20260805로 **무작위 5회+1234** 단건 재분석 → 전건 hit=2 (baseline) → **단건은 rolling STRONG을 대표 못함** 확인.

---

## 4) 수치 SSOT — K-TRANSITION-FULL

**파일:** `docs/benchmarks/20260805_KTRANSITION_FULL.json`  
**도구:** `tools/_k_transition_full.py` · wire=`false` · READ-ONLY

### sim_k2 (주 지표 · 공통번호 ≥2)

| 항목 | 값 |
|------|-----|
| range | 101~1235 · n=**1135** |
| mean_hit | **2.171806** |
| baseline | **2.000** (= 15×6/45) |
| delta | **+0.171806** |
| verdict | **STRONG** (Δ≥0.15) |
| mean_n_similar | **116.822** |
| hit_dist | 0:62 · 1:246 · **2:397** · 3:310 · 4:106 · 5:13 · 6:1 |

### sim_k3 / sim_k4

| 조건 | n_valid | delta | verdict |
|------|---------|-------|---------|
| sim_k3 (≥3) | 811 | +0.065 | MARGINAL |
| sim_k4 (≥4) | 0 | — | NOISE (표본<10) |

### carry_analysis

| 항목 | 값 |
|------|-----|
| full_dist (0~4) | 477 · 523 · 208 · 24 · 2 |
| mean_carry | 0.826 |
| 1235 carry | **2** · nums **[15, 43]** |
| pred_1236 \| carry=2 | 0:33.8% · **1:48.8%** · 2:15.9% · 3:1.4% (n=207) |

### brain_replace (JSON 원문 → **Cursor 운용 정정**)

- JSON 원문 target: **stat** · verdict: **즉시착수**
- **운용 정정(2026-08-05):** 「즉시착수」= **수집 충분히 끝난 뒤** 설계 착수. **지금은 수집 STEP**. wire 아님.
- markov/review **유지**

---

## 5) 1234→1235 팩트체크 (Cursor 재계산 = JSON 일치)

**파일:** `reports/20260805_KTRANSITION_FACTCHECK.md`

| 항목 | 값 | 일치 |
|------|-----|------|
| 1234 당첨 | [1,15,19,31,35,43] | ✅ |
| 1235 당첨 | [6,7,11,15,39,43] | ✅ |
| carry 1234→1235 | [15,43] count=2 | ✅ |
| 유사회차 (2+) | **212** | ✅ |
| top15 → 1235 hit | **2** (7, 15) | ✅ baseline |

**주의 (외부 AI 혼동 금지):** top20 정성 “6,7,15,39 적중” ≠ top15 정량 **hit=2**. 1234 단건 **대박 아님**.

---

## 6) 무작위 표본 sanity (Cursor 단건 분석)

**파일:** `docs/benchmarks/20260805_KTRANSITION_RANDOM_SAMPLE.json`  
**seed:** 20260805 · picks: **369, 442, 1024, 1152, 1216** + 기준 **1234**

| N | 유사건 | hit | vs 2.0 |
|---|--------|-----|--------|
| 369 | 67 | 2 | at |
| 442 | 74 | 2 | at |
| 1024 | 165 | 2 | at |
| 1152 | 202 | 2 | at |
| 1216 | 228 | 2 | at |
| 1234 | 212 | 2 | at |

**6/6 at baseline** · sample mean=2.0 vs rolling 2.172 → **단건 검증 변별력 약함**.

---

## 7) 3뇌 구조 · 교체 방향

| 뇌 | 현재 | Cursor 판단 |
|----|------|-------------|
| markov | ~80% quota · ge3 기여 | **유지** |
| review | ~20% · seed STABLE | **유지** |
| stat | **0%** · seed HIGH · 성능 낮음 | **교체** → sim_k2 transition hint |

### 같이 읽어야 할 교훈 (K-QUOTA-D-WIRE · FAIL)

- PREP repack ge3=0.170 ≠ live `predict_sets` ge3=0.10~0.115
- **quota/stat 변경은 live coordinator WF 후에만 GO**
- 현재 `BENCH_FIXED_QUOTA=None` (롤백 상태)

**파일:** `reports/20260805_KQUOTA_D_WIRE.md`

---

## 8) 기각·보류 축 (혼동 방지)

| ID | verdict | 외부 AI 메모 |
|----|---------|--------------|
| K-ASSOC-RULE-DIAG | NOISE | 연관규칙 wire 보류 |
| K-NEIGHBOR-MATCH | NOISE | kNN top15 < random |
| K-QUOTA-D-WIRE | FAIL | stat quota↑ live 붕괴 |
| 단건 1234 “성공” | 기각 | hit=2 = baseline |

---

## 9) 다음 1건 (NEXT_ACTIONS · Cursor 정정 2026-08-05)

> **정정:** JSON `brain_replace=즉시착수` = rolling 판정용. **지금 실행 = 패턴 수집 설계** (stat wire **아님**).  
> 상세: `reports/20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR.md`

```
ID: K-TRANSITION-COLLECT-DESIGN
할일: transition 패턴 수집(DB/로그) 설계 · 회차별 유사→freq 저장 · wire/뇌/발권 미접촉
완료조건: 형 GO
선행완료: docs/benchmarks/20260805_KTRANSITION_FULL.json
```

### 확정 순서 (Cursor)

| STEP | 내용 | 상태 |
|------|------|------|
| 1 | 패턴 **수집** 설계 (테이블/로그·backfill READ) | **← 지금** |
| 2 | 수집 데이터 재검증 | 대기 |
| 3 | stat → 전이 엔진 재설계 | 형 GO 후 |
| 4 | 발권 반영 + 주간 자동학습 | 형 GO 후 |

---

## 10) Cursor 작성 산출물 인덱스 (전체)

| 유형 | 경로 |
|------|------|
| **종합 브리핑 (본문)** | `reports/20260805_KTRANSITION_CURSOR_BRIEF_FOR_EXTERNAL_AI.md` |
| **방향성 SSOT (Cursor)** | `reports/20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR.md` |
| 방향성 JSON 마커 | `docs/benchmarks/20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR.json` |
| rolling SSOT | `docs/benchmarks/20260805_KTRANSITION_FULL.json` |
| rolling 보고서 | `reports/20260805_KTRANSITION_FULL.md` |
| 팩트체크 | `reports/20260805_KTRANSITION_FACTCHECK.md` |
| 무작위 JSON | `docs/benchmarks/20260805_KTRANSITION_RANDOM_SAMPLE.json` |
| 무작위 MD | `reports/20260805_KTRANSITION_RANDOM_SAMPLE.md` |
| 로드맵 | `reports/20260805_KTRANSITION_DISCUSS_ROADMAP.md` |
| 도구 | `tools/_k_transition_full.py` |
| Drive 복사 | `My_Drive_Sync/커서보고서/` (동명) |
| 협업 규칙 | `My_Drive_Sync/SUMMARY/AI_COLLAB.md` §3 |
| 다음 1건 | `My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md` |

---

## 11) 의사결정 트리 (외부 AI용)

```
K-TRANSITION sim_k2 STRONG (Δ+0.172, n=1135)
        │
        ▼
stat 뇌 = transition hint 설계 (wire=False, Cursor 실행)
        │
        ▼
live WF ge3 ≥ 0.135 (fusion baseline)?
   ├─ YES → 형 GO → 소규모 wire 테스트
   └─ NO  → 가중·top_m 조정, wire 보류
```

---

## 12) 요약 3줄 (복붙용)

1. **방향:** 1234 패턴 → rolling STRONG → stat 교체 → (미래) 자동 힌트.  
2. **지금:** 검증·기록 완료 — **설계만**, wire **전**.  
3. **신호:** rolling +0.17 (미세) · 단건=baseline — **과장 금지**.

---

_Cursor Agent · ROK21 · kkr2652199-prog/ROK21 · main · D:\ROK21 · port 7021_  
_본 문서 수정·push = Cursor 실행 결과. 젠스파크는 검토·코멘트만._
