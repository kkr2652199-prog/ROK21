# K-TIER3-LEARN-CLOSE

시각: 2026-08-15T15:30:25+09:00 · **DOC_OK** · DOC · 코드 **불변** · APPLY **없음** · 1237아님
목적=ENGINE SPEC 권고#1+#2 · covering 문장고정 A. 3등 학습 엔진 트랙을 닫고 문장을 고정한다.

HARD=통과. MAX=1236 · pred_1237=0 · peek=0 · hits≥5=0.

## 0) 고정 문장 (이후 이 문장과 다르게 쓰지 말 것)

1. 6~8 cover_r3는 3등 학습·예측 엔진이 아니다. 같은 predict_sets 재샘플+S1 밖번호 선택이다.
2. covering t=3은 ‘풀 안 당첨 3개가 한 장에 들어가면 5등 형태’이지 한국 3등(본번호 5맞)이 아니다.
3. 3등 형태(5고정+1가변)는 9~10 shape_r2에 이미 있다. 3등P 학습기가 아니다. 코드 재라벨 없음.
4. COVER_MIN_HITS=3 숙제는 5등(3맞) 근사 복습이다. 3등 숙제가 아니다.
5. ‘과거 3등 사례를 학습해 3등P를 올리는 엔진’ 트랙은 닫는다.
6. 풀-먼저 greedy t-cover(H)는 후보만. S1과 반대 기하. 별 GO 없이 APPLY 금지.

## 1) 라이브 플래그 (코드 실측 · 미변경)

| 항 | 값 |
|----|-----|
| 숙제 소비 | ['stat'] · WIRE=True |
| COVER_SELECT_MODE | outside_union |
| SHAPE_CORE_MODE | set1 (S2 HOLD) |
| COVER_MIN_HITS | 3 |
| STRUCTURE_COVER_WIRE | False |
| STAT_POOL_LEARN_WIRE | True |
| 몰아주기 쿼터 | True · ['stat'] |

## 2) 원장 센서스 (읽기)

| 항 | 값 |
|----|-----|
| draws MAX | 1236 |
| pred_1237 | 0 |
| 원장 | {'stat': 3000} |
| stat 역할 | {'cover_r3': 600, 'focus_r1': 1000, 'shape_r2': 400, 'skill_native': 1000} |
| hits≥5 | 0 (stat 0) |
| evolve | {'markov': 200, 'review': 200, 'stat': 200} |
| E[3등] 3000장 | 0.083977 (SPEC 인용 · 성적 아님) |

hits≥5=0 은 E≈0.084와 정합. 엔진 실패 문장 금지.

## 3) 닫는 것 / 남기는 것

| 닫음 | 남김(별 GO) |
|------|-------------|
| 3등P 학습 엔진 · 5맞 손실 · 공식5코어 카탈로그 | greedy t-cover 휠 H |
| t=3을 3등으로 부르는 문장 | covering 장수 계약 SPEC |
| shape 코드 재라벨 | S2 consensus 재탕 금지 |

## 4) 판정

DOC_OK. 코드/노브/DB 쓰기 없음. 숙제ON·궁합prefer·covering APPLY·S2·1237 없음.
다음 APPLY는 형 1건.

## 5) 금지 확인

동결 토큰 미수정. kweon 미접촉. 1237 아님.

