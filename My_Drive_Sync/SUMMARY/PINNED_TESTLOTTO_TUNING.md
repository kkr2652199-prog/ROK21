# PINNED_TESTLOTTO_TUNING — 테스트로또 본선 튜닝 핀 (20260728)

📌 **범위:** 테스트로또만 · 다른 탭 뇌 참조 금지 · 탭 삭제 보류  
📌 **SSOT:** `kkr2652199-prog/ROK21` · `D:\ROK21` · 포트 7021  
📌 **동결:** `random.choices` · `_get_draws_before` · boost 상한 (형 승인 전 수정 금지)  
📌 **평가:** `BENCH_PROTOCOL.md` · 명분 `WARRANT.md` · 수치 `docs/benchmarks/*.json`

> 이 문서 = **튜닝 순서 핀**. 인프라·UI 간소화·탭 삭제는 **신뢰 확보 후** 별도 GO.

---

## 0) 외부 벤치마킹 (인터넷 · 20260728)

| 출처 | 핵심 | ROK21 적용 |
|------|------|------------|
| [datarekha walk-forward](https://datarekha.com/time-series/evaluating-forecasts/) | 시간순 rolling · naive baseline 병기 | `review_single_draw` = expanding WF ✓ |
| [QuantInsti WFO](https://blog.quantinsti.com/walk-forward-optimization-introduction/) | IS/OOS 분리 · regime lag | K-REVIEW-RUN 후 WFE(성능 유지율) 측정 |
| [JackpotMath lottery-lab](https://jackpotmath.com/tools/lottery-lab) | 11방법 전부 → **baseline 수준** | mean≈0.8 **null-check**만 · 적중↑ 목표 폐기 |
| [statlotto NN](https://statlotto.com/posts/ai-lottery-prediction) | NN도 **random rate 수렴** | “AI 예측” 마케팅 거부 · **정직 UI** 유지 |
| [LinkedIn AI lottery tools](https://www.linkedin.com/pulse/from-random-picks-smart-analysis-rise-ai-powered-lottery-ahmed-foysal-st2vc) | AI = 분포·균형 **분석 보조** · 당첨 보장 아님 | analog·814만순위 = **보조 좌표** (뇌 아님) |

**외부 합의:** 공정 로또에서 **예측 우위 기대는 0**. ROK21 목표 = **(1) 컨닝 없는 WF 재현 (2) 명분 있는 제약 (3) random 대비 lie detection**.

---

## 1) AI 협업 논의 요약 (20260728)

### 🅰 벤치 아키텍트 (외부 표준)

> WF 전 구간 재실행 없이 튜닝 수치는 **무효**.  
> **Pin #1 = K-REVIEW-RUN** (learn_state reset → 2~1234).  
> 각 단계마다 **before/after JSON** + random mean 병기.

### 🅱 통계 감사 (JackpotMath·K-O/K-P)

> mean 0.8 상수 → **뇌 서열화 불가**.  
> 튜닝 성공 기준을 “stat > markov”로 두지 말 것.  
> 성공 = **(a) 재현 가능 (b) 컨닝 0 (c) 명분 라벨 유지 (d) random과 구분 불가면 정직히 기각**.

### 🅲 ROK21 동생 (본선 정렬)

> NEXT=K-AWAIT 유지. **1235 전에 K-REVIEW-RUN 필수**.  
> 4군·효도·전략X 뇌 출력을 testlotto에 **fusion 금지**.  
> analog·combo_rank_814만 **관측 레이어**.

### 🅳 엔지니어 (커서 · 실행)

> 순서: **REVIEW-RUN → 벤치 → (ending/markov 검증) → 1235 execute**.  
> 각 Pin마다 `tools/_k*.py` verify + `docs/benchmarks/` JSON.  
> 파일럿 1132~1234 먼저 → 전구간은 형 GO.

### 🅴 형 (결정 권)

> GO 지점: Pin 시작·DB 쓰기·동결 해제(K-E seed).  
> **탭 삭제·간소화 = 보류** (형 20260728 지시).

### 🤝 협업 합의 (4:1 찬성 · 1 보류)

| 항목 | A | B | C | D | E(형) |
|------|---|---|---|---|-------|
| K-REVIEW-RUN 선행 | ✓ | ✓ | ✓ | ✓ | **PASS 20260728** |
| mean으로 뇌 순위 | ✗ | ✗ | ✗ | ✗ | ✗ |
| 1235 without review | ✗ | ✗ | ✗ | ✗ | ✗ |
| 다른 뇌 탭 fusion | ✗ | ✗ | ✓ | ✗ | ✗ |

---

## 2) Pin 스택 (중요도 ↓ · 순차 진행)

### 🔴 PIN-0 — 데이터 정체성 (선행 · 블로커) ✅ PASS 2026-07-28

| ID | 할 일 | 근거 | 게이트 |
|----|--------|------|--------|
| **K-REVIEW-RUN** | `learn_state` reset → `run_review_loop(2,1234)` | brain_review 99.8% kweon 복사 | ✅ `20260728_KREVIEW_full_2_1234.json` verify_pass |
| **K-REVIEW-VERIFY** | stat/markov/review `[보조4뇌:` in review rows | K-PIPE-A 미반영 저장분 | ✅ 3698/3698 · sample 100/500/1234 |

**형 GO 필요:** DB 쓰기 · 백업 `backups/YYYYMMDD_재복습전/`

---

### 🟠 PIN-1 — 평가·신뢰 (REVIEW-RUN 직후)

| ID | 할 일 | 근거 | 게이트 |
|----|--------|------|--------|
| **K-TRUST-BENCH** | random mean·3뇌 mean·≥3% · WFE 창별 | BENCH_PROTOCOL · 외부 baseline | `docs/benchmarks/YYYYMMDD_KTRUST_bench.json` |
| **K-TRUST-UI** | “ROK21 재복습 데이터” vs legacy 라벨 | K-REBRAND 후 정체성 | UI 문구 · brain_review created_at 분포 |

**성공 정의 (비보수):** random 대비 우위 **기대하지 않음**. lie(컨닝·kweon 잔재) **0**이면 PASS.

---

### 🟡 PIN-2 — 3예측뇌 튜닝 (명분·구현 검증)

| ID | 대상 | OPEN | 조치 | 동결 |
|----|------|------|------|------|
| **K-TUNE-F** | markov learn_state 미소비 | K-F | `predict_flow_shaman` boost 배선 검증 | — |
| **K-TUNE-X** | review ending | K-X PATCHED | RE-RUN 후 l1·χ²/df 재측정 | random.choices |
| **K-TUNE-G** | ending_digit_boost=0 | K-G | miss SSOT review 기준 재활성 **가능성** | boost 상한 |
| **K-TUNE-A** | stat mean 0.760 | K-A | **패치 아님** · null-check · 명분만 | — |

**순서:** F → X(verify) → G(형 GO) · stat/markov **서열 경쟁 금지**

---

### 🟢 PIN-3 — 4보조·파이프 (이미 PATCHED · 재검증)

| ID | 상태 | RE-RUN 후 확인 |
|----|------|----------------|
| K-PIPE-A | PATCHED | review reasoning `[보조4뇌:` |
| K-AG / K-AA | PATCHED | pattern/balance learn키·pair÷32 |
| K-V dedup | PATCHED | E[k]=100 유지 |
| K-D fusion | 문서화 | coordinator 단일 경로 |

---

### 🔵 PIN-4 — 실전 (1235)

| ID | 트리거 | 명령 |
|----|--------|------|
| **K-AWAIT** | 1235 API 공개 | `python tools/_kawait_1235_loop.py --execute` |

**선행:** PIN-0 PASS · 3DB MAX=1235 · drift0

---

### ⚪ PIN-5 — 보류 (튜닝·신뢰 후)

| ID | 내용 | 사유 |
|----|------|------|
| K-E seed | 재현성 | **동결** · 형 승인 |
| K-N | learn_input best→mean | HOLD · 설계 후 |
| K-J/M/C | referee 가중 | HOLD · K-M |
| UI-SLIM | 탭 삭제 | 형 20260728 보류 |
| 814만 UI 흡수 | combo_rank inline | PIN-1 후 |

---

## 3) 실행 로드맵 (순차 · 추천)

```
[형 GO] PIN-0 파일럿 1132~1234 (1~2h)
    ↓ verify PASS
[형 GO] PIN-0 전구간 2~1234
    ↓
PIN-1 K-TRUST-BENCH (READ-ONLY 집계)
    ↓
PIN-2 K-TUNE-F → K-TUNE-X verify → (GO) K-TUNE-G
    ↓
1235 발표 → PIN-4 K-AWAIT execute
    ↓
PIN-5 (선택) UI·814만·탭
```

---

## 4) 금지 (全 Pin 공통)

- 4군·효도·전략X **뇌 출력** → testlotto 입력
- mean 단독 **뇌 서열·승자 선언**
- kweon 복사 brain_review를 **「튜닝 완료」** 로 표기
- 동결 토큰 **형 승인 없이** 수정
- 탭 삭제 (형 보류 중)

---

## 5) 다음 1건 (형 GO 대기)

**ID:** `K-REVIEW-RUN-PILOT`  
**할일:** 백업 → learn reset → `run_review_loop(1132, 1234)` → before/after 벤치  
**승인:** 형 「PIN-0 GO」 1줄

---

_갱신: 20260728 · HEAD=`7ee3fa9` · 협업 논의 반영_
