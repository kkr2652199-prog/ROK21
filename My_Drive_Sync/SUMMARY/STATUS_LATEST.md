# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-27 KST  
📌 사유: K-AA 이론값 적용 · pattern/balance 실증 복귀

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| kweon | `264de3c` 동결 |
| 명분 | **`WARRANT.md`** (K-AA · warrant.py 동기화) |

---

## 1) K-AA 요지

| 항목 | 결과 |
|------|------|
| 폴백 합 | **150→138** |
| ac_target | **7→8** |
| consec | PMF 단조 · 0≠1 |
| 배선 | **PASS** (composite 항등 · conf 변화) |
| 단위검증 | pattern/balance **둘 다 PASS** |
| 라벨 | pattern/balance → **실증** |
| 회귀 | E[k]=**100** · SHA일치 · 롤백없음 |
| 판정축 | 조합론 참값 (A거리=관측) |

> 1등 확률↑ 아님 · A정합 개선 아님 · 명분만.

---

## 2) OPEN / PATCHED

K-AA·K-Z·K-V·K-S **PATCHED** · K-Y·X·W OPEN(기록) · K-M/N HOLD

---

## 3) 다음 (형)

1. pair/30·zone 목표 재정의 여부  
2. 미소비 키·무효 aux  
3. K-R / hyodo
