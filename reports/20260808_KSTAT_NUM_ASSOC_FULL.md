# K-STAT-NUM-ASSOC-FULL — 전수 A+B+C+F (2026-08-08)

- **판정:** `NOISE_LIKE` · wire=`False` · brain=**과거학습**
- anchors n=**1035** · range [200,1234] · elapsed=1.69s

## vs null (F)

| 지표 | real | null_sim | Δ |
|------|-----:|---------:|--:|
| mean_lift | 0.998221 | 1.001851 | -0.00363 |
| union15_cover | 5.206763 | 5.255072 | -0.048309 |
| rank15_top1_hit | 0.140097 | 0.147826 | -0.007729 |

## B) 임계 스윕 top1_hit

- thr=1.1: real=**0.116908** · null=0.128502 · Δ=-0.011594
- thr=1.15: real=**0.119807** · null=0.130435 · Δ=-0.010628
- thr=1.2: real=**0.118841** · null=0.125604 · Δ=-0.006763

## A) 구간별 mean_lift / union_cover / top1_hit

- **early** n=346: meanL=0.996313 · union=5.216763 · top1=0.135838
- **mid** n=345: meanL=1.002089 · union=5.217391 · top1=0.144928
- **late** n=344: meanL=0.996259 · union=5.186047 · top1=0.139535

## 패턴 읽기

- 전수 n=1035 anchors [200,1234]
- mean_lift real=0.998221 null=1.001851 Δ=-0.00363
- union15_cover real=5.206763 null=5.255072 Δ=-0.048309
- rank15_top1_hit real=0.140097 null=0.147826 Δ=-0.007729
- thr1.1 top1_hit real=0.116908 null=0.128502 Δ=-0.011594
- thr1.15 top1_hit real=0.119807 null=0.130435 Δ=-0.010628
- thr1.2 top1_hit real=0.118841 null=0.125604 Δ=-0.006763

## 해석

- 당첨P↑ 클레임 금지.
- NOISE_LIKE = 전수에서도 실측≈null → 과거학습 발권 패치 근거 약함.

- tool: `tools/_k_stat_num_assoc_full.py`
