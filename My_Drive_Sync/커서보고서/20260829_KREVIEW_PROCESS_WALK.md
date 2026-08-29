# K-REVIEW-PROCESS-WALK

시각: 2026-08-29T12:22:57+09:00 · **WALK_OK** · READ-ONLY · APPLY없음 · 1237아님 · 억지결함 금지
시점=부품. 금액뇌가 실제로 통과하는 선만 따라감. 없는 문제를 만들지 않음.

## 0) 내가 어떤 부품인가

1. `predict.run` → `engine.generate(10)` (reasonable이라 oversample 없음).
2. `build_review_weights`: 이월×1.8 → 끝수균등 → **순위혼합 0.70** → 3연속평탄.
3. 6개를 `random.choices`로 뽑고, tier1·극소패스·형태저울을 통과한 장만 남김.
4. `expand_pool`이 그 10장에 skill/cover/shape **스티커**를 붙임.
5. 몰아주기는 이 10장 이후의 다른 부품. 이번 점검 범위 밖.

as_of=1236 peek_ok=True · first_winners>0 **1221** · 0 **14** · 키없음 **0**.
learn adj={'carry_over_boost': 0.0, 'ending_digit_boost': 0.0, 'pair_boost': 0.0, 'consecutive_boost': 0.0, 'overdue_boost': 0.0, 'odd_even_balance': 0.0} · pred_1237=0 · MAX=1238.

## 1) 라이브 스위치

| 노브 | 값 |
|------|-----|
| PRIZE_WIRE | True |
| REVIEW_PRIZE_RANK_MIX | True |
| REVIEW_PRIZE_RANK_ALPHA | 0.7 |
| REVIEW_REASONABLE_SET | True |
| compose | reasonable |
| REVIEW_SHAPE_WIRE | True |
| REVIEW_RARE_SLICE_WIRE | True |
| REVIEW_SHAPE_KB_WEIGHT_WIRE | True |
| REVIEW_CONSEC_PASS_WIRE | False |
| REVIEW_KB7_WIRE | False |
| ROLE_SLOTS_WIRE | True |
| ROLE_TIER_LEARN_BRAINS | ['stat'] |

## 2) 1236에서 한 장 만들어 보기 (seed 42)

want 10 · got **10** · attempts **18** · reject `{'shape_kb': 6, 'accept': 10, 'tier1': 2}`.
build 후 가중0: 없음.
장당 직전회 겹침 평균 1.1.
expand_pool n=10 roles={'skill_native': 5, 'cover_r3': 3, 'shape_r2': 2} sources={'review_reasonable': 10}.

## 3) 캐시 1037–1236

행 200 · 10장미만 0 · role|source `{'skill_native|None': 1000, 'cover_r3|None': 600, 'shape_r2|None': 400}`.

## 4) 찾은 것 (억지 아님)

- **LABEL_STICKER** (실체불일치): 6~8 cover / 9~10 shape는 별 엔진이 아님. 같은 generate 10장의 스티커.
- **SHAPE_KB_RNG** (설계된거절): 형태저울이 추가 random으로 장을 다시 뽑게 함. 칼 아님. 시드 경로에 동전 한 장 더 있음.
- **FW_PROXY_OK** (정상): first_winners가 draws에 있음. 판매수 원본은 없음(프록시). 결함 아님.
- **LEARN_ADJ_IDLE** (정상): learn 조정값 비어 있음. 라이브 가중은 코드 상수(이월 1.8·순위혼합)로 돔.
- **TEN_OK** (정상): 1236에서 10장 완성. attempts=18 reject={'shape_kb': 6, 'accept': 10, 'tier1': 2}
- **KB7_IDLE** (정상): 7번은 collect만 하고 가중/거절에 안 들어감. 예측 부품 아님.

## 5) 인간 입장에서 헷갈리는 것 vs 고장

고장으로 보지 않음: 판매수 없음(프록시), 7번 읽기만, learn 빈값, 극소패스/tier1 거절.
헷갈림: 6~10장 역할 이름. 화면 문구의 ‘이월힌트’는 자신감 숫자이지 10장 선발이 아님.
이후 패치 자리: 몰아주기. 이번 APPLY 없음.

## 6) 금지 확인

DB write 없음. 동결 토큰 미수정. kweon 미접촉. 1237 아님.

