# K-NEXT-ROUTE-LIT-GITHUB-SURVEY — 다음 패치 전 노선 정밀 검토

📅 2026-08-10 KST · **DOC_SURVEY** · wire=**False** · ge3↑/당첨P↑ **비약속**

형 지시: 다음 진행 전 · 인터넷 논문 · 1티어 개발자·미친 개발자 GitHub 자료를 검토해  
**우리 노선에서 배울 점**만 정밀 분석.

선행 노선 SSOT:
- `K-BRAIN-CROWD-RESTRUCTURE` (선호·금액·과거학습 역할)
- `K-BRAIN-INDEPENDENT-WIRE` (hint 분리 · EV MARGINAL)
- `K-BRAIN-INDEPENDENT-TUNE` (SCORE_WEIGHTS APPLY)
- `K-PAST-LEARN-YT-BENCH` (LSTM/필터 기각 유지)

---

## 0) 우리 노선 한 장 (검토 프레임)

| 뇌 | 축 | 성공 정의 (우리) | 실패 정의 |
|----|----|------------------|-----------|
| **과거학습** `stat` | 당첨번호 숙제·패턴 | WF 명분·재료 정합 | “빈도=당첨P↑” 클레임 |
| **선호번호** `markov` | 군중 인기 (생일·1등다수회) | 인기 방향 정렬 | EV와 혼동 |
| **금액뇌** `review` | 비선호 → **당첨 시 몫(EV)** | prize_proxy↓ (음수) | ge3로 성적 자랑 |

공유 허용: `lotto_draws`만.  
데이터 한계: **조합별 판매수 없음** → `first_winners` 프록시.

---

## 1) 1티어 학술 (채택 우선순위)

### A. Thaler & Ziemba (JEP 1988) — **금액뇌 SSOT**
- DOI: [10.1257/jep.2.2.161](https://doi.org/10.1257/jep.2.2.161)
- 요지: 비인기 번호는 **P(win) 불변**, 당첨 시 **분배 몫↑ → EV↑**. 고번호·끝수 0/8/9 비선호.
- **배울 점 (우리):** 금액뇌 축 분리·ge3 금지 정책이 문헌과 일치. BLEND 튜닝도 **EV프록시만**으로.
- **안 배울 점:** 캐나다 6/49 구체 비인기 리스트를 한국에 그대로 이식 금지 (문화·용지 레이아웃 다름).

### B. Ziemba 2023 ARFE 재방문 — **역할 언어**
- DOI: [10.1146/annurev-financial-053122-021925](https://doi.org/10.1146/annurev-financial-053122-021925)
- 요지: lotto의 “스킬”은 **페이오프(비인기)** 쪽. luck–skill 분류.
- **배울 점:** UI/보고서에서 금액뇌=“당첨 잘 맞춤”이 아니라 **“당첨되면 덜 나눠 가짐”** 문구 고정.

### C. Chernoff / Cook–Clotfelter conscious selection — **선호·금액 공통 전제**
- Chernoff(메사추세츠) · Cook & Clotfelter(1993) “conscious selection”
- Significance 2012 요약: [Playing the lottery with a little bit of stats know-how](https://doi.org/10.1111/j.1740-9713.2012.00540.x) — **P(win) 고정, EV만 변경**
- **배울 점:** 선호번호뇌는 “사람들이 실제로 고르는 편향”을 **명시적 목표**로 둔 것이 학술적으로 성립.  
  금액뇌는 그 편향의 **반대 극**.

### D. Stern & Cover (JASA 1989) — **이상적 EV 추정 (우리 데이터 갭)**
- [Maximum Entropy and the Lottery](https://doi.org/10.1080/01621459.1989.10478862) · PDF: Stanford Cover paper91
- 요지: **번호별 판매 비율(marginal pick freq)** 가 있을 때 maxent로 조합 인기도 추정 → EV 시뮬.
- **배울 점 (설계):** 이상 게이트는 `pick_freq[n]` 기반.  
- **우리 한계:** 동행복권 공개 DB에 pick marginal **없음** → 지금 `first_winners`는 **열등 프록시**.  
  → 다음 패치에서 “Stern-Cover급”을 흉내 내려면 **새 데이터 소스 확보**가 선행(없으면 금지).

### E. Moffitt & Ziemba (arXiv 1801.02958 / 1801.02959) — **신디케이트·커버링**
- “trump ticket / buy the pot” · 군중이 커버 안 한 조합 존재 시 기대값
- **배울 점:** 다양성·비중복(세트 간 겹침↓)은 **부분 당첨 커버** 목적.  
- **안 배울 점 / 우리 기각 유지:** 전수 구매·커버링 wire는 자본·물류 문제 + ROK21 `K-PAIR-COVER`/`K-STRUCTURE-COVER` **HOLD**.  
  소규모 5장 발권에 “buy the pot” 논리 **과장 적용 금지**.

### F. Wang et al. / JdDM “Number preferences in lotteries” — **선호 메커니즘**
- [Judgment and Decision Making](https://www.cambridge.org/core/journals/judgment-and-decision-making/article/number-preferences-in-lotteries/47BA27051627CEED421AD3AEE255521E)
- 요지: 생일·자기관련 숫자(1–31, 특히 1–12) 선호 = 거의 보편.
- **배울 점:** `structural_popular_prior` 1~12/1~31 가중은 문헌 정합.  
  선호뇌 튜닝 시 **구조사전 vs crowd(first_winners)** 비중(W_CROWD/W_STRUCT)이 핵심 노브.

### G. Baker–Lee / JRSS “Combination Preference Model” (2011) — **조합 단위 선호**
- DOI: [10.1111/j.1467-985x.2011.00693.x](https://doi.org/10.1111/j.1467-985x.2011.00693.x)
- 요지: 번호뿐 아니라 **조합·패턴**(용지 모양) 선호.
- **배울 점 (다음 후보):** 금액뇌/선호뇌를 번호 가중만으로 끝내지 말고,  
  장기적으로 **세트 shape**(연번·대각·저합) 인기도 프록시 검토 여지.  
- **지금 wire 금지:** shape 데이터 없음 · ROK21 필터 벤치≈null.

---

## 2) GitHub — “미친 개발자” 중 **정직한 것** vs **마케팅**

### ✅ 배울 프로세스 (채택 권고 · 코드 복붙 금지)

| 저장소 | 왜 1티어에 가깝나 | 우리 노선 매핑 |
|--------|-------------------|----------------|
| **[Hai4320/vietlot-suggestion](https://github.com/Hai4320/vietlot-suggestion)** | “알고리즘이 무작위 이기나?”에 **아니오**로 답함. backtest + split-half + NIST + 정직 라벨. 29사이클 대부분 붕괴. | **R38/R39 정신의 외부 실증**. 과거학습·ge3 튜닝에 “작은 n에서 운=실력” 경고 재확인. |
| **[lgpcarames/lottery_numbers](https://github.com/lgpcarames/lottery_numbers)** (fork) | P(win)↑ 안 함. (1) 세트 간 3겹침 제한 (2) 저번호(생일대) **회피**로 몫↑. | **금액뇌·covering 철학과 동일 축**. 우리 `prize` prior·고번호 선호와 정렬. |
| **kyr0/lotto-ai** | README가 스스로 “fancy RNG”라고 고백. | LSTM wire 금지 정당화 (YT-A와 동일). |

### ⚠️ 참고만 (전략 메뉴는 흥미 · 성적 클레임 불신)

| 저장소 | 내용 | 판정 |
|--------|------|------|
| **wiserguy1964/lottery_predictor** | STRAT01~09 · Markov(STRAT05)·빈도·휠. “79.9점” 등 | 점수 체계 불투명·null 대비 미흡 → **벤치 복제 금지**. 아이디어만: 다중 전략 **라벨 분리**(우리 3뇌와 유사). |
| **cpeoples/powerpredict** | Transformer+LSTM 앙상블 · 면책 “예측 불가” | 아키텍처는 화려 · **적중 축 wire 금지**. 다양성(Hamming)만 참고 가능. |

### ❌ 버릴 것
- “AI가 로또를 푼다” 톤 · tipster · 회차별 필출
- pick frequency 없이 maxent EV를 “완성”이라고 주장
- 해외 비인기 번호 리스트 하드코딩

---

## 3) 뇌별 · 배울 점 / 버릴 점 (정밀)

### 3.1 금액뇌 (`review`) — 문헌 **최강 지지**
| 배울 점 | 다음 패치 함의 | wire |
|---------|----------------|------|
| EV만 재라 (Thaler–Ziemba) | BLEND↑ 후보는 **prize_proxy_delta**만 | 후보 |
| 고번호·끝수 0/8/9 | `structural_unpopular_prior` 유지·미세조정 | 후보 |
| Stern–Cover는 pick marginal 필요 | 데이터 없으면 **강한 EV 모델 금지** | **否** |
| 학습 효과(비인기 회귀) | 시대별 prize_delta 모니터링 (이미 3구간) | 측정유지 |

### 3.2 선호번호 (`markov`) — 문헌은 “인기 존재” 지지 · **EV와 반대**
| 배울 점 | 함의 | wire |
|---------|------|------|
| 1–31/1–12 선호 보편 (Wang/JdDM) | prefer prior 정당 | 유지 |
| 인기≠당첨P | 선호뇌 성공지표=인기정렬 · ge3 금지 | 유지 |
| 용지 기하·오른손 편향 (Ziemba) | 한국 용지 기하 미실측 → **구조사전만** | 신규조사 전 否 |

### 3.3 과거학습 (`stat`) — 문헌·정직 GH가 **적중P↑에 회의**
| 배울 점 | 함의 | wire |
|---------|------|------|
| Hai4320: 대부분 전략 null | decay/핫콜드 ge3 튜닝 **보류 유지** | 否 |
| Numberphile/YT 벤치 | 숙제·명분 축으로만 | 유지 |
| 숙제 WF(1..N-1) | 이미 확정 길 — 문헌과 충돌 없음 | 유지 |

### 3.4 독립·몰아주기 — 문헌보다 **공정성 엔지니어링**
| 배울 점 | 함의 |
|---------|------|
| 다중 전략 분리(wiserguy 메뉴 / 우리 3뇌) | hint·SCORE 분리 완료 → 방향 맞음 |
| Hai4320 3게이트 | 다음 BLEND도 **split-half + 시대 consistent** 필수 |
| Covering 다양성 | 이미 HOLD · 재개 시 EV/커버 이중 목적 명시 |

---

## 4) 데이터 갭 (정직 표)

| 문헌이 쓰는 것 | 우리 DB | 결론 |
|----------------|---------|------|
| 번호별 판매비율 | ❌ | Stern–Cover급 EV **불가** |
| 조합별 판매수 | ❌ | 조합 EV 직접 계산 **불가** |
| 1등 당첨자수 `first_winners` | ✅ | 인기 **프록시** (열등·유지) |
| 당첨번호 시계열 | ✅ | 과거학습 숙제 |
| 이월·판매액 | 부분 ✅ | 보정 약하게만 |

→ **다음 패치의 천장:** 프록시 품질 개선이지, “완성된 복권 헤지펀드”가 아님.

---

## 5) 다음 패치 준비 — 권고 순서 (wire 전)

1. **①군중 BLEND 소튜닝 (권장 유지)**  
   - 노브: `BLEND_STRENGTH` / `W_CROWD` (review 우선, markov는 prefer_delta)  
   - 게이트: 기존 EV·prefer 축 + **early/mid/late consistent** + (가능하면) 전반/후반 split  
   - ge3 **금지**

2. **②명분 샘플 리뷰**  
   - 문헌 교훈: 명분이 “운 자랑”이 되지 않게, **재료·태그·컨닝 여부**만 검수

3. **신규 아이디어 HOLD (데이터 전)**  
   - 세트 shape 인기 (Baker–Lee)  
   - pick-frequency 크롤/확보 전 Stern–Cover  
   - covering 재개

4. **명시적 기각 유지**  
   - LSTM/Transformer 적중 wire  
   - 해외 비인기 번호 하드코드  
   - “buy the pot” 소액 발권 과장

---

## 6) 한 줄 결론

우리 노선(적중숙제 / 인기추적 / 몫EV · 독립배선)은 **1티어 경제학·행동·정보이론과 방향이 맞고**,  
GitHub에서 배울 것은 **화려한 모델이 아니라 Hai4320식 정직 게이트**다.  
다음 패치는 **금액·선호 축의 BLEND만**, Stern–Cover급은 **판매비율 데이터 없이 금지**.

## 파일
- `docs/benchmarks/20260810_KNEXT_ROUTE_LIT_GITHUB_SURVEY.json`
- 본 보고서 · 커서보고서 동기
