# K-REVIEW-KB7-GEAR-A (2026-08-28)

- **판정:** `CONFIRM_OK` · APPLY **없음** · 코드 신규 배선 **없음**
- 형: 7번은 **A** 확정. `REVIEW_KB7_WIRE=False` 유지. 7번=4·5·6 읽기묶음 전용(예측 단계 아님). 예측은 1~4번. 5·6은 7번에 넣지 않고 모니터. 몰아주기·자동화·1237예측 동결. `K-AWAIT-HYUNG-NEXT`(7번 기어 명시) 이 결정으로 닫음.
- 근거: `docs/benchmarks/20260828_KREVIEW_KB7_GEAR_A.json`
- 확인: `kb7_future.py` · `engine.py` 읽기만

## A 확정 (박제)

| 항목 | 결정 |
|------|------|
| 7번 역할 | 4·5·6 `collect_before` **읽기묶음 전용** |
| `REVIEW_KB7_WIRE` | **False** 유지 |
| 예측 | **1·2·3·4번**이 담당 (`random.choices` + 1·3 패스 + 4 저울) |
| 5·6 | 모니터 유지. 7번 예측 재료로 **넣지 않음** |
| 몰아주기 · 자동화 · 1237/1239 예측 | **동결** |

닫힌 NEXT: 「7번 기어 무엇 켤지 명시」→ **A로 닫힘**.

## 현행 유지 확인 (쓰기 없음)

타깃 1237 예측 **생성 없음**. `_get_draws_before(1237)`만 읽어 묶음 스모크.

| 항목 | 값 |
|------|-----|
| peek as_of | **1236** (<1237) |
| bundle as_of / wire | **1236** / **False** |
| has shape / consec / assoc | **True** / **True** / **True** |
| shape n · assoc n | **1236** · **1236** |
| `apply_kb7_weights` | 입력 가중치와 **동일** |
| `should_skip_kb7` | **False** (거절 없음) |
| pred_1237 / pred_1239 | **0** / **0** |
| DB MAX | **1238** |

플래그 실측: 1 `REVIEW_REASONABLE_SET=True` · 2 `REVIEW_SHAPE_WIRE=True` · 3 `REVIEW_RARE_SLICE_WIRE=True` · 4 `REVIEW_SHAPE_KB_WEIGHT_WIRE=True` · 5 READ True · PASS **False** · 6 READ True · `PREDICT_USE_BONUS_LINKS=False` · 7 WIRE **False**.

엔진: `collect_before`는 호출됨. `if REVIEW_KB7_WIRE` 가드 때문에 apply/skip **미진입**. apply/skip 본문도 빈자리(identity).

## 5·6을 7 예측에 안 넣는 사유 (기존 벤치)

- 5세분 PASS: `20260827_KREVIEW_RARE_CONSEC_NETCHECK.json` net **0**
- 6 핫쌍몰림: `20260827_KREVIEW_ASSOC_CROWD_NETCHECK.json` p=**0.006** HOLD
- 유사도-next · 자리전이: 널 HOLD (동일 날짜 JSON)

## 이번 턴에 하지 않음

- `REVIEW_KB7_WIRE=True` · apply/skip 본문 채우기 · 5·6 패스/가중
- 몰아주기 · 전체조합 · `random.choices` · kweon · fetch-latest 표 재구축 · 1237 예측 행 생성

## 롤백

- 해당 없음(코드 불변). 7번 읽기까지 끄면 `REVIEW_ASSOC_KB_READ`/`REVIEW_CONSEC_KB_READ`/`REVIEW_SHAPE_KB_READ` 각자 False(이번 미실행).

## 파일

- `docs/benchmarks/20260828_KREVIEW_KB7_GEAR_A.json`
- `reports/20260828_KREVIEW_KB7_GEAR_A.md`
