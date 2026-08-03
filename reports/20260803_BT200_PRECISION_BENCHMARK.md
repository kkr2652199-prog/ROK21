# 백테스트 정밀 분석 · 외부 벤치마크 대조

HEAD `fa9c2aa` · SSOT `D:\ROK21` · 2026-08-03 · READ-ONLY 분석(코드 미변경)

Canvas: `bt200-precision-benchmark.canvas.tsx`

---

## 1. 한 줄 판정

| 축 | 판정 |
|----|------|
| K-FUTURE-WIRE | 소표본(n100) ge3=**0.1500** → QUICK **0.1350** → FULL **0.1184** (null **0.1137**로 수렴) |
| DB combined (BT200) | ge3=**0.145** · mean=**1.73** · null5 대비 +0.031 · p≈**0.10** (경계) |
| DB signal_repack | ge3=**0.275**는 **best_of_15** · 올바른 null≈**0.3036** 대비 **미달** (문서 null 0.1137 비교 = 허위 PASS) |

---

## 2. 근거 파일 (수치 SSOT)

| 지표 | 값 | 출처 |
|------|-----|------|
| WIRE n100 ge3 / mean | 0.1500 / 1.70 | `docs/benchmarks/20260803_KFUTURE_WIRE_N100.json` |
| WIRE QUICK200 | 0.1350 / 1.715 | `..._QUICK200.json` |
| WIRE FULL1182 | 0.1184 / 1.6912 | `..._FULL.json` |
| null_ge3 / pin | 0.1137 / 0.1447 | 동 JSON `references` · BENCH_PROTOCOL |
| combined / signal_repack | 0.145·1.73 / 0.275·2.25 | `docs/benchmarks/20260730_KSIGNAL_BACKTEST_tail100.json` · DB runs 5–8 |
| eval_mode | best_of_5_from_30 / best_of_15 | `tools/import_k_signal_backtest.py` |

---

## 3. 이론 null 재계산 (6/45 Hypergeometric)

단일 티켓(예측 6 · 당첨 6):

- E[X] = **0.8000**
- P(X≥3) = **0.023834**

독립 티켓 m장의 max:

| m | E[max] | P(max≥3) |
|---|--------|----------|
| 5 | **1.7289** | **0.1136** ≈ 문서 null **0.1137** |
| 15 | **2.2692** | **0.3036** |

함의: 문서 `null_ge3=0.1137`은 **best-of-5** 단위. `signal_repack`(best_of_15)에 붙이면 안 됨.

---

## 4. 내부 성적 정밀

### 4.1 K-FUTURE-WIRE (fusion walk-forward)

| 창 | n | ge3 | mean | Δnull | Δpin | p | enrich |
|----|---|-----|------|-------|------|---|---------|
| n100 | 100 | 0.1500 | 1.70 | +0.0363 | +0.0053 | 0.161 | FAIL |
| QUICK | 200 | 0.1350 | 1.715 | +0.0213 | −0.0097 | 0.199 | FAIL |
| FULL | 1182 | 0.1184 | 1.6912 | +0.0047 | −0.0263 | 0.317 | FAIL |

- patch gate(≥0.09 vs V2): **PASS** (전 창)
- pin(0.1447): **FAIL** (QUICK/FULL)
- quota 고정: markov **80%** / review **20%** / stat **0%**
- FULL early ge3=**0.099** &lt; null → 장기 안정성 약함

### 4.2 DB reset BT200 (1035–1234)

| strategy | eval_mode | ge3 | mean | 올바른 null | 해석 |
|----------|-----------|-----|------|-------------|------|
| combined | best_of_5_from_30 | 0.145 | 1.73 | 0.1137 | mean=이론 · ge3 경계 PASS |
| signal_repack | best_of_15 | 0.275 | 2.25 | 0.3036 | ge3·mean 모두 null 이하/근접 |

combined hit 분포(n=200): 0→2, 1→79, 2→90, 3→29 · 이론 best-of-5 기대: 2.1 / 74.2 / 101.0 / 21.3 / 1.4(4+)

---

## 5. 외부 벤치마크

| 출처 | 요지 | ROK21 대응 |
|------|------|------------|
| [arXiv:0806.4595](https://arxiv.org/abs/0806.4595) | lotto k/N Hypergeometric 감사 | null 분포 SSOT |
| [APJCRI 2025 6/45](https://doi.org/10.47116/apjcri.2025.02.43) | 시계열·χ² 대부분 무작위성 | 패턴 전제 약함 |
| [StatLotto NN](https://statlotto.com/posts/ai-lottery-prediction) | OOS backtest → random baseline | FULL null 수렴과 동형 |
| [GitHub LSTM lotto](https://github.com/XingGou516/AI-Lottery-Prediction-System-Experimental-Project-AI-) | 예측 불가 · ROI 전 음수 | ge3≠수익 |
| [Medium LSTM](https://medium.com/mind-code/statistical-deception-predicting-lottery-numbers-with-ai-d555b521e5a5) | AI mean ≈ random mean | K-O (mean 서열 금지) |
| [iamnk 36 models](https://www.iamnk.com/evaluation-results-can-machine-learning-beat-lottery-randomness/) | 약한 신호 가능, 실수익 별개 | lift≠edge |
| [Hai4320 vietlot](https://github.com/Hai4320/vietlot-suggestion) | 73방법 중 확정 edge≈1 · 소표본 붕괴 | n100→FULL 붕괴 전형 |

**YouTube:** 공정 walk-forward+null을 공개한 사례는 드물고, 회고 적중 영상이 다수. 위 실험·논문 쪽이 벤치 기준으로 우선.

---

## 6. 권고 (형 GO 대기 · 코드 미변경)

1. **P0** 모든 벤치 표에 `eval_mode` + 올바른 null 병기  
2. **P1** gate를 n100 단독이 아니라 FULL/기간분할로  
3. **P2** pin 갭(0.1184→0.1447)은 mean이 아니라 ge3+기간 안정으로  
4. **P3** 볼단위·Brier 등 K-S 후보(형 승인 후)

---

## 7. 비고

- 당첨 보장 없음 · 본 분석은 실험/통계 진단  
- 원본 kweon 미접촉 · 동결 토큰 미수정
