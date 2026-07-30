# TESTLOTTO 4·5등 적중 표시 버그 수정 (20260730)

## 증상
- 1214회 등: hero 「4등 1 · 5등 2」 vs pool 카드 실제 5등만 존재 → 등수·하이라이트 불일치
- 1~5등 모달: `lotto_predictions` 기준 빈 목록 (pool-view 15세트 미반영)
- 1235회(미추첨): 당첨번호 없을 때 혼선 가능

## 근본 원인
**채점 SSOT 분리.** UI pool-view(10+5 walk-forward)로 카드를 그리면서, hero 요약·모달은 `detail`/`lotto_predictions` 구 DB 적중 수를 그대로 집계함. 1214 예: detail 4등 1건(stat 구버전 세트) ≠ pool 5등 4건.

## 수정 (`app/static/js/testlotto.js` v20260730d)
1. `_testlottoResolveActualRef` — `/api/testlotto/draws/{n}` SSOT 당첨번호
2. `_testlottoPoolViewScoreRows` — pool+repack 45세트 동일 채점(본번호 6 + 보너스 2등만)
3. hero 요약·1~5등 모달 → **표시 중인 pool-view 기준** 집계
4. `renderBrainSetCard` — `Number()` 등수 비교(문자열 `"4"` 오판 방지)
5. 미추첨(1235) — `matched_count=-1` · 「추첨 전」 유지

## 검증 (7021 · 브라우저 CDP)

| 회차 | 당첨번호 | hero 요약 | 비고 |
|------|----------|-----------|------|
| 1214 | 10·15·19·27·30·33 +14 | 5등 4 | stat #8·#9 하이라이트 3개·5등 배지 일치 |
| 1234 | 1·15·19·31·35·43 +27 | 5등 1 | PASS |
| 1200 | 1·2·4·16·20·32 +45 | 5등 2 | PASS |
| 1235 | (없음) | 「아직 추첨 전」 | false tier 없음 |

## 변경 파일
- `app/static/js/testlotto.js`
- `app/static/index.html` (cache bust `20260730d`)
