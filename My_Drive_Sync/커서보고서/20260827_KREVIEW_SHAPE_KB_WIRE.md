# K-REVIEW-SHAPE-KB-WIRE (2026-08-27)

- **판정:** `APPLY_OK_HOLD_LIVE` · 4번 저울 · 라이브 OFF · 몰아주기 미접촉
- 시각: 2026-08-27T04:17:40+09:00
- 형: 4번을 읽기만→저울. 보너스는 본번호6만. 칼 아님. 자동화 아님.
- 근거: `docs/benchmarks/20260826_KREVIEW_SHAPE_KB_WIRE.json` (지시문 산출물명 20260826 · 작업일 20260827)
- 종료체크: 20260827 접두가 비어 `20260826_*.md`만 있었음 → 본 파일로 당일 접두 보충. 본문 수치=위 JSON.

## S0 보너스 (READ-ONLY)

- 4번 특징 본번호6 `True` · 보너스는 라벨 `True`
- 정정 필요 `False` (이미 6개만 계산 · 표 재구축 없음)
- 1–1237 본번호6 평균 sum `138.2797` span `32.692` odd `3.0719`
- 가상(6+보너스) sum `160.6378` span `34.5441` odd `3.5756`
- 차이(가상−6) sum `22.3581` span `1.8521` odd `0.5037`
- 1237 feat_sum==본번호합 `True` bonus라벨 `36`
- 5번 consec 서명=sorted_nums(6) · PASS_WIRE `False`
- 6번 유사=본번호 · bonus_links 저장 `True` · 예측잠금 `True`
- 채점 5+보너스=2등 `True` · 5맞=3등 `True`
- pred_1237 `0` · pred_1239 `0` · MAX `1238`

## S1 배선

- 위치: `engine.generate` · 3번(rare_pass) 통과 후 · `keep_set_by_hist`
- 방식: 저울. 역사 흔한 모양 통과↑. 3번과 겹치는 거절 없음
- 재료: as_of 이전 odd/run/sum/span/AC. 보너스 미사용. peek 없음
- 플래그 `REVIEW_SHAPE_KB_WEIGHT_WIRE` 기본 **False** · review만 · 7번 WIRE 불변

## S2 게이트 1137–1236 n100

- HARD peek `0` n_ok `100` size_bad `0` bonus_in `0` hard `True`
- Δprefer `-0.000631` Δprize `-0.001106` iso `True`
- changed `100` extreme_ok `True` design `True`
- OFF rare `0.0` run4 `0.0` · ON rare `0.0` run4 `0.0`
- shape_score Δ `0.039397` (모니터·성적아님)
- 코드적용조건 `True` · 라이브 `False`
- elapsed `40.9`s

## S3

- 라이브 확정 없음. 켜려면 형 GO.
- 롤백=`REVIEW_SHAPE_KB_WEIGHT_WIRE=False`
- 자동화·몰아주기·전체조합·1237예측 없음

## 파일

- `draw_shape_kb.py` · `engine.py` · `draw_assoc.py`(예측잠금) · `kb7_future.py`
- `20260826_KREVIEW_SHAPE_KB_WIRE.json` · `20260826_KREVIEW_SHAPE_KB_WIRE.md` · `20260827_KREVIEW_SHAPE_KB_WIRE.md` · `20260827_KENDCHECK_GAP.md`
