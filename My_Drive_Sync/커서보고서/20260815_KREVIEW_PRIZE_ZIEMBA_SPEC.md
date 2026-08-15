# K-REVIEW-PRIZE-ZIEMBA-SPEC

시각: 2026-08-15T15:09:39+09:00 · **SPEC_OK** · READ-ONLY · APPLY **없음** · 1237아님 · hits 클레임 금지
목적=review `prize_table`이 Ziemba/Chernoff 비인기 규칙과 얼마나 같은지 실측. 예측 불변.

권고=**HOLD**. prize_table = 0.90*crowd_unpopular(first_winners) + 0.10*structural_unpopular_prior (고번호·끝 0/8/9). Ziemba 규칙은 struct에 이미 있음. 이번 APPLY 없음.

## 0) 이미 있는 배선

`structural_unpopular_prior`: n≥40 ×1.40 · n≥32 ×1.25 · n≤12 ×0.80 · 끝 0/8/9 ×1.15.
`prize_table` = W_CROWD **0.9** × crowd(1/√first_winners) + W_STRUCT **0.1** × 위 사전. blend review **0.85**.
as_of=1236 이전 draws=1235 · first_winners>0 사용=1221 · 0스킵=14 · peek_max=1235 (<1236=True).
조합별 판매수 없음 → 1등 당첨자수 프록시. 당첨P 불변 · 몫 EV만.

## 1) 표 정렬 (Spearman ρ, n=45)

| 쌍 | ρ |
|----|---|
| prize vs struct(Ziemba형 사전) | 0.4425 |
| prize vs crowd(당첨자수) | 0.9353 |
| crowd vs struct | 0.1366 |
| prize vs hi32 더미 | 0.2957 |
| prize vs 끝0/8/9 더미 | 0.0232 |
| prize vs 캐나다12(48제외) 더미 | -0.0717 |
| struct vs 캐나다12 더미 | 0.3857 |

prize top12=[40, 37, 27, 34, 15, 45, 14, 20, 39, 13, 18, 43] · struct top12=[40, 38, 39, 41, 42, 43, 44, 45, 32, 33, 34, 35] · crowd top12=[27, 37, 40, 15, 14, 34, 20, 13, 45, 17, 1, 18].
top12 교집합 prize∩struct=**5** · prize∩crowd=**10** · prize∩캐나다11=**3**.

## 2) 캐시 세트 점유 (1037–1236 · 모니터 · 널=비복원 6×k/45)

널 1장: hi32=1.867 · end089=1.600 · bday=4.133 · 캐나다11=1.467.

| 뇌 kind | n | hi32 (Δ널) | end089 (Δ널) | bday (Δ널) | 캐나다11 (Δ널) |
|---------|---|-------------|--------------|------------|----------------|
| review pool | 2000 | 1.9595 (+0.0928) | 1.7595 (+0.1595) | 4.0405 (-0.0928) | 1.46 (-0.0067) |
| review repack | 1000 | 2.514 (+0.6473) | 1.772 (+0.172) | 3.486 (-0.6473) | 1.477 (+0.0103) |
| stat repack | 1000 | 1.775 (-0.0917) | 1.482 (-0.118) | 4.225 (+0.0917) | 1.409 (-0.0577) |
| markov repack | 1000 | 1.811 (-0.0557) | 1.273 (-0.327) | 4.189 (+0.0557) | 1.529 (+0.0623) |

Δ는 이론 대비 편차. **누가 낫다 금지**. review가 고번호·끝수에서 널보다 크면 prize축이 세트에 보임.

## 3) 채택 / 기각

| 항 | 판정 |
|----|------|
| 문헌 규칙을 prize_table에 **새로** 넣기 | **기각(이미 있음)** |
| W_STRUCT를 이번 턴에 올리기 | **HOLD** · 군중 0.90이 표를 지배(ρ prize-crowd). 올리려면 prize 게이트+별 GO |
| review에 apply_learn_boost 복사 | **기각** · 축 붕괴 |
| 캐나다 12를 한국 6/45에 그대로 고정 | **기각** · 48 없음·시장 다름. 구조 사전(고번호·끝수)이 이식분 |
| hits/ge3로 품질 점수 | **기각** |
| 숙제 ON / covering / S2 / 1237 | **기각** |

## 4) 다음 APPLY (형 GO 후만)

후보 A: `W_STRUCT_BY_BRAIN['review']`만 소폭↑ (crowd↓). 게이트=review prize 축 비악화 · stat/markov 캐시 불변 · peek0.
후보 B: 없음(모니터 유지). 권고는 **B=HOLD** — 규칙은 이미 들어가 있고, 이번은 대조 SPEC.

## 5) 금지 확인

DB write 없음. 동결 토큰 미수정. kweon 미접촉. 1237 아님.
