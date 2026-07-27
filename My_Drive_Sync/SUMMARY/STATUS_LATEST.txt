# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-27 KST  
📌 사유: K-A~K-L 등재 · K-B/C/D READ-ONLY 원인규명

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · main |
| 로컬 | `D:\ROK21` · **7021** |

---

## 1) K-B 결론 (최우선)

| 항목 | 판정 |
|------|------|
| 역전 원인 | **서로 다른 난수 재생성** (교집합 69회 세트일치 **0**) |
| pred 희소 | **1149–1179** 연속 31회 갭 (07-25 재기록) |
| 성적 SSOT(mean) | **`testlotto_brain_review.predicted_sets_json`** |
| 운영 캐시 | `lotto_predictions` (비교용 SSOT 아님) |

---

## 2) K-C / K-D

| ID | 판정 |
|----|------|
| K-C | referee는 **best 누적 avg** 반영 · set mean과 지표 불일치(버그 아님) |
| K-D | testlotto 최초부터 coordinator · fusion 클릭경로 **원래 없음**(의도적 3+4) |

---

## 3) FINDINGS

K-A~K-L OPEN 등재. K-12b → K-L 승계.  
보고서: `reports/20260727_KB_KC_KD_원인규명.md`

---

## 4) 동결

- `random.choices` · K-E 형승인 전 수정금지  
- K-A는 K-B 해소 전 패치 금지  

---

## 5) 다음

1. K-B 성적 SSOT 선언 확정  
2. K-C/J 설계(형)  
3. hyodo 1232~1234 (형 승인)  
