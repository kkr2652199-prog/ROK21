# EXTERNAL_AI_BOOTSTRAP — 외부AI용 (GitHub 못 열 때)

> 형 → 외부AI 채팅에 **`EXTERNAL_START.md`(레포 루트) 전체** 또는 아래 LIVE 블록을 붙여넣는다.  
> 404 원인: 레포 비공개/토큰 없음. **경로 오류 아님.**

<!-- ROK21_LIVE_FLOW -->
## LIVE 작업 흐름 (자동 동기 · 외부AI 1순위)

| 키 | 값 |
|----|-----|
| HEAD(실측) | `b5ab7a2` |
| BASELINE_PIN | `640cb67` |
| WORK | `IDLE` |
| 지금 | 핀①~④ 완료 — SCATTER 기회大 · gather v0 회수0 → **V1 튜닝** |
| 직전 | 형 핀 GO · POS sticky≈null |
| BOOT다음 | K-GATHER-V1 — oracle 분해 후 휴리스틱 교체 (WIRE 보류) |
| NEXT1 ID | **K-GATHER-V1** |
| NEXT1 할일 | union6 회차 oracle 분해 → 몰아주기 휴리스틱 교체 → PILOT 재실행 JSON (WIRE 전 성적 게이트) |
| 승인필요 | 아니오 · **K-GATHER-WIRE만 형 GO** |
| 선행 | ①~④ 완료 · SCATTER 기회 확인 · v0 회수 0/21 |
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
1. 첫줄 `[복귀] HEAD=b5ab7a2 · 지금=핀①~④ 완료 — SCATTER 기회大 · gather v0 회수0 → **V1 튜닝** · 다음=K-GATHER-V1`
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
