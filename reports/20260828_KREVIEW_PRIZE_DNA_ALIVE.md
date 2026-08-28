# K-REVIEW-PRIZE-DNA-ALIVE

시각: 2026-08-28T11:35:34+09:00 · **DNA_PARTIAL** · READ-ONLY · APPLY없음 · 1237아님 · hits 클레임 금지
목적=지금 튜닝 뇌=금액뇌(review)인지, 비인기(남들이 덜 고르는) DNA가 코드와 1037–1236 캐시에 살아있는지 실측.

## 0) 한 줄

튜닝 뇌는 **금액뇌(review)** 가 맞다. 비인기 DNA는 **코드에 켜져 있다.** 실제 가중치 순위는 **이월(직전회 ×1.8)이 거의 전부**(ρ≥0.95). pool 10장은 고번호가 널보다 적고, **끝수 0/8/9만** 널보다 많다. 고번호·금액표 점수는 **몰아주기 5장(repack)** 에서 커진다. 당첨 확률은 안 바뀐다.

판정 **DNA_PARTIAL**. code_live=True · end_pool=True · hi_pool=False · hi_repack=True · prize_repack_best=True · carry_owns_weights=True · 표 crowd>struct=True.

## 1) DNA가 뭔가 (코드)

문헌(Thaler–Ziemba / Chernoff): 당첨P=동일, 남이 안 고른 조합이 당첨되면 **몫(금액)** 이 커진다.
이 레포는 조합별 판매수가 없어서 `prize_table` = W_CROWD **0.8** × (1/√first_winners) + W_STRUCT **0.2** × (고번호·끝 0/8/9).
엔진 `build_review_weights`가 이 표를 blend **0.85** 로 곱한 뒤 `random.choices`로 6개를 뽑는다. `PRIZE_WIRE`=True. 7번 WIRE=False.

같이 켜진 다른 DNA:
- 합리한장 `REVIEW_REASONABLE_SET`=True (compose=`reasonable`)
- 3연속 평탄 `REVIEW_SHAPE_WIRE`=True
- 극소형태 패스 `REVIEW_RARE_SLICE_WIRE`=True
- 형태지식 저울 `REVIEW_SHAPE_KB_WEIGHT_WIRE`=True
- 극소연속 PASS `REVIEW_CONSEC_PASS_WIRE`=False
- 이월 ×1.8 + 끝수 질량 균등(`neutralize_ending_digit_mass`)

as_of=1236 이전 1235회 · first_winners>0 사용=1221 · 0스킵=14 · peek_max=1235 (<1236=True) · MAX=1238 · pred_1237=0.

## 2) 표 정렬 (as_of 1236 · Spearman ρ, n=45)

| 쌍 | ρ |
|----|---|
| prize vs crowd(당첨자수↓) | 0.7937 |
| prize vs struct(고번호·끝089) | 0.68 |
| crowd vs struct | 0.1366 |
| prize vs hi32 더미 | 0.5211 |
| prize vs 끝0/8/9 더미 | 0.1006 |

prize top12=[40, 37, 45, 34, 39, 27, 38, 43, 20, 15, 14, 18]
가중치(풀경로) top12=[15, 43, 19, 40, 6, 7, 44, 28, 27, 32, 11, 34]
이월만 top12=[15, 6, 27, 7, 43, 19, 28, 44, 40, 32, 11, 34]
top12 교집합 풀∩prize=**5** · 풀∩이월=**12**.

## 3) 가중치 DNA (as_of 1236 한 시점)

| 쌍 | ρ |
|----|---|
| 최종가중 vs 이월만 | 0.9853 |
| 최종가중 vs prize표 | 0.2523 |
| 최종가중 vs (이월×prize blend) | 0.9916 |
| 이월만 vs prize표 | 0.1927 |

최종가중이 prize blend와 거의 같으면 금액 DNA가 가중치에 묻어 있는 것. 이월과도 높으면 두 DNA가 공존.

## 4) 캐시 장 점유 (1037–1236 · 방금 REFILL · 널=6×k/45)

널 1장: hi32=1.867 · end089=1.600 · hi40=0.800 · bday=4.133.

| 뇌 kind | n | hi32 (Δ널) | end089 (Δ널) | hi40 (Δ널) | bday (Δ널) |
|---------|---|-------------|--------------|------------|------------|
| review pool | 2000 | 1.8315 (-0.0352) | 1.8035 (+0.2035) | 0.7795 (-0.0205) | 4.1685 (+0.0352) |
| review repack | 1000 | 2.099 (+0.2323) | 1.718 (+0.118) | 0.838 (+0.038) | 3.901 (-0.2323) |
| stat pool | 2000 | 1.7875 (-0.0792) | 1.469 (-0.131) | 0.7345 (-0.0655) | 4.2125 (+0.0792) |
| stat repack | 1000 | 1.74 (-0.1267) | 1.537 (-0.063) | 0.663 (-0.137) | 4.26 (+0.1267) |
| markov pool | 2000 | 1.8615 (-0.0052) | 1.443 (-0.157) | 0.7415 (-0.0585) | 4.1385 (+0.0052) |
| markov repack | 1000 | 1.432 (-0.4347) | 1.453 (-0.147) | 0.515 (-0.285) | 4.568 (+0.4347) |

review가 고번호·끝089에서 널보다 크고, stat/markov보다 크면 **비인기 구조가 장에 보임**. repack(몰아주기 5장)은 pool과 다를 수 있음 · score5 공식은 이번 측정에서 안 바꿈.

## 5) 금액표 점수 (회차별 prize_table로 그 회 장을 채점 · 널 기대≈1.0)

| 뇌 kind | n | mean prize | Δ1.0 |
|---------|---|------------|------|
| review pool | 2000 | 1.006781 | +0.006781 |
| review repack | 1000 | 1.024564 | +0.024564 |
| stat pool | 2000 | 1.002128 | +0.002128 |
| stat repack | 1000 | 1.000946 | +0.000946 |
| markov pool | 2000 | 1.007512 | +0.007512 |
| markov repack | 1000 | 1.007165 | +0.007165 |

같은 표로 세 뇌를 채점한다. review mean이 1보다 크고 타뇌보다 크면 **남이 덜 고른 쪽(프록시)으로 금액뇌만 기울어 예측 장을 뽑은 것**.

## 6) 번호빈도 vs 표 (review pool 전수 · 표는 as_of1236 한 장)

ρ 빈도↔prize=0.1872 · ↔crowd=0.295 · ↔struct=0.0297 · ↔이월=0.3355.
창 200회 표가 매회 바뀌므로 이 ρ는 근사. 본증거는 §5.

## 7) 판정

**DNA_PARTIAL**. 적중↑ 클레임 금지. 판매수 원본 없음. 시동/몰아주기공식/1237예측 없음.
롤백 해당 없음(READ-ONLY).

## 8) 금지 확인

DB write 없음. 동결 토큰 미수정. kweon 미접촉. pred_1237=0.

