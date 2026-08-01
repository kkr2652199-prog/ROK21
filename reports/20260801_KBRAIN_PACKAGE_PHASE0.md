# K-BRAIN-PACKAGE-PHASE0 — 뇌 패키지 스켈레톤 생성

날짜 2026-08-01 · 형 GO · HEAD `3ca16e2` (커밋 전)

---

## 1. 실행 요약

| 항목 | 내용 |
|------|------|
| ID | **K-BRAIN-PACKAGE-PHASE0** |
| 목적 | `app/testlotto/brains/` 하위 3뇌+shared 패키지 스켈레톤 생성 (docstring + pass/stub) |
| 기존 파일 | **변경 없음** — predict_*.py · coordinator · predict_statistical/markov 미수정 |
| 벤치 | Phase0 — **ge3 벤치 불필요** (코드 경로 미연결) |
| 다음 | **K-BRAIN-PACKAGE-PHASE1** — stat_brain 구현 · 동치 n=200 |

---

## 2. 생성 파일 (19건)

### stat_brain/ (5)
- `__init__.py` — 패키지 docstring
- `engine.py` — predict_statistical 흡수 예정
- `learn.py` — learn_state('stat') 연결 예정
- `aux.py` — balance 전용 보조 예정
- `predict.py` — `run()` NotImplementedError stub

### markov_brain/ (5)
- `__init__.py`
- `engine.py` — predict_markov 흡수 예정
- `learn.py`
- `aux.py` — pattern 전용 보조 예정
- `predict.py` — `run()` NotImplementedError stub

### review_brain/ (5)
- `__init__.py`
- `engine.py` — predict_review_king 흡수 예정
- `learn.py`
- `aux.py` — miss 전용 보조 예정
- `predict.py` — `run()` NotImplementedError stub

### shared/ (4)
- `__init__.py`
- `diversity.py` — set_diversity 래핑 예정
- `referee.py` — aux_referee 공용 예정
- `db_facts.py` — get_number_freq · get_pair_freq · get_gap_map · get_carry_candidates (NotImplementedError + 한국어 docstring)

---

## 3. git diff 검증

```
git diff --name-only  → data/lotto_testlotto.db (기존 수정 · 본 작업 미포함)
git status --short    → ?? app/testlotto/brains/{stat,markov,review}_brain/ · shared/
```

- **기존 predict_*.py · coordinator.py · predict_statistical.py · predict_markov.py:** diff **0건**
- **random.choices · _get_draws_before · boost cap:** 미접촉
- **DB 쓰기:** 없음

---

## 4. 금지 항목 준수

| 금지 | 상태 |
|------|------|
| 기존 predict_*.py 수정/삭제 | ✅ 미변경 |
| predict_statistical/markov 수정 | ✅ 미변경 |
| coordinator 수정 | ✅ 미변경 |
| random.choices | ✅ 미사용 |
| _get_draws_before | ✅ 미사용 |
| boost cap 변경 | ✅ 미접촉 |
| 코드 migration | ✅ Phase0 스켈레톤만 |

---

## 5. 다음 단계

**K-BRAIN-PACKAGE-PHASE1**
- stat_brain/engine·learn·aux·predict 구현
- predict_statistical + predict_stat_fairy → stat_brain 이전
- **동치 벤치 n=200** (draw 1035~1234 · ge3·mean·nums 일치 허용오차 0)
- FAIL 시 revert · NEXT=K-ATTACK-HOLD

---

## 6. 관련 문서

- `reports/20260801_KBRAIN_PACKAGE_C_PROPOSAL.md`
- `My_Drive_Sync/SUMMARY/WARRANT.md`
