# K-REVIEW-CONSEC-ROOT-AND-PRIZE-ISOLATE

시각: 2026-08-29T13:08:37+09:00 · **SPEC_OK** · READ-ONLY · APPLY **금지** · 1237아님 · hits 클레임 금지
목적=① 쌍번호 뿌리가 tier1 연번기준인지 2번 억제인지 ② 비인기 하락이 4번 저울인지 RNG 분기인지.

## 파트 A · S0) 현재 노브

tier1 연번 기준: **연번<4** (`max_consec >= 4` 탈락). 라이브 3연속 통과=True · 4연속 탈락=True.
2번 억제강도: **×0.75** · `REVIEW_SHAPE_WIRE`=True. 가운데(3연속 능선)만 깎음. 쌍 자체 가중은 아님.
4번 WIRE=True · RUN_NEUTRAL 파일 False=True. prize표 미접촉=True.
게이트 1137–1236 n=100 peek=0 seed=42.

## 파트 A · S1) tier1 연번기준 오프라인

코드 미변경. `engine.tier1_filter`만 메모리 교체 후 복원. 라이브=4번 ON · 2번 ×0.75.

| 기준 | run2 | run3 | prize | struct |
|------|------|------|-------|--------|
| 연번<4 (현재) | 0.675 | 0.043 | 0.022583 | 0.036781 |
| 연번<3 | 0.612 | 0.0 | 0.022954 | 0.035348 |
| 연번<2 | 0.0 | 0.0 | 0.023369 | 0.037174 |

Δ(<3−<4) run2=-0.063 run3=-0.043 prize=0.000371 struct=-0.001433.
Δ(<2−<4) run2=-0.675 run3=-0.043 prize=0.000786 struct=0.000393.

## 파트 A · S2) 2번 억제강도 오프라인

코드 미변경. `apply_consec_flatten(factor=…)`만 메모리 교체 후 복원. tier1 연번<4 · 4번 ON.

| 강도 | run2 | run3 | prize | struct |
|------|------|------|-------|--------|
| ×0.75 (현재) | 0.675 | 0.043 | 0.022583 | 0.036781 |
| ×0.60 | 0.689 | 0.041 | 0.022235 | 0.035074 |
| ×0.50 | 0.625 | 0.036 | 0.021634 | 0.034223 |

Δ(0.60−0.75) run2=0.014 prize=-0.000348 struct=-0.001707.
Δ(0.50−0.75) run2=-0.05 prize=-0.000949 struct=-0.002558.

## 파트 A · 판정

run2를 가장 크게 줄인 축: **tier1_<2** → 뿌리=**tier1**.
연번<2는 쌍을 원천 차단하므로 run2=0은 정의상. 비동어 비교는 연번<3(Δrun2 **−0.063**) vs 2번×0.50(**−0.05**) vs ×0.60(**+0.014**) — 그래도 **tier1**.
2번×0.60은 run2를 늘리고 prize/struct를 같이 깎음. ×0.50은 run2를 조금 줄이나 prize/struct 동반악화.
연번<2는 prize·struct 비악화. 연번<3은 prize 비악화 · struct만 −0.001433.
cut map={'tier1_<3': -0.063, 'tier1_<2': -0.675, 'shape2_0.60': 0.014, 'shape2_0.50': -0.05}.
비인기 동반악화 prize={'tier1_<3': False, 'tier1_<2': False, 'shape2_0.60': True, 'shape2_0.50': True} · struct={'tier1_<3': True, 'tier1_<2': False, 'shape2_0.60': True, 'shape2_0.50': True}.

## 파트 B · S0) RNG 분기 지점

1. `keep_set_by_hist`가 `random.random()`을 씀 → `random.choices`와 **같은 전역 RNG**.
2. 저울이 거절하면 generate가 한 바퀴 더 돌아 **choices를 더 소비**.
3. 같은 seed로 OFF/ON을 따로 `generate(10)`하면 첫 저울 `random()` 이후 시퀀스가 갈라짐.

## 파트 B · S1–S2) 시드 정렬 vs 분기

기존 분기 Δ(직전 BALANCE) prize=-0.00192 struct=-0.005521.
이번 분기(OFF generate vs ON generate) Δprize=-0.00192 Δstruct=-0.005521 Δrun2=0.008.
고정10장 후필터(시드 안 갈라짐, 장수 줄 수 있음) keep평균=7.43 skip=0 · Δprize=-0.000538 Δstruct=0.000381.
공유후보 정렬 10vs10 Δprize=-0.000759 Δstruct=0.000415 Δrun2=0.001 skip=0.

비인기 하락 주범: prize=**RNG_분기** · struct=**RNG_분기** · 종합=**RNG_분기**.
정렬|Δ|이 분기의 절반 미만이면 RNG 분기. 정렬이 분기의 75% 이상을 같은 부호로 유지하면 저울.

## 판정

**SPEC_OK**. APPLY **없음**. 파일 플래그/prize표/`random.choices`/몰아주기/kweon 미수정.
pred_1237=0 · pred_1239=0 · MAX=1238 · restored=True.

## 금지 확인

코드/플래그/DB write 없음(산출물 md/json만). 1237/1239 예측 없음. hits 클레임 없음.

