# K-EVOLVE-DIAG-3BRAIN-EXPAND

시각: 2026-08-15T14:50:08+09:00 · **EXPAND_OK** · 3뇌 독립 write · 1237아님 · hits/tier 클레임 금지
목적=캐시 채점 append를 markov/review로 확장. 예측로직 미변경. EVOLVE_AUTO/FEATURE_LAMBDA OFF.

HARD=통과. write ok=600 skip=0 fail=0. pred_reset=0 pred_after=3000.

## 1) census

| 항목 | 전 | 후 |
|------|----|----|
| evolve 행 | 200 | 600 |
| evolve 뇌 | {'stat': 200} | {'markov': 200, 'review': 200, 'stat': 200} |
| 원장 | {'stat': 3000} | {'stat': 3000} |
| 캐시 | {'markov': 200, 'review': 200, 'stat': 200} | {'markov': 200, 'review': 200, 'stat': 200} |
| predictions | 0 | 3000 |
| pred 뇌 | {} | {'markov': 1000, 'review': 1000, 'stat': 1000} |
| pred_1237 | 0 | 0 |
| draws MAX | 1236 | 1236 |
| learn/skill_hw/role_hw | 0/600/1200 | 0/600/1200 |

## 2) HARD

| 항 | 값 |
|----|-----|
| peek as_of>=draw | 0 |
| evolve 뇌별 | {'markov': 200, 'review': 200, 'stat': 200} |
| 합산뷰 | 없음 |
| 원장 불변 | True |
| learn/숙제 불변 | True |
| stat 캐시 fp 불변 | True |
| markov/review 캐시 채움 | True |
| drift | 0 |
| cross_source | 0 |
| pred_1237 | 0 |
| draws MAX | 1236 |
| EVOLVE_AUTO | False |
| FEATURE_LAMBDA | False |
| review learn_boost | False |

## 3) prefer/prize (캐시 불변 증명 · 모니터)

| 뇌 | prefer전 | prefer후 | Δprefer | prize전 | prize후 | Δprize |
|----|----------|----------|---------|---------|---------|--------|
| stat | 1.009444 | 1.009444 | 0.0 | 1.004395 | 1.004395 | 0.0 |
| markov | None | 1.045325 | None | None | 1.016871 | None |
| review | None | 1.018102 | None | None | 1.037964 | None |

stat 캐시는 다시 뽑지 않음(fp 불변 · Δ=0). markov/review는 빈 `[]` 행만 해당뇌 `expand_pool(brains=[tag])`로 채움(타뇌·원장·숙제 미접촉). 채운 뒤 캐시→로그/발권 복사. 우열 클레임 금지.

## 4) 독립

- evolve nums == 해당뇌 캐시: ok={'stat': 200, 'markov': 200, 'review': 200} drift={'stat': 0, 'markov': 0, 'review': 0}
- 타뇌 캐시 소스로 기록: 0
- review apply_learn_boost 함수: **없음**(carry만). 기록 features.has_apply_learn_boost=false.

## 5) 롤백

`write_evolve_diag_confirmed` 호출 제거 + `DELETE FROM testlotto_evolve_log WHERE brain_tag IN ('markov','review')` + `backups/20260815_EXPAND전_DB전체` 복원. 원장 불변.
