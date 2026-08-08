# EXTERNAL_AI_BOOTSTRAP — 외부AI용 (GitHub 못 열 때)

> 형 → 외부AI 채팅에 **`EXTERNAL_START.md`(레포 루트) 전체** 또는 아래 LIVE 블록을 붙여넣는다.  
> 404 원인: 레포 비공개/토큰 없음. **경로 오류 아님.**

<!-- ROK21_LIVE_FLOW -->
## LIVE 작업 흐름 (자동 동기 · 외부AI 1순위)

| 키 | 값 |
|----|-----|
| HEAD(실측) | `5c93cda` |
| BASELINE_PIN | `640cb67` |
| WORK | `IDLE` |
| 지금 | **K-STAT-NOISE-SOURCE**(n400·seed24) — 잡음 유입점 **'뽑기' 단계로 확정**(점수·repack 결정적) · 그러나 **PREMISE_NOT_ESTABLISHED**: 뇌별 팽창차(stat1.2739/markov0.7329)가 seed10 오차 안(구분가능쌍 **0/3**) · 뇌수준 std 도 stat0.016040/markov0.015184/review0.013584 **동일** → stat 전용 대책 근거 없음 |
| 직전 | K-STAT-SEED-NOISE-FLOOR(바닥 b=0.010127 · FULL-WF Δ+0.0047 < 바닥 → 적중축 판정불가 확정) · R38 게이트 가동(k_gate · COMPLIANT) |
| BOOT다음 | ①잡음바닥 seed16+ 재측정(권장 · 바닥 자체 오차 미상) ②1236+ 전향적 EV로그 ③seed 평균화 설계(형 GO 필요) 중 **형 1건 선택** · 발권가중 금지 |
| NEXT1 ID | **K-NOISE-SOURCE-NEXT-PICK** |
| NEXT1 할일 | stat 잡음 원인 진단 완료 — **결론: 질문의 전제가 무너짐(PREMISE_NOT_ESTABLISHED)**. 뇌별 팽창차(stat 1.2739 / markov 0.7329)는 seed10 측정오차 안이라 구분가능쌍 **0/3**. 잡음 유입점은 **'뽑기' 단계로 확정**(점수·repack 모두 결정적). 형 확인 후 1건 선택 — **①잡음바닥 seed 16+ 재측정**(권장 · 현 바닥 b=0.010127 이 seed10 기반이라 바닥 자체의 오차가 미상 · 이 값이 앞으로 모든 판정 임계를 정함 · stat↔markov 구분에 seed 16이면 충분) / ②회차 1236+ 전향적 EV 로그 시작 / ③seed 평균화 설계(같은 회차 반복 뽑기→번호 득표 · random.choices 무수정 · 발권경로 변경이라 형 GO 필요) / ④트랙정지 |
| 승인필요 | 없음 (①②는 측정·기록만 · 발권경로 무변경) / ③은 형 GO 필수 |
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
1. 첫줄 `[복귀] HEAD=5c93cda · 지금=**K-STAT-NOISE-SOURCE**(n400·seed24) — 잡음 유입점 **'뽑기' 단계로 확정**(점수·repack 결정적) · 그러나 **PREMISE_NOT_ESTABLISHED**: 뇌별 팽창차(stat1.2739/markov0.7329)가 seed10 오차 안(구분가능쌍 **0/3**) · 뇌수준 std 도 stat0.016040/markov0.015184/review0.013584 **동일** → stat 전용 대책 근거 없음 · 다음=K-NOISE-SOURCE-NEXT-PICK`
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
