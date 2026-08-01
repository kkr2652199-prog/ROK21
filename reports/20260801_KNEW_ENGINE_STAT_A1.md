# K-NEW-ENGINE-STAT-A1 — stat_brain engine v2 (dual-window + cycle gap)

**일시:** 2026-08-01 KST  
**범위:** `app/testlotto/brains/stat_brain/engine.py` — `build_weights` only  
**형 GO:** 진행해줘

---

## 1) 설계 요약

### 제거 (v1 → v2)
| 항목 | v1 | v2 |
|------|----|----|
| 전체 윈도우 빈도 | `exp(-0.02 * age)` 단일 루프 | **제거** → dual window |
| gap 부스트 | gap≥50 ×1.3 / gap≥30 ×1.15 | **제거** → cycle 기반 |

### 추가 — Layer 1 (dual window frequency)
- **long_freq:** 전체 `draws`, decay `exp(-0.005 * age)` → sum=1 정규화
- **short_freq:** `draws[-52:]`, decay `exp(-0.05 * age)` → sum=1 정규화  
  (`len(draws) < 52` 이면 전체 draws 사용 + debug log)
- **blend:** `freq[n] = 0.4 * long_norm[n] + 0.6 * short_norm[n]`

### 추가 — cycle gap boost (gap_map 대체)
- `db_facts.get_gap_map(draws)` + 번호별 평균 출현 주기(appearance 간 draw_no gap 평균, rare→default 10)
- `gap >= avg_cycle * 1.5` → ×1.25
- `gap >= avg_cycle * 1.2` → ×1.15
- Layer 2 `learn.apply_learn_boost` overdue (gap≥30) **유지**

### 유지 unchanged
- hot_count recent 5 (×1.2 if cnt≥2)
- pair_freq top30 bonus
- feedback trap/hit
- `learn.apply_learn_boost` at end
- `generate()` — **random.choices·tier1_filter 미변경** (동결 준수)

### 플래그
- `ENGINE_V2 = False` (모듈 기본값 — production 안전)
- env `K_STAT_ENGINE_V2=1` 또는 bench monkeypatch로 v2 활성화

---

## 2) Before / After (build_weights)

| 단계 | v1 (baseline) | v2 (A1) |
|------|---------------|---------|
| 빈도 | 단일 exp(-0.02) | 0.4 long + 0.6 short |
| gap | 30/50 고정 임계 | avg_cycle × 1.2 / 1.5 |
| hot/pair/feedback/learn | 동일 | 동일 |

---

## 3) 벤치 (stat solo)

**도구:** `tools/_k_new_engine_stat_a1_bench.py`  
**JSON:** `docs/benchmarks/20260801_KNEW_ENGINE_STAT_A1.json`  
**조건:** seed=42 · n=200 · draw 1035~1234 · `stat_brain.predict.run(draws, n_sets=5)` · READ-ONLY

| variant | ge3_count | ge3_rate | mean_match | p vs null |
|---------|-----------|----------|------------|-----------|
| **baseline** (ENGINE_V2=False) | 27 | **0.1350** | 1.8050 | 0.198612 |
| **v2** (K_STAT_ENGINE_V2=1) | 27 | **0.1350** | 1.7750 | 0.198612 |
| **delta** | 0 | **0.0000** | −0.0300 | — |

**Gate:** `v2 ge3 >= baseline_solo OR (delta >= +0.01 AND p < 0.15)`

| 조건 | 결과 |
|------|------|
| gate_a: v2 ge3 ≥ baseline (0.1350) | **PASS** (동률) |
| gate_b: delta ≥ +0.01 AND p < 0.15 | FAIL (delta=0, p=0.199) |
| baseline_solo ref | 0.1125 (참고) — v2 0.1350 ≥ ref |

**판정: PASS** — v2가 baseline solo 대비 **퇴화 없음** (동일 ge3). uplift 없음 → `ENGINE_V2` 기본 False 유지.

---

## 4) 검증

- [x] `python -c "from app.testlotto.brains.stat_brain import predict"` — OK
- [x] bench 실행 — PASS
- [x] `generate()` 내 `random.choices(pool, weights=w, k=1)[0]` — **내용 미변경** (파일 라인 203, helper 추가로 오프셋만 이동)

---

## 5) 다음

- **K-NEW-ENGINE-MARKOV-A1** — markov_brain engine 개선 (형 GO 대기)
- STAT v2 uplift 없음 → production `ENGINE_V2=False` 유지 권고
