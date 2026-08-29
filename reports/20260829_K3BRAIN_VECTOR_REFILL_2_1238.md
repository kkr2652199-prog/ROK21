# K-3BRAIN-VECTOR-REFILL-2-1238

시각: 2026-08-29T14:58:24+09:00 · **REFILL_OK** · 예측기록 초기화 후 2–1238 3뇌 재백필 · hits 클레임 금지
목적=브라우저에서 회차별 벡터 확인. 1회는 이전회 없음 스킵. 1239 예측 없음.
원장·숙제·learn·lotto_draws 보존. DB git 안 함.

HARD=통과. peek=0 · pred_1237=15 · pred_1238=15 · pred_1239=0 · MAX=1238.

## 1) 리셋

| 표 | 삭제 |
|----|------|
| pool_view_cache 전체 | 3707 |
| lotto_predictions 전체 | 18520 |
| evolve_log 전체 | 3704 |

보존: lotto_draws · pool_hit_ledger · skill_homework · role_homework · learn_state.

## 2) 백필 2–1238

| 뇌 | expand ok | fail | cache nonempty | evolve | pred |
|----|-----------|------|----------------|--------|------|
| stat | 1237 | 0 | 1237 | 1237 | 6185 |
| markov | 1236 | 1 | 1236 | 1236 | 6180 |
| review | 1237 | 0 | 1237 | 1237 | 6185 |

예측 구간 min=2 max=1238. 브라우저=테스트로또 회차전환.

## 3) census

| 항 | 전 | 후 |
|----|----|----|
| 원장 | {'stat': 3000} | {'stat': 3000} |
| learn/skill/role | 0/600/1200 | 0/600/1200 |

## 4) 판정

성적 아님. 롤백=`backups/20260829_VECTOR전_1_1238/`.

## 5) 브라우저·API

포트 **7021**. 회차전환 후 3뇌 pool 표시. 새로고침 필요(탭 메모리캐시가 리필 전 값을 잡을 수 있음).

| 회차 | pred | pool-view | UI |
|------|------|-----------|-----|
| 2 | review5+stat5 (markov없음) | 3행미달 miss | 해당없음 |
| 100 | 15 | 3뇌 각10 cached | — |
| 1236 | 15 | cached · computed_at 2026-08-29 14:58:15 | 과거학습#1=`7 8 17 28 31 39` 일치 |
| 1238 | 15 | cached · computed_at 2026-08-29 14:58:21 | 과거학습#1=`3 12 23 28 32 41` 일치 |

1239=0. 적중 클레임 금지.

## 6) 금지 확인

1239 없음. kweon 미접촉. 동결토큰 미수정. DB git 안 함.

