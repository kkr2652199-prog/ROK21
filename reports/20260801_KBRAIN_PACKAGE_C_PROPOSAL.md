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

1. **K-BRAIN-PACKAGE-B** — stat만 이동 · ge3 동치 n=200
2. **K-BRAIN-PACKAGE-C** — 3뇌 + aux 1:1 · FULL ge3 비교
3. coordinator 축소 · `signal_pool` 뇌별 hook (선택)

---

## 9. 외부 AI·커서 합의

> **C가 형 최종 그림과 일치.** B는 마일스톤.  
> 「안 된다」 아님 · **HOLD + 동치 검증 + 단계 GO.**

---

## 10. 관련 문서

- `reports/20260801_ROK21_SESSION_ARCHITECTURE_NOTES.md`
- `reports/20260801_K_ARCHITECTURE_REVIEW.md`
- `My_Drive_Sync/SUMMARY/WARRANT.md` · `FINDINGS.md`
