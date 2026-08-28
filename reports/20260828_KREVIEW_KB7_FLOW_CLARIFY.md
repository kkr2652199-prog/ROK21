# K-REVIEW-KB7-FLOW-CLARIFY (2026-08-28)

- **판정:** `DISCUSS_OK` · APPLY **없음** · 코드/플래그 **불변**
- 형: 7번이 엔진에서 1~6 데이터를 참고해 번호를 예측하는 단계인지. 맞으면 진행, 아니면 설명. 흐름대로 7에서 예측한다고 봄.
- 근거: `app/testlotto/brains/review_brain/engine.py` · `kb7_future.py` · `reports/20260823_KREVIEW_KB7_SLOT.md`

## 한 줄

**아님.** 지금 번호는 7번에서 뽑히지 않는다. 7번은 4·5·6 **읽기 묶음 자리**이고 기어 OFF라 장 구성에 안 넣는다.

## 지금 엔진이 장을 만드는 순서 (`generate`)

1. `_get_draws_before(target)` 과거만 (T 당첨 미입력).
2. **1번** 합리한 장 + **2번** 연번평탄 + prize/이월 — `build_review_weights`.
3. `kb7.collect_before` = 4형태+5연속+6연관 **읽기**. `REVIEW_KB7_WIRE=False` 이면 `apply_kb7_weights` **미적용**(그리고 WIRE True여도 함수 본문이 가중치를 그대로 반환).
4. **`random.choices`로 6개 뽑음** ← 실제 번호 생성. 동결 라인.
5. **1번** `tier1` · **3번** `should_pass` 극소패스.
6. **4번** `keep_set_by_hist` 저울 (`REVIEW_SHAPE_KB_WEIGHT_WIRE=True`). hist는 kb7.shape를 빌려 씀(4번 라이브이지 7번 기어가 아님).
7. **7번** `should_skip_kb7` — WIRE False라 **항상 통과**(거절 없음). WIRE True여도 본문이 `return False`.

몰아주기는 이 엔진 뒤 `signal_pool` score5. 미접촉.

## 7번이 아닌 것 / 인 것

| 오해 | 코드 |
|------|------|
| 7번 = 1~6 데이터로 예측 | **1·2·3은 이미 앞에서 장을 바꿈.** 7은 1·2·3을 읽지 않음. |
| 7번 단계에서 예측한다 | **예측(6개 추출)은 `random.choices`.** 7은 그 전후 빈 훅. |
| 4·5·6이 7을 통해 예측에 들어감 | 4는 **별 플래그로 이미 라이브**. 5·6은 읽기만. 7 WIRE **False**. |

7번의 원래 자리(K-REVIEW-KB7-SLOT): 「4·5·6을 한 소스로 모아 **미래에** 넣는 스위치」. 지금은 모으기만.

## 5·6을 7에 넣으면

이미 검증에서 순수증분/널 편향이 없어 HOLD.

- 5세분 PASS: net **0** (3번과 동일 집합)
- 6 핫쌍몰림: p=**0.006** HOLD
- 유사도-next: Δ **−0.024** p=**0.85** HOLD
- 자리전이: Δ **−0.028** p=**0.89** HOLD

그래서 이번 턴 **진행(APPLY)하지 않음**. 5·6을 예측 재료로 켜는 것은 형 GO가 있어도 게이트+사유가 다시 필요.

## 형이 원하는 흐름과 맞추려면 (미적용 · 별 GO)

가능한 해석 두 개. 이번 턴 선택하지 않음.

- A: 7번 기어에 **4만** 참고를 모은다(4는 이미 저울 라이브 · 이중배선 주의).
- B: 「예측은 7에서만」으로 1·2·3·4를 7 뒤로 옮긴다 = **구조 변경**. 동결 라인·1·2·3 패스와 충돌. 비권고.

## 상태 불변

- `REVIEW_KB7_WIRE=False`
- pred_1237 **0** · 몰아주기 미접촉 · 자동화 아님
- 다음=형 1건. 7번을 켜려면 「7번 기어 시험 GO」+ 무엇(4만/빈자리유지)을 명시.

## 파일

- `reports/20260828_KREVIEW_KB7_FLOW_CLARIFY.md`
- `app/testlotto/brains/review_brain/engine.py` · `kb7_future.py` (읽기만)
