# K-EVOLVE-LOG-FIELD-SPEC

시각: 2026-08-15T15:36:16+09:00 · **SPEC_OK** · READ-ONLY · APPLY **없음** · 1237아님
목적=COOCCUR 다음 B. evolve_log **필드 확장 SPEC**. 롤링 χ² 모니터. WEIGHT 0 유지. 새 테이블 없음.

권고=**HOLD**. 이미 있는 features_json에 롤링 모니터 키만 추가하면 된다. 새 파이프 불필요. 이번 턴은 SPEC만. 키를 넣으면 쓰기 경로가 바뀌므로 APPLY는 별 GO.

HARD=통과. peek=0 · weight≠0=0 · pred_1237=0 · MAX=1236.

## 0) 지금 있는 것 (실측)

| 항 | 값 |
|----|-----|
| PK | (draw_no, brain_tag) |
| 행 | {'markov': 200, 'review': 200, 'stat': 200} |
| as_of | 전부 N-1 (어긋남 0) |
| weight_applied≠0 | 0 / 600 |
| WEIGHT_APPLIED 코드 | 0.0 |
| FEATURE_LAMBDA_WIRE | False |
| EVOLVE_AUTO | False |
| 지금 features 키 | ['has_apply_learn_boost', 'n_pool', 'n_repack', 'weight_applied'] |
| 컬럼 수 | 20 (ALTER 없음) |

지금 `write_evolve_diag` features = `weight_applied, n_repack, n_pool, has_apply_learn_boost`.
구 `evolve_log` 경로의 repack_avg_* 는 진단 일반화 경로에 **안 들어감**.

## 1) SPEC (코드에 아직 없음)

- 새 테이블 **금지**. ALTER **금지**. `features_json` 키만 추가.
- 쓰기=`write_evolve_diag(brain)` 만. `click_feedback` 본체 금지.
- `weight_applied` **0.0** 유지. `FEATURE_LAMBDA_WIRE` **False**. `EVOLVE_AUTO` **OFF**.
- 롤링 창 **52회** 당첨번호 빈도 vs 균일 χ² → `roll52_chi2` (당첨공 모니터. 사면분포 아님).
- 세트 모니터: `repack_mean_consec` · `repack_mean_hi32` · `repack_mean_prefer` · `repack_mean_prize`.
- prefer/prize 점수는 **기록만**. `prefer_table` 수정·궁합 APPLY 아님.
- χ²를 APPLY 게이트로 쓰지 않음. mean_hits를 예측 입력으로 쓰지 않음.

| 키 | 의미 |
|----|------|
| `roll52_chi2` | 직전 52회 당첨번호 빈도 vs 균일 χ². 모니터만. APPLY 게이트 금지. |
| `roll52_n` | 창 길이(기본 52). 부족하면 그 길이. |
| `repack_mean_consec` | repack5 연번쌍 평균. 세트 속성. |
| `repack_mean_hi32` | repack5 고번호(≥32) 평균. prize 축 모니터. |
| `repack_mean_prefer` | repack5 set_crowd_score(prefer_table). markov 축 모니터. |
| `repack_mean_prize` | repack5 set_crowd_score(prize_table). review 축 모니터. |

## 2) 왜 APPLY 안 하나

- 키를 넣는 순간 쓰기 경로가 바뀐다. 이번은 SPEC.
- 회차 6개 χ²는 무의미(DISCUSS 반박). 롤링도 공정성 감시이지 예측 입력이 아님.
- 새 테이블을 만들면 `backtest_runs=0` 같은 SOFT 공백이 하나 더 생긴다.

## 3) 판정

SPEC_OK · HOLD. 코드/DB 쓰기 없음. 숙제ON·궁합 APPLY·covering휠·S2·1237 없음.
다음 APPLY는 형 1건.

## 4) 금지 확인

동결 토큰 미수정. kweon 미접촉. 1237 아님.

