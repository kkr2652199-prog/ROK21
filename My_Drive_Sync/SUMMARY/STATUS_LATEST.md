# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-27 KST  
📌 사유: SSOT=ROK21 확정 · 커밋 UTF-8 로컬설정 · FINDINGS K-08/K-09 경위 보고

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| **SSOT** | `kkr2652199-prog/ROK21` · main |
| 로컬 | `D:\ROK21` · **7021** |
| kweon 동결 | `D:\3kweon` · HEAD **`264de3c`** · 미접촉 |
| 복원 | `RESTORE.md` |

---

## 1) 인코딩

| 항목 | 값 |
|------|-----|
| i18n.commitEncoding | utf-8 |
| i18n.logOutputEncoding | utf-8 |
| core.quotepath | false |
| chcp | 949 (콘솔) |
| 깨짐 원인 | 메시지 주입 경로(PowerShell ascii 등) · rewrite 안 함 |
| 신규 커밋 | Python UTF-8 `-F` 사용 |

---

## 2) K-07 / FINDINGS 요지

| 항목 | 값 |
|------|-----|
| testlotto 1232 | 12,15,19,22,24,36 +3 |
| testlotto 1233 | 2,7,20,25,37,40 +29 |
| testlotto 1234 | 1,15,19,31,35,43 +27 |
| hyodo | 1231 (OPEN 잔여) |
| K-08 | OPEN · `3ec4794` 신설 (지표 best vs mean) |
| K-09 | CLOSED · `5bf9839` OPEN → `2837d2e` CLOSED |
| Y 1.033 | EV 순배율(컷오프 Y풀·창200·위약보정) CI[1.019,1.048] |

---

## 3) 동결·플래그

- `random.choices` · `_get_draws_before` · boost  
- `ROK21_EV_RERANK` / `ROK21_LEARN_CUTOFF` 기본 OFF  

---

## 4) 다음

1. hyodo 1232~1234 (형 승인)  
2. 정찰 관찰목록 → K-A~  
3. (선택) EV/CUTOFF opt-in  

---

## 5) 산출물

`reports/20260727_ROK21_SSOT확정_인코딩수정.md`  
`My_Drive_Sync/커서보고서/` 동일 복사
