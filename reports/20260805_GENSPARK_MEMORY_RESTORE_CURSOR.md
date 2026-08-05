# [CURSOR 작성] 젠스파크 압축 기억 복원 — 보고서 읽기 가이드

> **작성자: Cursor (ROK21 실행 AI)** · NOT 채팅 기억 · NOT 젠스파크 자체 요약  
> **목적:** 세션 압축 후, **보고서·JSON만**으로 형·젠스파크가 동일 기억을 복원한다.  
> **규칙:** 채팅 장문 = 불신. 수치·판정 = `docs/benchmarks/*.json` raw만.

---

## 0) 30초 복원 (이것만 먼저)

```
압축감지: 채팅기억 폐기 · JSON 재페치

[복귀] HEAD≈710d11a · 지금=K-TRANSITION-COLLECT-DESIGN PASS
      · 다음=COLLECT-DESIGN-DONE → STEP2 재검증(형 GO)
      · wire/뇌/발권 = 금지
```

| 키 | 값 |
|----|-----|
| SSOT | `kkr2652199-prog/ROK21` · 포트 **7021** |
| 형 의도(지금) | 패턴 **수집·기록** (발권 단계 아님) |
| 신호 | FULL sim_k2 Δ**+0.172** STRONG = **미세** |
| 수집 | `transition_log` backfill 101~1234 n**1134** PASS |
| 혼동 금지 | collect hit≈**1.998**(N→N+1) ≠ FULL **2.172**(hit@N) |

---

## 1) 우리가 합의한 전체 스토리 (시간순)

읽기 순서 = **기억 복원 순서**. 위에서 아래로.

| # | 무슨 일이었나 | 판정 | 필독 (raw) |
|---|---------------|------|------------|
| 1 | 유사≥2 → 다음회 빈도 아이디어 · 1234→1235 단건 | hit=2=baseline | FACTCHECK MD |
| 2 | 전회차 rolling 101~1235 | **STRONG** Δ+0.172 | `...KTRANSITION_FULL.json` |
| 3 | 무작위 6건 sanity | 전건 hit=2 | `...RANDOM_SAMPLE.json` |
| 4 | assoc / neighbor 등 | **NOISE** | 각 JSON |
| 5 | 형: 지금은 수집·학습, 교체·발권은 나중 | COLLECT_FIRST | `...DIRECTION_BRIEF_CURSOR.md` **[CURSOR]** |
| 6 | `transition_log` 설계·backfill·훅 | **PASS** | `...COLLECT_DESIGN.json` |

### 형 의도 한 줄 (정답 아님 · 방향)

단일 회차 “정답 예측”이 아니라, **비슷한 과거 여러 건**의 다음 번호 빈도를  
매 회차 **DB에 학습·저장** → 확실해지면 약한 뇌(stat) 재설계 → 1236~ 자동.

```
STEP1 수집 설계     ✅ COLLECT-DESIGN PASS
STEP2 재검증         ⏳ 형 GO 대기
STEP3 stat 재설계    ⏳ 재검증·형 GO 후
STEP4 발권·자동학습  🚫 확실 전 금지
```

---

## 2) 보고서 읽기 지도 (압축 복구용)

### A. 방향·역할 (먼저)

| 파일 | 왜 읽나 |
|------|---------|
| `reports/20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR.md` | **Cursor 방향 SSOT** · 수집우선 |
| `reports/20260805_KTRANSITION_CURSOR_BRIEF_FOR_EXTERNAL_AI.md` | 종합 인덱스·혼동금지 |
| `My_Drive_Sync/SUMMARY/K_ANALOG_COLLAB.md` | **별트랙 UI** · 본선 아님 |

### B. 신호 수치 (JSON raw 필수)

| 파일 | 기억할 숫자 |
|------|-------------|
| `docs/benchmarks/20260805_KTRANSITION_FULL.json` | mean_hit **2.171806** · Δ **+0.171806** · STRONG |
| `...FACTCHECK.md` | 1234 유사 **212** · hit **2** · carry **[15,43]** |
| `...RANDOM_SAMPLE.json` | 6/6 hit=2 |

### C. 수집 구조 (지금 완료분)

| 파일 | 기억할 것 |
|------|-----------|
| `docs/benchmarks/20260805_KTRANSITION_COLLECT_DESIGN.json` | PASS · rows **1134** · collect mean **1.998** · FULL재현 **2.171806** match |
| `tools/_k_transition_collect.py` | 수집 로직 · wire 없음 |
| `.cursor/hooks/transition_collect_hook.py` | stop 훅 · 자동 collect_latest |

### D. 기각축 (다시 꺼내지 말 것)

| ID | 판정 |
|----|------|
| K-ASSOC-RULE-DIAG | NOISE |
| K-NEIGHBOR-MATCH | NOISE |
| K-QUOTA-D-WIRE | FAIL (PREP≠live) |
| 「1234 대박」 | 기각 (hit=2) |
| 「stat 즉시 교체」 | **철회** → 수집 후 STEP3 |

---

## 3) 두 지표 혼동 방지 (가장 중요)

| 이름 | 정의 | 값 |
|------|------|-----|
| **FULL 신호** | 유사회차 next-freq top15 ∩ **당회 N** | mean **2.172** · STRONG |
| **collect 저장** | 같은 top15 ∩ **다음회 N+1** | mean **≈1.998** ≈ 무작위 |

→ “수집 mean이 2.172가 아니다” = **버그 아님**. 학습용(N+1)과 신호측정(N)이 다름.  
FULL 숫자는 `full_style_recheck`로 재현됨.

---

## 4) raw URL (젠스파크 fetch용)

베이스: `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/`

**필수 4개**

1. `docs/benchmarks/20260805_KTRANSITION_COLLECT_DESIGN.json`
2. `docs/benchmarks/20260805_KTRANSITION_FULL.json`
3. `docs/benchmarks/20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR.json`
4. `reports/20260805_GENSPARK_MEMORY_RESTORE_CURSOR.md` (본 파일)

**보조**

- `reports/20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR.md`
- `reports/20260805_KTRANSITION_CURSOR_BRIEF_FOR_EXTERNAL_AI.md`
- `reports/20260805_KTRANSITION_FACTCHECK.md`
- `My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md`
- `EXTERNAL_START.md`
- `My_Drive_Sync/SUMMARY/GENSPARK_COMPRESS_RECOVER.md`

---

## 5) 복구 후 첫 답 템플릿 (젠스파크용)

```
압축감지: 채팅기억 폐기 · JSON 재페치

[복귀] HEAD=<실측> · 지금=K-TRANSITION-COLLECT-DESIGN PASS
      · 다음=STEP2 재검증(형 GO) · wire금지

팩트체크:
| 항목 | JSON값 |
| FULL Δ | +0.171806 STRONG |
| collect rows/mean | 1134 / ≈1.998 |
| FULL재현 match | true |
| 지금단계 | 수집완료 · 교체·발권 아님 |

폐기한 틀린 기억: (있으면 나열)
질문 1개: (형에게)
```

---

## 6) 서명

```
author     : Cursor
doc_id     : GENSPARK-MEMORY-RESTORE-CURSOR
not_author : Genspark chat memory / compressed summary
repo       : kkr2652199-prog/ROK21
```
