# EXTERNAL_AI_BOOTSTRAP — 외부AI용 (GitHub 못 열 때)

> 형 → 외부AI 채팅에 **`EXTERNAL_START.md`(레포 루트) 전체** 또는 아래 LIVE 블록을 붙여넣는다.  
> 404 원인: 레포 비공개/토큰 없음. **경로 오류 아님.**

<!-- ROK21_LIVE_FLOW -->
## LIVE 작업 흐름 (자동 동기 · 외부AI 1순위)

| 키 | 값 |
|----|-----|
| HEAD(실측) | `0fe62b1` |
| BASELINE_PIN | `640cb67` |
| WORK | `IDLE` |
| 지금 | **K-STAT-SEED-NOISE-FLOOR** — n1183·seed10 전구간 · stat ge3 폭 **0.035503** · 분산적합 `a²/n+b²` → **바닥 b=0.010127**(R²0.9985) · **FULL-WF Δ+0.0047 < 바닥 → 표본 늘려도 판정 불가** |
| 직전 | R38 게이트 강제 가동(k_gate 공용모듈 · COMPLIANT) · DECISION-GATE(win26/mix0.8=NOISE_SELECTION_CONFIRMED · 순서불변 2.429e-17) |
| BOOT다음 | ①1236+ 전향적 EV로그 ②stat 잡음저감(팽창1.27 · markov 0.73 대비 최악) ③legacy 판정 게이트 소급적용 중 **형 1건 선택** · 발권가중 금지 |
| NEXT1 ID | **K-NOISE-FLOOR-NEXT-PICK** |
| NEXT1 할일 | 잡음 하한 확정 완료(**바닥 b=0.010127** · FULL-WF Δ+0.0047 이 바닥 미만 → 적중축은 표본을 늘려도 판정 불가로 확정) 형 확인 후 1건 선택 — **①회차 1236+ 전향적 EV 로그 시작**(권장 · 적중축이 닫혔으므로 유일하게 남은 인기회피축을 개입 없이 검증) / ②stat 잡음 저감 진단(팽창 stat 1.2739 vs markov 0.7329 — 왜 stat만 잡음을 더하는지 원인 특정) / ③legacy 132건 중 상수·배선에 실제 영향 준 판정만 게이트 소급적용 / ④트랙정지 |
| 승인필요 | 없음 (①~③ 모두 측정·기록만 · 발권경로 무변경) |
| 선행 | 없음 |
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
1. 첫줄 `[복귀] HEAD=0fe62b1 · 지금=**K-STAT-SEED-NOISE-FLOOR** — n1183·seed10 전구간 · stat ge3 폭 **0.035503** · 분산적합 `a²/n+b²` → **바닥 b=0.010127**(R²0.9985) · **FULL-WF Δ+0.0047 < 바닥 → 표본 늘려도 판정 불가** · 다음=K-NOISE-FLOOR-NEXT-PICK`
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
| **젠스파크 압축** | `GENSPARK_COMPRESS_RECOVER.md` + EXTERNAL_START 붙여넣기 · JSON 재페치 |
| 매턴 갱신 | 커서 종료루틴 `sync_all_resume_docs()` (R37 · genspark_recover 포함) |

커서에게 **"EXTERNAL_START 최신화"** 라고 하면 HEAD/NEXT 다시 박음.

---

## GitHub 열 수 있을 때

날짜 무관 합류 = `My_Drive_Sync/SUMMARY/EXTERNAL_AI_JOIN_PROMPT.md`  
형의 짧은 큐:

```
동생, JOIN_PROMPT대로 EXTERNAL_START→FLOW→NEXT→BOOT→RESTORE 읽고 [복귀] 후 다음1건만.
```
