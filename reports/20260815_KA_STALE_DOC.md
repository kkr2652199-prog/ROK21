# K-A-STALE-DOC — FINDINGS K-A 구표본 표시

시각: 2026-08-15 · **DOC_OK** · 코드 APPLY 없음 · ge3/mean 서열 금지 · 1237아님

근거: `My_Drive_Sync/SUMMARY/FINDINGS.md` K-A · K-O · `docs/benchmarks/20260815_KSTAT_LEDGER_REALIGN_BT200.json`

---

## 0) 한 줄

**K-A의 0.760은 옛 표본이다.** 이 숫자로 엔진을 고치거나, 뇌를 줄 세우면 안 된다. 이번 턴은 대장에 ‘구표본’만 적었다.

---

## 1) 원기록 (지우지 않음)

| 항목 | 값 |
|------|-----|
| ID | K-A |
| 옛 상태 | OPEN |
| 옛 요약 | stat mean 0.760 < baseline 0.788 / 이론 0.80 |
| 창 | 최근 100회 **1135–1234** · 500세트 |
| 위치 기록 | `predict_stat_fairy.py` · `predict_statistical.py` |
| 당시 조건 | K-B 해소 전 패치 금지 |

K-B는 이미 **PATCHED**다. 그래서 ‘K-B 때문에 패치 보류’는 더 이상 이유가 아니다.  
그래도 **패치하지 않는다.** 이유는 K-O다.

---

## 2) 왜 패치 근거가 아닌가

1. **K-O:** 한 장 기대 적중 = 6×(6/45) = **0.80** 상수. 세트 mean만으로 뇌·패치 서열을 매기면 안 된다.
2. **창이 다르다.** 0.760 = 1135–1234 · 500세트. 지금 모니터 = 1037–1236 · skill 1~5 mean_all **0.83** (`20260815_KSTAT_LEDGER_REALIGN_BT200`). 창·장수·경로가 달라 **빼서 좋아졌다/나빠졌다**고 쓰면 안 된다.
3. **0.83도 이론 0.80 근처**다. 실력 향상이 아니다 (K-O).
4. 게이트는 prefer/prize 비악화다. mean으로 APPLY 금지.

---

## 3) 이번 변경

| 파일 | 변경 |
|------|------|
| FINDINGS.md / .txt | K-A 상태 **OPEN → HOLD** · 요약에 **STALE_DOC · 구표본 · 패치금지 · mean서열금지** |
| 예측 코드 | **없음** |
| knobs | **없음** |

---

## 4) 하지 말 것

- 0.760을 목표로 `predict_statistical.py` / `random.choices` 수정
- 0.760 vs 0.83 으로 ‘엔진이 좋아졌다’ 클레임
- mean으로 stat/markov/review 서열
- 1237 양산

---

## 5) 다음

리스트 #1~#3 끝. #4 `K-STAT-SHAPE-CORE-V2`는 **새 아이디어 있을 때만**(S2 consensus 재탕 금지).  
잠금 재탕·발권·합동·타뇌는 형 지시 시. 1237아님.
