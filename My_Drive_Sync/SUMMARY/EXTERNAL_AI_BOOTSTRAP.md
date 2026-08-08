# EXTERNAL_AI_BOOTSTRAP — 외부AI용 (GitHub 못 열 때)

> 형 → 외부AI 채팅에 **`EXTERNAL_START.md`(레포 루트) 전체** 또는 아래 LIVE 블록을 붙여넣는다.  
> 404 원인: 레포 비공개/토큰 없음. **경로 오류 아님.**

<!-- ROK21_LIVE_FLOW -->
## LIVE 작업 흐름 (자동 동기 · 외부AI 1순위)

| 키 | 값 |
|----|-----|
| HEAD(실측) | `9a0a323` |
| BASELINE_PIN | `640cb67` |
| WORK | `IDLE` |
| 지금 | **K-SEED-AVERAGE-DESIGN**(n300·outer10×안쪽8) — **NOISE_CUT_NOT_ESTABLISHED**: R8 까지 올려도 σ 비 **1.38배**(√R 예측 2.83배 미달 · 기울기 −0.13) · R39 구분불가(필요 outer 41~55) · **손익이 결정타**: 해상도 이득 1.156배/비용 8배 · seed 잡음 0 이어도 상한 1.4647배 · **등가회차 역산 시 평균화 과지불 5.99배** → **배선 안 함** · ge3 Δ+0.011 게이트 UNDECIDABLE |
| 직전 | SEED-NOISE-FLOOR v2(FLOOR_NOT_ESTABLISHED · 바닥 0.005087 CI 0포함) · R39 신설(`tools/k_precision.py` 7/7) |
| BOOT다음 | ①학습기 경로 잡음(평균 안 되는 A몫) 진단 ②1236+ 전향적 EV로그 ③트랙정지 중 **형 1건 선택** · 발권가중 금지 |
| NEXT1 ID | **K-SEED-AVG-NEXT-PICK** |
| NEXT1 할일 | seed 평균화 설계·검증 완료 — **결론: NOISE_CUT_NOT_ESTABLISHED · 배선 안 함**. R8 까지 올려도 잔여 잡음이 √R(2.83배)로 안 줄고 **1.38배**에 그침(기울기 −0.13) · R39 구분불가(필요 outer 41~55). 결정타는 손익 — 이항SE 0.018322 는 못 줄이므로 **seed 잡음을 0으로 만들어도 판정 해상도 상한 1.4647배**, R8 실측 1.156배에 비용 8배. 같은 해상도를 **회차 늘리기로 사면 5.99배 싸다**(등가 n=400.9 vs 반복비용 2400). ge3 는 Δ+0.011 로 게이트 UNDECIDABLE = 무변화. 분해 σ²=A+B/R 에서 stat 은 63%만 제거 가능하고 나머지 A 는 **평균되지 않는 학습기 경로**. 형 확인 후 1건 선택 — **①학습기 경로 잡음 진단**(권장 · 평균화가 못 건드린 A 몫의 정체 확인 · 이걸 줄여야 판정 해상도가 오름 · 측정만 · 발권 무변경) / ②회차 1236+ 전향적 EV 로그 시작(개입 없이 인기회피축 검증) / ③트랙정지 |
| 승인필요 | 없음 (①②는 측정·기록만 · 발권경로 무변경) |
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
1. 첫줄 `[복귀] HEAD=9a0a323 · 지금=**K-SEED-AVERAGE-DESIGN**(n300·outer10×안쪽8) — **NOISE_CUT_NOT_ESTABLISHED**: R8 까지 올려도 σ 비 **1.38배**(√R 예측 2.83배 미달 · 기울기 −0.13) · R39 구분불가(필요 outer 41~55) · **손익이 결정타**: 해상도 이득 1.156배/비용 8배 · seed 잡음 0 이어도 상한 1.4647배 · **등가회차 역산 시 평균화 과지불 5.99배** → **배선 안 함** · ge3 Δ+0.011 게이트 UNDECIDABLE · 다음=K-SEED-AVG-NEXT-PICK`
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
