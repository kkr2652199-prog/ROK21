# K-BRAIN-SIGNAL-A1 — pattern_signal + coordinator confidence blend

**일시:** 2026-08-01 KST  
**범위:** `app/testlotto/brains/shared/pattern_signal.py` (신규) · `coordinator.py` (삽입만)  
**형 GO:** K-BRAIN-SIGNAL-A1 착수

---

## 1) 구현 요약

### pattern_signal.py (신규)
| 함수 | 역할 |
|------|------|
| `_extract_features(draw)` | 9차원 패턴 벡터 — sum/270, odd/6, r1~r5/6, ac/10, max_consec/5 |
| `_cosine_similarity(a,b)` | 코사인 유사도 0.0~1.0 (self=1.0) |
| `get_pattern_signal(draws,k=10)` | query=draws[-1] · pool=draws[:-6] · top-k analog next-draw 가중 → {1~45} sum=1 |

**가드:** `len(draws)<15` · `max_sim<0.90` · valid analog 없음 → uniform 1/45  
**컨닝 방지:** search idx+1 next draw 사용 시 `idx+1 < len(draws)-1` (query 회차 제외)

### coordinator.py (최소 삽입)
- `_get_draws_before` 직후 `get_pattern_signal(draws)` 1회 계산
- 각 brain `predict_sets()` 반환 직후 confidence blend:
  - `conf_final = 0.85 * conf_brain + 0.15 * signal_score`
  - `signal_score = (avg_sig / uniform) * 10` — 세트 6수의 signal 평균, uniform 대비 스케일
  - signal max < `1/45 * 1.5` (≈0.0333) 이면 blend **skip** (near-uniform)

**미변경:** stat/markov/review `engine.py` · `random.choices` · `_get_draws_before` · BOOST_CAPS

---

## 2) confidence blend 설계 결정

| 항목 | 선택 | 근거 |
|------|------|------|
| w_brain 매핑 | 세트 scalar confidence 유지 | predict_sets는 per-number weight 미반환 |
| signal 매핑 | 6수 signal weight **산술평균** | 세트 단위 1 score로 축약 |
| 스케일 | `(avg_sig / (1/45)) * 10` | uniform→10pt · conf 60~90대와 0.15 가중 호환 |
| skip 조건 | max(signal) < 1/45×1.5 | spec near-uniform 가드 |
| blend 비율 | 85% brain / 15% signal | spec 고정 · aux 1:1(40pt)과 별 레이어 |

---

## 3) 검증 체크리스트

| # | 항목 | 결과 |
|---|------|------|
| 1 | import `pattern_signal` | **PASS** |
| 2 | `_extract_features` len=9 | **PASS** |
| 3 | `_cosine_similarity(x,x)=1.0` | **PASS** |
| 4 | draws<15 → uniform | **PASS** |
| 5 | sum-normalized 1.0 | **PASS** |
| 6 | idx+1 conning guard (code path) | **PASS** |
| 7 | engine `generate` signatures unchanged | **PASS** (grep) |
| 8 | `random.choices` / BOOST_CAPS engine 미변경 | **PASS** (grep) |
| 9 | smoke draw 1225~1234 ×10 | **PASS** (no errors · ~20s) |

---

## 4) smoke 상세

```
tools/_kbrain_signal_a1_smoke.py
draw 1225~1234: OK status=예측 완료 (3+4뇌 체계)
SMOKE PASS 1225-1234
```

---

## 5) 다음

- **K-BRAIN-SIGNAL-BACKTEST-100** — 형 GO 대기 (본 턴 **착수 안 함**)
- BACKTEST 전 commit/push는 형 지시 시

---

## 6) 변경 파일

| 파일 | 변경 |
|------|------|
| `app/testlotto/brains/shared/pattern_signal.py` | **신규** |
| `app/testlotto/brains/coordinator.py` | signal compute + confidence blend 삽입 |
| `tools/_kbrain_signal_a1_smoke.py` | 검증용 (optional) |

**HEAD(작업 시점):** `2e3065e`
