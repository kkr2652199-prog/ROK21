# K-TRANSITION 방향성 브리핑 — **CURSOR 작성** (2026-08-05)

> **작성자: Cursor (ROK21 실행 에이전트 · `D:\ROK21` · commit/push 담당)**  
> **작성 시각(KST):** 2026-08-05 ~12:40  
> **목적:** 외부AI·타 커서 에이전트·형이 **혼동 없이** 동일 SSOT를 읽도록,  
> 깃허브 실측 + 신호 팩트 + 역할 차이 + **지금 할 일**을 한 파일에 고정한다.  
> **이 파일이 Cursor 브리핑 SSOT.** 채팅 요약만 믿지 말고 본 문서 + JSON을 읽는다.

---

## 0) 한 줄 결론 (Cursor 판정)

| 항목 | Cursor 결론 |
|------|-------------|
| 패턴 방향 | ✅ 전원 일치 — 「유사 회차(공통≥2) → 다음 회차 번호 빈도」 |
| 신호 존재 | ✅ `K-TRANSITION-FULL` sim_k2 Δ**+0.172** STRONG (미세 신호) |
| **지금 단계** | **패턴 수집·기록·분석** (발권·wire·뇌 교체 **아님**) |
| NEXT 문구 수정 | 「stat 교체 설계 착수」는 **성급** → **transition 패턴 수집 설계**로 정정 |
| K-ANALOG | 별트랙(UI/API 힌트) · 본선 아님 · 발권 미접촉은 유지 |

---

## 1) 깃허브 실측 (Cursor가 `git`으로 확인)

| 키 | 값 |
|----|-----|
| 레포 | `kkr2652199-prog/ROK21` · main · 포트 **7021** |
| HEAD(작성 직전) | `88ba6bd` (이후 push로 갱신) |
| WORK | IDLE |
| 관련 최근 커밋 | `03b7f3c` TRANSITION-FULL · `99e8a90` 논의기록 · R37 sync 연속 |

### 필독 증거 파일 (수치·판정)

| 용도 | 경로 | Cursor 비고 |
|------|------|-------------|
| rolling 벤치 | `docs/benchmarks/20260805_KTRANSITION_FULL.json` | **수치 SSOT** |
| 보고서 | `reports/20260805_KTRANSITION_FULL.md` | |
| 팩트체크 | `reports/20260805_KTRANSITION_FACTCHECK.md` | 1234→1235 hit=2 |
| 무작위표본 | `reports/20260805_KTRANSITION_RANDOM_SAMPLE.md` | 6/6 hit=2 |
| 로드맵(구) | `reports/20260805_KTRANSITION_DISCUSS_ROADMAP.md` | 본 브리핑으로 단계 정정 |
| **본 브리핑** | `reports/20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR.md` | **← Cursor 작성** |
| JSON 마커 | `docs/benchmarks/20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR.json` | author=Cursor |

### 타 에이전트 문서 (혼동 주의)

| 파일 | 작성 맥락 | Cursor 해석 |
|------|-----------|-------------|
| `My_Drive_Sync/SUMMARY/K_ANALOG_COLLAB.md` | 2026-07-28 · K-ANALOG | UI/API · coordinator 미접촉 · **뇌 교체 아님** |
| 외부AI 채팅 브리핑 | 젠스파크 등 | 방향 정리용 · **채팅 기억 불신** · JSON/본문서 우선 |

---

## 2) 신호 팩트 (과장 금지 · Cursor 재확인)

출처: `docs/benchmarks/20260805_KTRANSITION_FULL.json`

| 지표 | 값 |
|------|-----|
| range | draw 101~1235 · n_valid(sim_k2)=**1135** |
| mean_hit | **2.171806** |
| random baseline | **2.000** (top15 × 6/45) |
| delta | **+0.171806** |
| 판정(기준표) | **STRONG** (Δ≥+0.15) |
| sim_k3 | Δ**+0.065** MARGINAL · n=811 |
| sim_k4 | n_valid=**0** (support&lt;10) |
| wire | **false** |

### 단건 sanity (과장 방지)

| 출처 | 내용 |
|------|------|
| FACTCHECK | 1234 유사 212건 · top15→1235 hit=**2** (=baseline) · carry `[15,43]` |
| RANDOM_SAMPLE | 369·442·1024·1152·1216·1234 → **6/6 hit=2** |

**Cursor 해석:** STRONG은 “회차당 +0.17개” 수준의 **미세 신호 존재** 판정이다.  
단건 “대박”·즉시 발권 개선 클레임은 **금지**.

---

## 3) 역할·경로 비교 (Cursor 정리표)

| 항목 | Cursor(TRANSITION) | 타에이전트(K-ANALOG) | 외부AI 정리 | 형 의도(2026-08-05 확인) |
|------|--------------------|----------------------|-------------|---------------------------|
| 패턴식 | 유사≥2 → next-freq | 동일 계열 + pattern_sim | 동일 | 동일 |
| 측정 | rolling 전수 | PREP 단건+API설계 | 합류점 지적 | 전회차 학습·저장 |
| 지금 | (구)교체설계 문구 | UI 패치 Go | **수집 STEP1** | **수집·분석 우선** |
| 발권 | wire 금지 | 미접촉 | 나중 | 나중 |
| 뇌 | stat 교체 목표 | 미언급 | 패턴 후 | 패턴 충분 후 재설계 |

**일치:** 패턴 아이디어.  
**불일치(해소):** “지금 당장 할 일” — Cursor NEXT가 교체로 점프했음 → **본 문서로 수집 단계로 정정**.

---

## 4) 형 의도 — Cursor가 이해한 전체 흐름

```
[지금] 패턴 수집 · 분석 · 기록
  매 회차 당첨 확정
  → 과거 유사(공통≥2) 탐색
  → 유사 회차들의 다음 회차 번호 빈도
  → DB/로그에 학습 데이터로 저장
  → wire 없음 · 발권 없음 · 3뇌 미수정

[다음] 쌓인 데이터로 재검증
  → hit/mean_hit/Δ 재확인
  → 신호 유지 시에만 엔진 논의

[형 GO 후] 약한 뇌(stat)를 전이 패턴 엔진으로 재설계
  → markov/review 유지
  → 발권 pool 반영은 별도 GO

[패치 성공 후] 1236~ 매주 자동 학습·자동 반영
```

형 예시 요지(정답 아님·방향만):  
단일 회차 미래예측이 아니라, **비슷한 과거 여러 건**의 다음 번호 빈도를 모아  
낮은 확률이라도 셋트·뇌별로 참고할 패턴을 **매 회차 학습·저장**한다.  
확실해지기 전 전면 패치 금지.

---

## 5) Cursor 확정 순서 (실패 방지)

| STEP | 내용 | wire/뇌 | 상태 |
|------|------|---------|------|
| **1** | transition 패턴 수집 설계 (테이블/로그·회차별 필드·backfill READ) | 금지 | **← 지금** |
| 2 | 수집 데이터로 재검증 | 금지 | 대기 |
| 3 | stat → 전이 패턴 엔진 재설계 | 형 GO | 대기 |
| 4 | 발권 반영 + 주간 자동학습 | 형 GO | 대기 |

### 금지 (Cursor 재선언)

- `random.choices` · `engine.py` 직접 수정 · auto-tune · wire  
- DB INSERT/UPDATE **발권·predictions 경로**  
- 신호 과장 · 단건 hit로 STRONG 재해석  
- K-ANALOG UI와 본선 transition 수집 **혼동**  
- cold-free wire와 본선 **섞기**

---

## 6) 타 문서와의 관계 (읽기 순서)

외부AI / 타 에이전트가 복구할 때 **이 순서만**:

1. 본 파일 `20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR.md` (**Cursor**)  
2. `docs/benchmarks/20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR.json`  
3. `docs/benchmarks/20260805_KTRANSITION_FULL.json` (수치)  
4. `20260805_KTRANSITION_FACTCHECK.md` · `RANDOM_SAMPLE`  
5. `K_ANALOG_COLLAB.md` — **참고만** (UI 트랙)  
6. `NEXT_ACTIONS.md` LIVE 1건

채팅에 붙여넣은 외부AI 브리핑은 **보조**. 불일치 시 **본 Cursor 문서 + JSON** 우선.

---

## 7) NEXT 정정 (Cursor 제안 → SSOT 반영)

| 구분 | 구 문구 | 신 문구 (본 push) |
|------|---------|-------------------|
| ID | K-TRANSITION-FULL-DONE | **K-TRANSITION-COLLECT-DESIGN** (또는 DONE 유지 시 할일만 정정) |
| 할일 | stat 뇌 교체 설계 착수 | **transition 패턴 수집(DB/로그) 설계 · wire/뇌 미접촉** |
| 완료조건 | 형 GO | 형 GO |
| 메모 | 즉시착수 | STRONG=미세신호 · 수집 후 재검증 · 교체는 STEP3 |

---

## 8) 서명

```
author      : Cursor
role        : ROK21 executor (code · bench · commit · push)
repo        : kkr2652199-prog/ROK21
doc_id      : K-TRANSITION-DIRECTION-BRIEF-CURSOR
prior_json  : docs/benchmarks/20260805_KTRANSITION_FULL.json
not_author  : Genspark / other Cursor agents / chat-only summaries
```

_EOF Cursor briefing_
