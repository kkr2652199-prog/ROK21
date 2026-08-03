# K-RARE-BUNDLE 적용 여부 정밀 분석 (수학·과적합·인터넷·1D/2D/3D)

HEAD `522a9a8` · 2026-08-03 · READ-ONLY 분석(엔진 wire 미적용)  
Canvas: `rare-bundle-apply-analysis.canvas.tsx`  
대상 SSOT: `docs/benchmarks/20260803_KRARE_BUNDLE_survey.json` · `reports/20260803_KRARE_BUNDLE_SURVEY.md` · `app/testlotto/rare_bundle.py`

---

## 0. 한 줄

**극소 번들은 「구조(템플릿) 희귀」 카탈로그로는 올바르다. 「당첨/ ge3 확률 상승」용으로 강제 적용하면 수학적으로 이득이 없고, 과배제 시 ge3가 내려갈 수 있다. → wire HOLD · 관측/UX/λ실험만.**

---

## 1. 깃허브·레포에서 확인한 의뢰 산출물

| 항목 | 값 | 출처 |
|------|-----|------|
| ID | K-RARE-BUNDLE-01 | survey JSON |
| C(45,6) | **8,145,060** | 보고서·코드 |
| catalog / ultra / hits | **213 / 183 / 1235** | JSON summary |
| 역사 6연속 | **0** | JSON |
| API | `/rare-bundles/summary` · `/ultra` | 보고서 |
| refs | arXiv:math/0507469 · MathDoctors · LotteryCodex | `rare_bundle.REFS` |
| 커밋 | `796c92c` · docs sync `522a9a8` | git log |

코드 주석도 이미 명시: **「구조별 빈도 ≠ 개별 조합 확률」**.

---

## 2. 수학 검증

### 2.1 개별 조합 (1등)

\[
P(\text{특정 6수}) = \frac{1}{\binom{45}{6}} = \frac{1}{8{,}145{,}060}
\]

ultra든 popular든 **동일**. 극소 강제 발권 ≠ P(1등)↑.

### 2.2 구조(템플릿) 빈도 — K-RARE가 잰 것

| 구조 | 개수 | 비율 |
|------|-----:|-----:|
| consec_6 (6연속 창) | 40 | ≈4.91e-6 |
| split 1·2·3+43·44·45 | 1 | ≈1.23e-7 |
| 3홀3짝 | C(23,3)C(22,3) | ≈**0.335** |

「극소」= 템플릿이 814만 중 **얇은 slice**. LotteryCodex frequency ratio와 같은 층위.

### 2.3 연속번호 — 자주 나오는 축 (혼동 주의)

arXiv:math/0507469: \(p(n,m)=1-\binom{n-m+1}{m}/\binom{n}{m}\)

| 게임 | P(≥1쌍 연속) |
|------|-------------:|
| 6/49 (논문) | ≈0.495 |
| **6/45 (재계산)** | ≈**0.529** |

즉 **「2연속 포함」은 흔하고**, **「6연속 전체」는 극히 드묾**. 둘을 한 희귀도로 묶으면 안 됨.

### 2.4 「미당첨 ultra 183」 과해석

\[
\mathbb{E}[\text{consec\_6 적중 횟수}|1235] = 1235 \times \frac{40}{8145060} \approx 0.006
\]

역사 0건·미당첨 183은 **정상**. “안 나왔으니 곧 나온다/특수하다”는 도박사의 오류.

---

## 3. 인터넷·문헌 검등

| 출처 | 요지 | ROK21 |
|------|------|-------|
| LotteryCodex equal probability | 조합당 P 동일 · 템플릿 빈도만 다름 | 의뢰 분석과 정합 |
| LotteryCodex frequency ratio | rare template = 공간 비율 작음 · 예측 아님 | ultra 강제 금지 |
| arXiv math/0507469 | 연속쌍 확률 ~50% | 6연속≠연속쌍 |
| PINNED_TESTLOTTO_TUNING | 814만=**보조 좌표** · 뇌 아님 | 유지 |
| LEAKAGE_POLICY §6 | 패턴배제=레이어 · 과배제→ge3↓ · λ검증 | 적용 시 필수 |
| K-EXCLUDE / WIRE FULL | 배제·fusion 소표본 붕괴 | rare wire 위험 |

---

## 4. 적용하면 무엇이 오르나?

| 목표 | ultra 강제 적용 | 판정 |
|------|-----------------|------|
| P(1등) / 세트 ge3 | 불변 또는 **하락**(과배제) | **비추천** |
| 구조 설명·교육 UI | 상승(이해도) | **추천** |
| 당첨 시 공유 배당↓ 휴리스틱 | 가능(행동 가정) | UX만 · 벤치 외 |
| pin 0.1184→0.1447 | 무관 | **별도 엔진 축** |

---

## 5. 1D · 2D · 3D 사용안

### 1D (단일 축)
- feature: `max_consec_run`, `parity_skew`, `zone_skew`, `combo_rank_814`, `rarity_score`
- 용도: 로그·UI 배지 · **가중 0 (예측 미반영)**
- 위험: 낮음

### 2D (교차 템플릿)
- (저/고)×(홀/짝) 또는 (연속런)×(구역) — LotteryCodex식 **prevalent 정렬** vs **rare 회피**
- 용도: λ 스윕 survey (QUICK→FULL)
- 위험: 중간 · wire HOLD

### 3D (융합 스택)
\[
\text{score}=\alpha\cdot\text{brain}+\beta\cdot\text{diversity}+\gamma\cdot f(\text{rarity})
\]
- 기본 **γ=0** (현 live)
- γ&gt;0: 극소 회피(구조 prevalent 쪽) · γ&lt;0: 극소 선호
- 둘 다 ge3↑ 수학 보장 없음 → A/B만

---

## 6. 권고 로드맵

| 단계 | 내용 | GO |
|------|------|-----|
| **A0** | API·DB 관측 유지 (현재) | 기본 |
| **A1** | UI 고지: 「구조 희귀 / 당첨확률 동일」 | 저위험 |
| **A2** | 1D feature 로그만 (미반영) | 관측 |
| **A3** | 2D/3D γ QUICK200→FULL | 형 GO |
| **A4** | **pin갭** (우선 실익 축) | 형 GO |

---

## 7. 결론

1. 의뢰 분석(K-RARE-BUNDLE)의 **조합론·문헌 근거는 타당**.  
2. **확률 상승용 적용은 HOLD** (동등확률 정리와 충돌).  
3. 쓸 거면 **1D 관측 → 2D 템플릿 λ → 3D γ** 순 · null/eval_mode 병기.  
4. ge3/pin을 올리려면 rare가 아니라 **pin갭·볼단위** 축이 맞음.

*당첨 보장 없음 · 원본 kweon 미접촉*
