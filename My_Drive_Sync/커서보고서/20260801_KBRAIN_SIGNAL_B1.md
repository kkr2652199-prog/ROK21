# K-BRAIN-SIGNAL-B1 — signal weights 직접 블렌딩 (virtual draws)

**일시:** 2026-08-01 KST  
**범위:** `pattern_signal.py` (`make_signal_draws` 추가) · `coordinator.py` (A1 confidence blend → B1 virtual draws)  
**형 GO:** 방향 2 — signal을 weights 생성 단계에 반영

---

## 1) 배경

K-BRAIN-SIGNAL-BACKTEST-100 (방향1 confidence blend): ge3=**0.0600** = K-HIGHWAY 동일 → 번호 **선택**에 signal 미반영.

**B1 변경:** signal top6을 **가상 draws 3회차**로 변환 → `draws_with_signal = virtual + draws` → engine 빈도/가중치 파이프라인에 자연 주입.

---

## 2) 구현 변경

### pattern_signal.py — `make_signal_draws()` 추가
- signal max < uniform×1.5 → `[]`
- top6 번호 · `draw_no = base - 1000 - i` · n_virtual=3
- 기존 `get_pattern_signal` / `_extract_features` **불변**

### coordinator.py
- **제거:** `_blend_pattern_confidence` 및 confidence 0.85/0.15 blend
- **추가:** `make_signal_draws` → `draws_with_signal`
- `predict_sets(draws_with_signal, ...)` (dedup regen 동일)
- aux scoring은 **실제 draws** 유지 (컨닝 방지)

**미변경:** stat/markov/review `engine.py` · `random.choices` · `_get_draws_before` · `BOOST_CAPS`

---

## 3) 검증 체크리스트

| # | 항목 | 결과 |
|---|------|------|
| 1 | uniform signal → `[]` | **PASS** |
| 2 | top6 6개 · draw_no > 0 | **PASS** (base=1234 → 234,233,232) |
| 3 | `virtual_draws + draws` 순서 | **PASS** |
| 4 | `_blend_pattern_confidence` 완전 제거 | **PASS** (grep 0건) |
| 5 | 동결 토큰 미수정 | **PASS** (engine.py 미변경) |
| 6 | smoke 1225~1234 ×10 | **PASS** · virtual_active **10/10** |

---

## 4) smoke test

```
draw 1225~1234: OK virtual=3 each
virtual_draws_active=10/10 (100%)
```

도구: `tools/_kbrain_signal_b1_smoke.py`

---

## 5) NEXT

- **K-BRAIN-SIGNAL-B1-BACKTEST-100** — walk-forward n=100 · **형 GO 대기**
- B1-BACKTEST 자동 착수 **금지**
