# EXTERNAL_AI_BOOTSTRAP — 외부AI용 (GitHub 못 열 때)

> 형 → 외부AI 채팅에 **`EXTERNAL_START.md`(레포 루트) 전체** 또는 아래 LIVE 블록을 붙여넣는다.  
> 404 원인: 레포 비공개/토큰 없음. **경로 오류 아님.**

<!-- ROK21_LIVE_FLOW -->
## LIVE 작업 흐름 (자동 동기 · 외부AI 1순위)

| 키 | 값 |
|----|-----|
| HEAD(실측) | `c2c26a6` |
| BASELINE_PIN | `640cb67` |
| WORK | `IDLE` |
| 지금 | NEXT 교체 — **K-REFEREE-WINDOW** (합의) · CONF-CAL ARCHIVE 보류 |
| 직전 | K-ATTACK-BAYES soft≈null · invcorr<RR |
| BOOT다음 | learn_state(+cutoff) 슬라이딩 윈도우 WINDOW=30 |
| NEXT1 ID | **K-REFEREE-WINDOW** |
| NEXT1 할일 | learn_state.py + learn_state_cutoff.py 동시 패치 — recent_avg_match 누적평균 → 슬라이딩 윈도우(WINDOW=30) 교체. K-ATTACK-CONF-CAL 은 그 다음 NEXT로 ARCHIVE에 보류 등록. |
| 승인필요 | 아니오 |
| 선행 | 동생·형 합의 완료 · CONF-CAL 보류 |
| OPEN샘플 | K-00, K-02, K-05 |

### 역할
- 형=결정 · 동생(너)=판단·짧은 지시서 · 커서=실행·commit·push
- 너는 D:\ROK21 / 비공개 GitHub를 못 열 수 있다 → **이 LIVE 블록이 SSOT**
- 404 = 권한 없음(경로 오류 아님). D:\3kweon·memoy·1~3군 미접촉

### 본선 vs 인프라
- 테스트로또 **3예측+4보조 유지** (구조 해체 없음)
- K-AB~AF = 수집/문서/훅(예측력 무관) · 인프라 지시 남발 금지
- 형 방향 = 전제 실증·쓸모 (적중↑ 랜덤앱 아님)

### 네가 할 일
1. 첫줄 `[복귀] HEAD=c2c26a6 · 지금=NEXT 교체 — **K-REFEREE-WINDOW** (합의) · CONF-CAL ARCHIVE 보류 · 다음=K-REFEREE-WINDOW`
2. 승인 없으면 장문 지시서 금지 · 형에게 질문 1개
3. 추가 파일 필요 시: `형, SUMMARY/○○.md 붙여줘`
<!-- /ROK21_LIVE_FLOW -->

---

## 복사용 짧은 큐 (형 → 동생)

```
동생, 아래 EXTERNAL_START / LIVE 블록만 SSOT로 써.
GitHub·D:\ROK21 접근 불가면 fetch 시도하지 말고 붙여넣기만 읽어.
승인 전 장문 지시서 금지. 질문 1개만.
(이 메시지 아래에 LIVE 또는 EXTERNAL_START 본문 첨부)
```

---

## 형용 메모
| 현상 | 해결 |
|------|------|
| GitHub 404 | `EXTERNAL_START.md` 채팅 붙여넣기 |
| 흐름 못 찾음 | 레포 루트 `EXTERNAL_START.md` = 1순위 |
| 매턴 갱신 | 커서 종료루틴 `sync_all_resume_docs()` (R37) |

커서에게 **"EXTERNAL_START 최신화"** 라고 하면 HEAD/NEXT 다시 박음.

---

## GitHub 열 수 있을 때

날짜 무관 합류 = `My_Drive_Sync/SUMMARY/EXTERNAL_AI_JOIN_PROMPT.md`  
형의 짧은 큐:

```
동생, JOIN_PROMPT대로 EXTERNAL_START→FLOW→NEXT→BOOT→RESTORE 읽고 [복귀] 후 다음1건만.
```
