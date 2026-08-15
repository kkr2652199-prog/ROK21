# K-3BRAIN-VECTOR-REFILL-200

시각: 2026-08-15T15:54:26+09:00 · **REFILL_OK** · 3뇌 벡터 리셋+백필 · 1237아님 · hits 클레임 금지
목적=패치 후 1037–1236 캐시·예측·evolve를 지우고 3뇌 각각 `expand_pool(brains=[tag])` 200회 재생성.
원장·숙제·learn 보존. DB 파일 커밋 안 함.

HARD=통과. peek=0 · pred_1237=0 · MAX=1236.

## 1) 리셋

| 표 | 삭제 |
|----|------|
| pool_view_cache 1037–1236 | 600 |
| lotto_predictions 1037–1236 | 3000 |
| evolve_log 1037–1236 | 600 |

보존: lotto_draws · pool_hit_ledger · skill_homework · role_homework · learn_state.

## 2) 백필

| 뇌 | expand ok | fail | cache nonempty | evolve | pred(repack5) | fp 전→후 |
|----|-----------|------|----------------|--------|---------------|----------|
| stat | 200 | 0 | 200 | 200 | 1000 | 1030e5b6341dc581→1030e5b6341dc581 |
| markov | 200 | 0 | 200 | 200 | 1000 | cb8968f3ce9b4dff→cb8968f3ce9b4dff |
| review | 200 | 0 | 200 | 200 | 1000 | a505859e840ad332→a505859e840ad332 |

## 3) census

| 항 | 전 | 후 |
|----|----|----|
| 원장 | {'stat': 3000} | {'stat': 3000} |
| learn/skill/role | 0/600/1200 | 0/600/1200 |
| 숙제 소비 | ['stat'] | 동일 |

## 4) 판정

REFILL_OK면 3뇌 벡터가 지금 노브(review W_STRUCT 0.20 포함)로 다시 채워진 것. 성적 아님.
롤백=백업 `backups/20260815_VECTOR전_DB전체/`.

## 5) 금지 확인

1237 없음. 숙제ON/covering휠/S2/궁합 APPLY 없음. 동결 토큰 미수정. kweon 미접촉. DB git 안 함.

