# 보조4뇌 역할 전환 제안 — 과거 신호 전달자 (AUX SIGNAL PIVOT)

📅 2026-07-29 · **문서+조사** · 코드 변경 없음 · HEAD 실측

## 1) 한 줄 요약

**지금:** 4보조 = 15장에 점수만 매기는 채점자 (AUX↔hit **무상관** 확인, K-BENCH-01)  
**형 제안:** 4보조 = 과거 DB 패턴을 **뇌 신호**로 3뇌에 전달 (수박장수 비유 — “이번 주 수박은 이런 날씨”)  
**판정:** 방향은 **검증 가능한 가설**. “불가능”이 아니라 **역할 재정의 실험**이 맞음.

---

## 2) 현재 구조 (팩트)

| 항목 | 실측 |
|------|------|
| 4보조 역할 | `coordinator._apply_aux_scoring` — 세트마다 score_set → confidence 가산 |
| 최종 5장 선정 | `apply_markov_wire_quota` **set_no_asc** (AUX로 컷 안 함) |
| AUX↔적중 | spearman ρ≈0 · p>0.05 (K-BENCH-01, n=17730 세트) |
| 피드백 | `walkforward`→`apply_feedback` → stat/review만 adjustments 소비 |
| K-BENCH-01-WIRE | tier 피드백 배선 **FAIL** ge3=0.1142 · pin 0.1447 미달 → **롤백** |

**쉬운 말:** 4보조는 “심사위원 점수”인데, 점수와 당첨이 **연결 안 됨**. 그래서 채점자 말고 **정보 전달자**로 바꿔보자는 제안.

---

## 3) 형 제안 — 수박장수 비유

```
[과거 DB] ──► 4보조(패턴·구간·빈도) ──► 신호 벡터 ──► 3뇌(stat/markov/review)
                  ↑ 채점 X                    ↑ 가중치 힌트만
```

- **채점자:** “이 조합 85점” → 현재 방식, hit과 무상관
- **신호 전달자:** “최근 50회 홀짝 3:3 비율 62%” “1~10번대 2개 이하 조합은 드묾” → 3뇌가 **필터·가중 힌트**로 소비

1군 참고(READ-ONLY): `postmortem_engine` + `pattern_store` — 당첨 후 `pool_cover`·`pack_gap`·`brain_summary` 축적 (`reports/20260729_BENCH_DEEP_IDEAS.md` · 1115행).

---

## 4) 과학적 근거 (인터넷 조사)

### 4.1 “814만분의 1이지만 조합마다 같지 않다”

| 주장 | 근거 | 한계 |
|------|------|------|
| **단일 조합** 당첨 확률은 동일 | 조합론 기본 · Lottery Codex 등 | 다음 회차 예측 불가 |
| **패턴 그룹**별 조합 **개수**가 다름 | 합계·홀짝·저고번 구간 — 중앙 합(≈138) 조합이 극단 합보다 **수백 배 많음** | 그룹 빈도 ≠ 개별 번호 예측 |
| **동일 조합 재출현** | C(45,6)≈814만 → 이미 나온 6개 재출현 기대 ≈ 0 | 독립 시행이면 재출현도 동일 확률 |
| **번호대 분포** | 6/45 로또 시계열 논문(KCI 2025): 대부분 무작위성 유지 · 24가설 중 소수만 기각 | “당첨 예측” 아닌 **공정성 검정** |
| **한국 실측 블로그** | 갭·핫콜드 백테스트 n=1000+ → 랜덤 대비 유의차 **없음**(p>0.27) | 단기 패턴 전략 기각 |

**열어볼 포인트 (보수적 닫기 금지):**
- 개별 번호 예측은 어렵지만 **구조적 특성**(합·홀짝·구간·AC)의 **집합 분포**는 장기적으로 중앙에 몰림 — SELMA·LottoPipeline 등은 이 축으로 **조합 필터·스코어**를 씀.
- StatLotto·EBDZ 등: “다음 번호 예측”은 불가하지만 **메타모델**(어떤 통계 전략이 최근에 신호가 일관적인지)은 가능하다고 구분.
- ROK21 K-Q: 볼 빈도 χ² p≈0.97 → **번호 예측 전제**는 기각. **구조 필터·다양성** 명분은 K-W/K-AA에서 유지.

### 4.2 post-draw 신호 특징 (문헌·오픈소스)

| 신호 유형 | 예시 | 용도 |
|-----------|------|------|
| Recency / gap | 번호별 미출 간격 | 가중 힌트 (기각됐으나 필터 명분) |
| Frequency | hot/cold 윈도우 | 구조 스코어 |
| Structural | 홀짝·합·연속쌍·AC·구간 | tier1 필터·AUX pattern |
| Aggregate ML | 합/홀짝 **개수** 예측 (EBDZ) | 개별 번호 대신 **분포** 학습 |
| Postmortem | pool_cover, pack_gap, brain_summary | **사후** 구조 — 1군 pattern_store |

---

## 5) ROK21 vs 1군 (READ-ONLY)

| 1군 | ROK21 현재 | 갭 |
|-----|-----------|-----|
| `postmortem_draw` 1115행 | K-BENCH-01 postmortem **일회성** JSON | 영구 축적 없음 |
| `pattern_store` ktier 등 | `draw_features` + POSTHOC | 신호→예측 배선 없음 |
| 4보조 분업 DB | 4보조 score_set만 | **신호 채널** 없음 |

---

## 6) 다음 실험 후보 3개 (READ-ONLY survey만)

### E1 — AUX-SIGNAL-01: 채점→신호 분리 survey
- **가설:** AUX 출력을 confidence 가산 대신 `{odd_even_bias, sum_band, zone_mix, gap_signal}` JSON으로 3뇌에 **read-only 힌트** 전달 시 ge3 변화?
- **방법:** stored pred + 신호 오버레이 시뮬 (DB write 없음) · pin 0.1447 대비
- **리스크:** coordinator 수정 — **별도 GO**

### E2 — POSTMORTEM-SIGNAL-02: 1군형 draw 특성 bin → ge3 stratify
- **가설:** ge3+ 회차의 draw_features(홀짝·합·AC) bin이 ge3-와 다르면, 그 bin을 **사전 힌트**로 쓸 수 있는가?
- **방법:** K-BENCH-01 `ge3_draw_features_diff` 확장 · K-BENCH-04 후보
- **리스크:** 표본 작음(ge3+ n≈130) · 다중비교

### E3 — PATTERN-HINT-03: pattern_store ktier 유사 신호 READ-ONLY 이식 survey
- **가설:** 1군 `ktier_win_json` 구조를 testlotto `draw_features`에서 재현 → stat/markov **가중 힌트**만 주입
- **방법:** `tools/_k_pattern_hint_survey.py` (신규, READ-ONLY) · 예측 코드 미수정
- **리스크:** 1군↔ROK21 스키마 차이 · 인과 역전 주의

---

## 7) K-BENCH-01-WIRE 결과 반영

| 항목 | 값 |
|------|-----|
| tier 피드백 WIRE | **FAIL** ge3=0.1142 · p=0.49 |
| 조치 | learn_state tier 배선 **롤백** |
| 시사점 | “등수 태그→boost” 축은 pin 개선 없음 → **4보조 역할 전환**이 더 유망한 다음 축 |

---

## 8) Verdict

| 질문 | 답 |
|------|-----|
| 4보조 채점 계속? | hit 무상관 → **유지만으로는 한계** |
| 신호 전달자 전환? | **검증 가능** · E1~E3 survey 후 형 GO |
| “로또는 맞출 수 없다”만? | 번호 예측≠구조·다양성·필터 최적화 — **후자는 실험 가치 있음** |

**다음 권고:** `K-AUX-SIGNAL-01` survey (READ-ONLY) — coordinator 변경은 형 별도 GO.

---

## 근거 파일
- `docs/benchmarks/20260729_KBENCH_POSTMORTEM.json`
- `docs/benchmarks/20260729_KBENCH01_WIRE_verify.json`
- `reports/20260729_4AUX_FEEDBACK_REVIEW.md`
- `reports/20260729_BENCH_DEEP_IDEAS.md`
- 인터넷: Lottery Codex 조합구성 · KCI 6/45 시계열(2025) · SELMA GitHub · StatLotto AI 메타모델
