# K-BRAIN-CROWD-RESTRUCTURE — 선호번호·금액뇌·과거학습 역할 재배치

📅 2026-08-08 KST · 형 지시: 흐름술사→선호번호 / 복습왕→금액뇌 / 과거학습은 특성에 맞게 유지·진행 · 엔진 견고 · 학술 벤치

## 1) 역할 잠금 (tag 유지 · 표시명 변경)

| tag | 구 표시명 | 신 표시명 | 축 | 엔진 |
|-----|-----------|-----------|----|------|
| `stat` | 과거학습 | **과거학습**(유지) | 당첨번호 **적중·패턴 숙제** | `stat_brain` + past_learn soft (재료=1..N-1) |
| `markov` | 흐름술사 | **선호번호** | 군중 **인기** | 전이·동반 + `crowd_signal.prefer_*` |
| `review` | 복습왕 | **금액뇌** | 군중 **비선호 → 당첨 시 몫(EV)** | 이월·복습 + `crowd_signal.prize_*` |

- DB/코드 키 `stat`/`markov`/`review` **불변** (호환).
- `METHOD_TO_TAG`에 구명 `흐름술사`·`복습왕` 잔존 호환.

## 2) 데이터 한계 (정직)

공개 `lotto_draws`에는 **조합별 판매수 없음**.

| 필드 | 용도 |
|------|------|
| `first_winners` | 그 회 당첨조합의 **인기 프록시** (다수=선호 쪽 신호) |
| `total_sales` | 선호 가중 보정(약) |
| 구조 사전 | 문헌: 생일대 1~31 선호 / ≥32·끝수 0·8·9 비선호 |

→ 선호번호뇌 = 인기회차 번호 + 생일대.  
→ 금액뇌 = 저당첨자수 회차 번호 + 고번호·비선호 끝수.  
**당첨 확률을 올린다고 주장하지 않음.** 금액뇌는 당첨 시 분배 몫(EV) 축.

## 3) 학술·벤치 포인트

| 출처 | 요지 | 반영 |
|------|------|------|
| Thaler & Ziemba, *JEP* 1988 | 비인기 번호 → P(win) 불변, 당첨 시 몫↑ | 금액뇌 `prize_table` |
| Ziemba et al. / Chernoff conscious selection | 생일·패턴으로 선택이 균일하지 않음 | `structural_*_prior` |
| Ziemba 2023 *ARFE* 재방문 | unpopular numbers = luck-skill(페이오프만 스킬) | 역할 분리 문서화 |
| 기존 ROK21 `K-PAST-LEARN-EV-RELABEL` | `first_winners` 인기편향 실증 · soft태그≠EV | 금액뇌는 **별축**(태그 soft 재정의 아님) |

롤백 env: `K_CROWD_PREFER=0` · `K_PRIZE_EV=0`.

## 4) 배선 (엔진 견고 원칙)

1. **기존 엔진 코어 유지** (markov 전이·visit / review 이월·neutralize).
2. `random.choices` **라인 미수정** — 가중치 테이블만 `blend_weights`로 혼합 (`BLEND_STRENGTH=0.55`).
3. `_get_draws_before` / learn cutoff 경로 그대로 (컨닝 금지).
4. 공통 모듈: `app/testlotto/brains/shared/crowd_signal.py`.
5. UI: `registry.py` + `testlotto.js` / `testlotto-detail.js`.

## 5) 스모크 (as_of 1236 · draws last=1235)

| 뇌 | method | crowd.mode | 비고 |
|----|--------|------------|------|
| stat | 과거학습 | — | 숙제축 유지 |
| markov | 선호번호 | prefer | prefer_top 예: 12,7,3,13… (저번호 쪽) |
| review | 금액뇌 | prize | prize_top 예: 40,37,45,39… (고번호 쪽) |

판정: **SMOKE_OK** · 3뇌×5세트 · method/tag 일치.

## 6) 과거학습 판단 (이번 턴)

- 숙제 기록(1216~1235)은 이미 FILL_OK.
- decay/재료 하드코드 튜닝은 **게이들 MDD 때문에 보류**(이전 DECISION-GATE).
- 이번 턴은 **역할 분리·군중축 배선**이 우선. 과거학습 숫자 튜닝은 별도 GO.

## 7) 다음

- 선호/금액 **성적 주장 전**에는 ge3가 아니라 EV프록시(당첨회 `first_winners`·몫) 게이트 설계가 필요.
- 또는 형 ①1235 명분 리뷰 / ④정지.

## 파일

- `app/testlotto/brains/shared/crowd_signal.py` (신)
- `markov_brain/{engine,predict}.py` · `review_brain/{engine,predict}.py`
- `brains/registry.py` · `app/static/js/testlotto*.js`
- `docs/benchmarks/20260808_KBRAIN_CROWD_RESTRUCTURE.json`
