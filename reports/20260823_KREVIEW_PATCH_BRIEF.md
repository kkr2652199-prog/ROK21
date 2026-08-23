# K-REVIEW-PATCH-BRIEF (2026-08-23)

- **판정:** `DISCUSS_OK` · 코드 APPLY 없음 · 예측 없음
- 형: 지금까지 패치를 번호순·쉽게. 맞는 부분 패스, 다른 부분 이후 세부패치. 엔진 가동 시 모든 부품이 과거 회만 보고 다음 회를 뽑는지.
- 근거: `engine.py` · `data_service._get_draws_before` · `routes.fetch-latest` · 벤치 `20260823_KREVIEW_*.json`

## A) 이번 통작업 패치 번호순 (금액뇌)

| # | 이름 | 상태 | 예측에 쓰는가 | 한 줄 |
|---|------|------|---------------|--------|
| 1 | 합리한 장 `REVIEW_REASONABLE_SET` | **켜짐** | **예** | 장마다 1–45에서 6개. 이상한 장(tier1) 버림. 45소진 아님 |
| 2 | 3연속 평탄 `REVIEW_SHAPE_WIRE` | **켜짐** | **예** | 가중 가운데 ×0.75. 당첨 연번쌍은 널과 비슷해서 과다 억제 |
| 3 | 극소형태 패스 `REVIEW_RARE_SLICE_WIRE` + 목록 21245 | **켜짐** | **예** | 얇은 조각 장이면 버리고 다시 뽑음 |
| 4 | 회차 형태지식 `testlotto_draw_shape_kb` | 저장·읽기 | **아니오** | 1–**1238** 특징 저장. `summarize_before`만. 번호 불변 |
| 5 | 극소연속 표 11서명·1600 | 저장·읽기 | **아니오** | `PASS_WIRE=False`. 기존 run≥4는 tier1이 이미 거절 |
| 6 | 번호 연관 `testlotto_draw_assoc` | 저장·읽기 | **아니오** | **1–1237**만. 6+보너스 쌍·비슷조합. 번호 불변 |

꺼진 잔존(롤백용): 앞채움 `POOL_FRONTLOAD` 빈집합 · 45소진 `REVIEW_SEQ_DISTRIBUTE=False`.

손 안 댐: **몰아주기** `score5`. 특성 기어(prize/carry 값) 이번 통작업에서 변경 없음. `random.choices` 라인 동결.

## B) 가장 중요 질문 — 지금 시스템인가?

**뼈대는 맞다. 완성된 자동 시동은 아직 아니다. 보완이 맞다.**

이미 맞는 것:

- 예측 호출 시 `_get_draws_before(target)` → `draw_no < target`만. 타깃 당첨 미입력.
- 켜진 부품(1·2·3 + 기존 이월/prize/끝수균등/tier1)은 그 과거 리스트로 다음 회 장을 뽑는다.
- 학습진화 `EVOLVE_AUTO` 기본 **OFF**. 적중으로 가중 진화하지 않음(형 말과 같음).

아직 아닌 것:

- 4·5·6은 예측 전에 **책을 펴기만** 하고, 뽑는 공식에 **안 넣음**.
- 새 회차가 `fetch-latest`로 들어와도 assoc/형태지식/극소목록을 **자동 재구축하지 않음**. 피드백·evolve_diag만 후처리.
- assoc 표는 1237까지, 형태지식은 1238까지 — 회차 창이 서로 다름.
- 「시동 한 번이면 모든 부품이 자동」은 형이 나중에 하자고 한 단계. 지금은 수동 패치.

## C) 형 확인용

맞으면 패스. 다르면 그 번호만 세부패치.

롤백 키: 1=`REVIEW_REASONABLE_SET=False` · 2=`REVIEW_SHAPE_WIRE=False` · 3=`REVIEW_RARE_SLICE_WIRE=False` · 4=`REVIEW_SHAPE_KB_READ=False` · 5=`REVIEW_CONSEC_KB_READ=False` · 6=`REVIEW_ASSOC_KB_READ=False`
