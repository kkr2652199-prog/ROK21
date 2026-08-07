# K-PAST-LEARN-YT-BENCH — 과거학습 패치 × 신뢰 YouTube (2026-08-08)

- **판정:** `DOC_SURVEY` · wire=**False** · 당첨P↑ 비약속  
- 수치 SSOT: `docs/benchmarks/20260808_KPAST_LEARN_YT_BENCH.json`  
- 선행: FRAME_LOCKED · DETAIL-TUNE(CANDIDATE 미적용) · KYT_FILTER_BENCH

---

## 초보용 한 줄

우리가 만든 **과거학습 틀**을, “믿을 만한” 유튜브와 맞춰 봤다.  
결론: **요즘 자주 나온 번호를 세게 보는 방식 = 당첨 확률 올린다는 증거는 신뢰 영상에 없다.**  
→ 틀은 유지, decay 후보는 **보류 권고**, 예언형 영상은 **버림**.

---

## 0) 우리가 패치한 것 (벤치 대상)

| 항목 | 지금 값 | 한 줄 의미 |
|------|---------|------------|
| 뇌 | 과거학습만 | 다른 뇌는 안 건드림 |
| 짧은 창 | **26회** | 최근 반년 정도를 더 봄 |
| 짧은 창 비중 | **0.8** | 최근을 80% 반영 |
| decay | 기본 0.005/0.05 · 후보 0.01/0.05 미적용 | 옛날을 잊는 속도 |
| ASSOC/전이 | **OFF** | “이 번호 다음엔 저 번호” 가중 끔 |
| fusion | ge3 **0.135** | 전체 발권 성적 유지 |

---

## 1) 신뢰 게이트 (이것만 통과한 영상 분석)

**받음**
- 교육/수학 채널이거나, 실험으로 **한계를 보여 줌**
- 독립시행·도박사오류·covering처럼 **다시 확인 가능한** 주장
- “이번 주 1등 번호”를 팔지 않음

**버림**
- 회차별 필출·세로라인·정예풀 예언
- AI/LSTM 당첨 보장 톤
- 방법·데이터가 안 보이는 통계 마케팅

---

## 2) 채택 영상 (정밀 매핑)

| ID | 영상 | 신뢰 | 우리 패치와 연결 | 적용 |
|----|------|------|------------------|------|
| **YT-A** | [조코딩 · LSTM 로또](https://www.youtube.com/watch?v=3G3zExNItj0) | HIGH | 시퀀스 예측 실패 → ASSOC/LSTM OFF 정당화 | **유지(OFF)** |
| **YT-B** | [Numberphile · Randomness](https://www.youtube.com/watch?v=tP-Ipsat90c) | HIGH | 미출·줄무늬≠다음 확률↑ → soft/미출을 P↑로 쓰지 말 것 | **정책 유지** |
| **YT-C** | [다중필터 생성기](https://youtu.be/T7I3hEfQBlc) | MED※ | 합·홀짝·핫콜드=조합 모양 · ROK21 실측≈null | **필터 wire 금지** |
| **YT-D** | covering 27장 (논문 [arXiv:2307.12430](https://arxiv.org/abs/2307.12430) + standupmaths 해설) | HIGH | 다장 분산 아이디어 · EV↑ 아님 · 기존 PAIR-COVER **HOLD** | **참고만** |

※ YT-C는 이미 `20260808_KYT_FILTER_BENCH`에서 DB 재실측함.

---

## 3) 버린 영상 (예시)

| URL/유형 | 버린 이유 |
|----------|-----------|
| [I5nxvjDQrUg](https://www.youtube.com/watch?v=I5nxvjDQrUg) | 회차 예언·미출/세로라인 |
| [YZMfWyuzIyc](https://www.youtube.com/watch?v=YZMfWyuzIyc) | 정예풀·필출 법칙 |
| [XMb_T56sVLI](https://www.youtube.com/watch?v=XMb_T56sVLI) | AI/LSTM 당첨 예측 마케팅 |
| 멘사노트·골드 Shorts 등 | 주간 예언 · 재현 벤치 불가 |

---

## 4) 적용 가능 사례 (실제 액션)

| 사례 | 내용 | 지금 할 일 |
|------|------|------------|
| **A1** | 빈도·decay·hot/cold = **뽑기 모양/명분**이지 당첨↑ 아님 | 틀(26/0.8) 유지 · **DETAIL decay 적용 보류(KEEP_BASE)** |
| **A2** | ASSOC/시퀀스/LSTM 발권 가중 금지 | **OFF 유지** |
| **A3** | 합·홀짝·연번 필터 | annotate/warrant만 · soft에 강제 삽입 금지 |
| **A4** | covering 분산 | 과거학습 세부축 아님 · PAIR-COVER HOLD 참고 |

### DETAIL decay 후보에 대한 YT 판정
- 후보 `LONG=0.01` / `SHORT=0.05` 는 자체 hold만 +0.02, fusion 동일  
- 신뢰 영상도 “최근을 더 보면 이긴다”를 지지하지 않음  
→ **상수 적용 비권고 (KEEP_BASE)** · 형 GO로 확정

---

## 5) 초보용 비유

- **신뢰 영상** = 학교 수학 선생님 / 실험으로 “안 된다”를 보여 주는 사람  
- **예언 영상** = “이번 주 이 번호” 파는 사람 → 벤치에 안 씀  
- 우리 틀은 **번호 뽑는 습관(최근을 더 봄)** 을 정한 것  
- 유튜브가 말해 주는 것: 그 습관이 **로또 확률을 바꿔 주진 않는다** → 그래서 fusion이 그대로인 게 정상

---

## 6) 다음

- 형 GO: DETAIL **보류확정** / 그래도 적용 / 다른 세부축  
- tipster·LSTM wire **금지**
