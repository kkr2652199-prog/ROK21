# K-BRAIN-PACKAGE — 3뇌 구조 A/B/C 비교 및 C안(뇌+전용보조) 설계

날짜 2026-08-01 · **코드 변경 없음** · HOLD 중 설계 문서  
HEAD `de0f1f4` · NEXT **K-ATTACK-HOLD**

---

## 1. 질문 요약

형이 제안한 3단계:

| 단계 | 구조 |
|------|------|
| **A** | (형 인식) 1·2·3뇌 각각 + 보조4 + 공용 |
| **B** | 1·2·3뇌 **독립 파일** + 보조4 **전역 공용** |
| **C** | 1·2·3뇌 **완전 독립** + **뇌당 맞는 보조 1개** 같은 파일/패키지 + referee 공용 |

**추가:** 「뇌기능 삭제」= 역할 제거가 아니라 **흩어진 코드 이전·중복 제거**.

---

## 2. A(현재) — 코드 실态

형 그림과 **차이:**

```
[stat/markov/review predict_sets] → 15장
         ↓
[coordinator: 4보조 × 0.25 균등 · 15장 전부]  ← 뇌별 전용 아님
         ↓
[wire quota 5]
```

- `brains/predict_*.py` = **얇은 어댑터** (30~97줄)
- 엔진 = `predict_statistical.py` · `predict_markov.py` (**루트 분산**)
- 4보조 = **전역 1벌** · `coordinator._aux_composite_score`
- repack = `signal_pool.py` · **live와 별 트랙**

---

## 3. A / B / C 비교

| | **A 현재** | **B 중간** | **C 최종** |
|--|-----------|-----------|-----------|
| 예측 | 껍데기+엔진 분산 | 뇌3 파일 독립 | 뇌3 **패키지** 독립 |
| 보조 | 4개 전역 균등 | 4개 전역 | **1:1 + referee** |
| coordinator | 무거움 | 얇아짐 | **호출·wire만** |
| repack | signal_pool 분리 | 동일 | **뇌 패키지 내** 가능 |

**권장 경로:** A → **B(동치)** → **C(보조1:1)** · 또는 형 GO 시 B+C 한 번에(동치 부담↑).

---

## 4. C안 — 뇌↔보조 매핑 (WARRANT·K-Y)

| 예측뇌 | 전용 보조 | 근거 |
|--------|-----------|------|
| **stat** | **balance** | 빈도·분포·홀짝·구간 |
| **markov** | **pattern** | pair·연속·AC·전이 |
| **review** | **miss** | trap·오답·복습 |
| **(공용)** | **referee** | brain_w · K-M · 메타 |

referee는 **3뇌 파일에 넣지 않음** — coordinator/shared.

---

## 5. C안 — 폴더 트리 (목표)

```
app/testlotto/brains/
  stat_brain/
    engine.py      ← predict_statistical 흡수
    learn.py
    aux_balance.py
    predict.py     ← generate + post_score
  markov_brain/
    engine.py      ← predict_markov 흡수
    aux_pattern.py
    predict.py
  review_brain/
    engine.py
    aux_miss.py
    predict.py
  shared/
    diversity.py
    referee.py
  coordinator.py   ← run + wire (~80줄 목표)
```

**뇌 API (개념):**

```python
def run(draws, n_sets=5) -> list[dict]:
    raw = engine.generate(...)
    raw = diversity.pick(raw, n_sets)
    return [post_score(s) for s in raw]  # 전용 aux + referee
```

---

## 6. 「삭제」 vs 「이전」

| | 처리 |
|--|------|
| stat/markov/review **역할** | **유지** (FINDINGS·기각 정책) |
| coordinator 4×0.25 전역 aux | **C에서 제거** → 뇌별 post_score |
| `predict_statistical.py` 등 | **이동 후** deprecated |
| `random.choices` 라인 | **동결** · 이동만 |

---

## 7. 기대 효과 / 비기대

| 확실 | ge3↑ 자동 ❌ · 동치 벤치 필수 |
|------|------------------------------|
| 뇌별 1파일 읽기·튜닝 | K-MARKOV-LEARN류 재실패 가능 |
| aux→생성 hint 자리 | HOLD 중 wire·coordinator 패치 금지 |
| repack 통합 용이 | EV 축 별도 |

---

## 8. GO 조건 (형 승인 후)

1. **K-BRAIN-PACKAGE-B** — stat만 이동 · **동치 벤치 n=200 필수** (ge3·mean·세트 nums 일치)
2. **K-BRAIN-PACKAGE-C** — 3뇌 + aux 1:1 · FULL ge3 비교
3. coordinator 축소 · `signal_pool` 뇌별 hook (선택)

---

## 11. C안 설계 근거 — 코드 직접 확인 (2026-08-01)

> READ-ONLY grep·파일 실측 · 패치 없음

| # | 주장 | 판정 | 코드 근거 |
|---|------|------|-----------|
| **1** | markov 껍데기 36줄 · 엔진=`predict_markov.py` · learn_state 미소비 · pair_freq는 reasoning만 | **✅ 확인** | `predict_flow_shaman.py` L18 `_markov_predict`만 호출 · L23-25 `hot_pairs`→`reasoning` 문자열 · `load_learn_state` **0건**. 엔진은 `get_feedback_summary` trap×0.8/hit×1.15 (`predict_markov.py` L120-134) — **learn_state와 별 경로** |
| **2** | stat 껍데기 ~52줄 · learn 읽지만 confidence만 | **⚠️ 부분** | **껍데기** `predict_stat_fairy.py` L28-43: `load_learn_state` → reasoning·**carry 시 confidence** (+8×). **생성 가중**은 **엔진** `predict_statistical.py` L179-223에서 `weights[n]`에 ending/carry/overdue **반영 후** `random.choices`. C안 B단계 시 **두 파일을 stat_brain/engine.py 한 덩어리로 합침** |
| **3** | review 97줄 직접 생성 · carry_boost 반영 · neutralize가 boost 희석 | **✅ 확인** | L27-30 `prev_nums ×1.8×carry_boost` · L34 `neutralize_ending_digit_mass` **random.choices 직전** (K-P3). ending_digit_boost는 **미참조** · DB cap 0.3이어도 review 경로 **무효** |
| **4** | aux는 생성 후 채점 · set_no_asc 발권 → aux가 발권에 **미반영** | **✅ 확인** | `coordinator.py` L180-181 aux→confidence sort · L207 `apply_markov_wire_quota` → **set_no/pred_set_no 오름차순** (L46-66). confidence 정렬 **발권에 미사용** (remainder만 conf fallback) |
| **5** | review↔miss **신호 역방향** (이월선호 vs trap penalty) | **✅ 설계 긴장** | review: `prev_nums ×1.8` (`predict_review_king.py` L29-30). miss: `frequent_traps` 포함 시 감점 (`aux_miss_detective.py` L29-31). **생성 vs 사후채점** 분리라 직접 상쇄는 아니나 C안 1:1 페어링 시 **hint 통합 설계 필요** |
| **6** | `neutralize_ending_digit_mass` 위치 — review에 있으나 **balance 역할** | **✅ 확인** | K-P3 주석 L37-40 · `WARRANT.md` review 끝수 편향경보. **balance_aux**는 사후 `score_set`만 · **생성 전 끝수 균등**은 review 전용 → C안에서 **stat/review 경계 재배치** 후보 |

### C안 B단계(stat 이동) — 동치 게이트 (형 확정)

```
ID: K-BRAIN-PACKAGE-B
선행: 형 GO · K-ATTACK-HOLD survey 예외
PASS: 이동 전후 n=200 · draw 1035~1234 · stat 세트 nums·ge3·mean 동일(허용오차 0)
금지: random.choices 라인 변경 · _get_draws_before · boost cap · wire quota
FAIL: 즉시 revert · NEXT=K-ATTACK-HOLD
```

### C안에서 1~6번이 풀리는 방향 (설계만)

| 이슈 | C안 대응 |
|------|----------|
| 1 markov pair reasoning-only | `engine`에서 pair_freq→visit_count 또는 hint |
| 2 stat learn 분산 | engine+learn 한 패키지 |
| 3 review neutralize vs carry | `aux_balance`와 역할 분리·ending boost 경로 정리 |
| 4 aux 무효 발권 | **뇌별 post_score 후 set_no** 또는 conf top-k wire 대안 survey |
| 5 review↔miss | miss hint를 **생성 전** review engine에 (trap down-weight) |
| 6 ending neutralize | review→balance 이동 또는 shared `ending_policy.py` |

---

## 9. 외부 AI·커서 합의

> **C가 형 최종 그림과 일치.** B는 마일스톤.  
> 「안 된다」 아님 · **HOLD + 동치 검증 + 단계 GO.**

---

## 10. 관련 문서

- `reports/20260801_ROK21_SESSION_ARCHITECTURE_NOTES.md`
- `reports/20260801_K_ARCHITECTURE_REVIEW.md`
- `My_Drive_Sync/SUMMARY/WARRANT.md` · `FINDINGS.md`
