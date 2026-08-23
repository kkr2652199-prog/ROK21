# K-REVIEW-KB7-SLOT (2026-08-23)

- **판정:** `APPLY_OK` · 7번 자리 · 기어 OFF · 몰아주기 미접촉
- 시각: 2026-08-23T13:26:29+09:00
- 형: 1·2·3 패스. 4·5·6은 엔진이 읽고 7번으로 미래장 참고. 단계 튜닝 필요. 아이디어 요청.
- 근거: `20260823_KREVIEW_KB7_SLOT.json`

## 이번 패치

- `kb7_future.collect_before` = 4형태 + 5연속 + 6연관 한 묶음
- `REVIEW_KB7_WIRE=False` · apply/skip 빈 자리
- 1236 발권 OFF==ON 동일 `True` n `10`
- 묶음 as_of `1235` · shape `True` n `1235` · consec `True` · assoc `True` n `1235`
- pred_1237 `0` · pred_1239 `0` · MAX `1238` · wire `False`

## 다음 단계(형 1건)

- 4상세 / 5상세 / 6상세 중 하나, 또는 7번 한 소스만 기어 시험
- 자동화 시동 아직 아님

## 아이디어(성적 클레임 아님)

- 4: 최근 회 보통 홀수·폭만 참고. 극단은 이미 3번이 자름
- 5: PASS_WIRE 켜면 1600은 3번과 중복. 서명 flatten은 별 GO+게이트
- 6: 핫쌍 가중이 아니라 한 장에 핫쌍 과다하면 패스(몰림 방지). 1238 표 추가는 별 오더
- 7: 스위치 하나. 4만/5만/6만 켜서 단계 튜닝. prefer 0.005 게이트

## 롤백

- `REVIEW_KB7_WIRE=False`(이미) · 엔진 collect 호출 제거

## 파일

- `kb7_future.py` · `engine.py`
- `20260823_KREVIEW_KB7_SLOT.json` · `20260823_KREVIEW_KB7_SLOT.md`
