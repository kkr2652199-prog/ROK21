# K-RARE-TEMPLATE-TAXONOMY — 6/45 조합군 체계 · 이론 w

📅 2026-08-05 · **DOC** · wire=False  
전제: 티켓 1장 P = 1/8,145,060. 아래 \(w\) = 템플릿에 속한 조합 **개수**. 군확률 = \(w/\mathrm{C}(45,6)\).

---

## 1) 표기

| 기호 | 의미 |
|------|------|
| \(N=45, n=6\) | 로또6/45 |
| \(C(a,b)\) | 이항계수 |
| \(w\) | 템플릿 크기 |
| ultra | \(w\)가 매우 작거나 구조적으로 극단인 인스턴스군 |

---

## 2) 축 A — 홀짝 (odd = k)

\[
w(k)=\mathrm{C}(23,k)\cdot\mathrm{C}(22,6-k)\quad(k=0..6,\ \text{가능범위})
\]

| k | w (정확) | 비고 |
|---|----------|------|
| 0 | C(22,6)=74613 | all even · rare_bundle 있음 |
| 1 | C(23,1)·C(22,5) | |
| 2 | … | |
| 3 | 최대 질량 근처 | WARRANT emp≈null |
| 6 | C(23,6)=100947 | all odd |

**갭:** catalog는 양 끝(0,6)만. **전수 k=0..6 템플릿 테이블** 필요.

---

## 3) 축 B — 존 (low1-15 / mid16-30 / high31-45)

\[
w(l,m,h)=\mathrm{C}(15,l)\mathrm{C}(15,m)\mathrm{C}(15,h),\quad l+m+h=6
\]

특수: all-low \(w=\mathrm{C}(15,6)=5005\) · all-high 동일.

**갭:** all-low/high만 있음. **(l,m,h) 전수** 미구현.

---

## 4) 축 C — 합(sum) bin

합 \(S=\sum x_i\), 범위 21..255.  
\(w(S)=\#\{A\subset\{1..45\}:|A|=6,\sum A=S\}\) — 생성함수/DP로 정확 계산.

**갭:** rare_bundle **MISSING** · WARRANT는 mean≈138만.

---

## 5) 축 D — 스팬 · 최소간격

- span = max−min  
- `spread_min_gap7`: 인접 gap≥7 — 열거 집계 (PATTERN_META count=None)

**갭:** span bin 전수 테이블 없음.

---

## 6) 축 E — 연속

- 연속쌍 ≥1: \(w = C(45,6)-C(40,6)\) (갭변환)  
- run=6: \(w=40\) (윈도우 1-6 … 40-45)  
- run≥5: PATTERN_META ≈660 (정밀 포함제외는 R2+)

문헌: arXiv:0507469 · 1001.2972 · WARRANT emp≈0.517 vs null≈0.529

---

## 7) 축 F — 등차 · 극단분할 · combinadic 순위

| 키 | w | 비고 |
|----|---|------|
| arithmetic_6 | 165 | rare_bundle |
| split_exact_123_434445 | 1 | ultra |
| split_low3_high3_extreme | 14400 | C(10,3)² |
| rank_top/bottom1000 | 1000 | combinadic |

---

## 8) 축 G — LotteryCodex 4분할 (LO/LE/HO/HE)

번호장을 LOW/HIGH × ODD/EVEN 4칸으로 나눠 개수 튜플 템플릿.  
**갭:** 미구현 · R1 이후 스펙.

---

## 9) 축 H — as_of 상태 (티켓 고유 w 아님)

carry / overdue — Hypergeometric·대기시간. **군 w와 계층 분리.** WARRANT 참고.

---

## 10) v0 코어 → 확장

| 단계 | 내용 |
|------|------|
| v0 | `detect_patterns` / `enumerate_ultra_rare_catalog` (213) |
| v1 | odd k 전수 + zone (l,m,h) 전수 + sum DP |
| v2 | 4way LO/LE/HO/HE + span bins |
| v3 | (형 GO) annotate wire |

---

## 11) 극소 / 극소의극소 (운영 정의)

| 등급 | 초안 정의 |
|------|-----------|
| rare | \(w / C(45,6) < 10^{-3}\) 또는 양끝 홀짝·단일존 |
| ultra | consec_6 · exact split · arithmetic_6 · all-odd/even · all-zone · rank 말단 · (확장) sum 극단 bin |

개별 티켓 P는 동일. 등급은 **군 희소도**만 표시.

판정: **TAXONOMY DOC** · wire 없음
