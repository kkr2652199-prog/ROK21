# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-26 KST  
📌 사유: K-09 컷오프 구현·누수 비유의 CLOSED · EV 순효과 Y풀 재검증 생존 · K-09 전제 라벨 제거

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| 로컬 | `D:\ROK21` · **7021** |
| SSOT | `kkr2652199-prog/ROK21` |
| 원본 | `D:\3kweon` 미접촉 |
| 복원 | `RESTORE.md` |

---

## 1) K-09 최종

| 항목 | 값 |
|------|-----|
| 구현 | `learn_state_cutoff.py` · 피드백 재구성(b) |
| 플래그 | `ROK21_LEARN_CUTOFF=1` + `set_learn_as_of` · **기본 OFF** |
| OFF 해시 | 동일 |
| 누수 X−Y (200회) | −0.010 CI[−0.024,+0.004] **비유의** |
| review X/Y | 둘 다 mean **0.767** |
| **상태** | **CLOSED** (실질 무해) · 플래그는 가용 |

**K-09 미해결 전제 라벨: 제거.**

---

## 2) EV (Y 컷오프 풀 · 창200)

| 지표 | 값 |
|------|-----|
| mean A / D | **0.798** / **0.792** |
| 순배율 | **1.033** CI **[1.019, 1.048]** |
| 정지규칙 | **YES → 배선 유지** |
| env | `ROK21_EV_RERANK=1` opt-in · 기본 OFF |

환급률 대비: +3.3% ≠ 티켓 구매 EV.

---

## 3) 동결·운영 플래그

- 동결: `random.choices` · `_get_draws_before` · boost  
- `ROK21_EV_RERANK` 기본 OFF  
- `ROK21_LEARN_CUTOFF` 기본 OFF  

---

## 4) 다음

1. (선택) 운영 opt-in 시험  
2. K-10 tier1 완화 보류 유지  
3. 열린 K: 00,02,05~08,10~12  

---

## 5) 산출물

`reports/20260726_ROK21_K09컷오프_EV재검증.md`  
`docs/benchmarks/20260726_K09컷오프/`
