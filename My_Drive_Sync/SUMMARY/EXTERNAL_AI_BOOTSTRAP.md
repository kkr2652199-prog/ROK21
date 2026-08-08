# EXTERNAL_AI_BOOTSTRAP — 외부AI용 (GitHub 못 열 때)

> 형 → 외부AI 채팅에 **`EXTERNAL_START.md`(레포 루트) 전체** 또는 아래 LIVE 블록을 붙여넣는다.  
> 404 원인: 레포 비공개/토큰 없음. **경로 오류 아님.**

<!-- ROK21_LIVE_FLOW -->
## LIVE 작업 흐름 (자동 동기 · 외부AI 1순위)

| 키 | 값 |
|----|-----|
| HEAD(실측) | `69b9c7d` |
| BASELINE_PIN | `640cb67` |
| WORK | `IDLE` |
| 지금 | **K-BRAIN-INDEPENDENCE-AUDIT**(형GO · 버그사냥) — **INDEPENDENCE_OK 14/14**. 형 지시 「한번 더 버그를 찾아보자」로 **2건 추가 발견·수정** — ⑥`repack_by_brain` 이 `number_scores` 에 **`brain_tag` 미전달** → 뇌별 가중치 dict 가 **한 번도 조회 안 되는 죽은 배선**(첫 hint 절제가 `+0.0000` 이던 게 증상) ⑦hint 축 개방 직후 **또 죽은 배선 검출** → 호출자 누락에도 `repack_by_brain` 이 직접 만들게 수정 · **죽은배선 탐지 B6 신설**(dict 바꿔서 결과 안 바뀌면 실패) · **실측**: 3뇌 점수세트 번호겹침 Jaccard **0.664~0.687**(공유 14.2~14.5개) vs 무작위 기대 **0.250** = 약 2.7배 · hint 0 으로 두면 **0.743→0.30** → **공유 hint 가 주원인** · 10세트 완전성·pass0≠pass1·뇌간 동일세트 0건 통과 · hint 개방은 성적 무변화 실증 |
| 직전 | **K-BRAIN-RNG-INDEPENDENT + K-PREDICT-RESET**(형GO) — **WIRE_CONFORMS 9/9**(1216~1235 · 리셋 후 재검증). ④`expand_pool` 이 3뇌를 **한 난수 흐름**으로 돌려 stat 이 markov 를 오염(발권경로는 이미 뇌별 시드리셋인데 pool 경로만 누락) → **뇌마다 `random.seed` 리셋** ⑤pass0 시드를 `seed+draw_no` 로 맞춰 **pool 1~5 = 실제 발권 5세트**(C8 신설) · 뇌별 상수 dict 개방(`POOL_SLOTS/SCORE_WEIGHTS/LEARN_EMA_BY_BRAIN` · **값 전부 동일=성적 무변화**) · **미해결 명시: hint 는 3뇌 공유**(`W_HINT=0.40` · 뇌별 hint 는 성적 주장이라 범위 밖) · DB 3뇌 예측 **7,094행 삭제**(원천 보존 · rare_hits·transition_log 는 회차파생이라 보존) |
| BOOT다음 | **선생님 차례** — 형 예정대로 **①과거학습 뇌(stat) 예측 튜닝**(권장) / ②뇌별 hint spec 값 차별화(배선 완료·값만 게이트 필요 · 겹침 2.7배의 주원인) / ③1236+ 자동시스템 배선 중 **형 1건 선택** · 발권가중 금지 |
| NEXT1 ID | **K-STAT-TUNE-START-PICK** |
| NEXT1 할일 | 형 지시 「한번 더 버그를 찾아보자 · 없으면 과거학습 뇌부터 튜닝」 → **버그 2건 발견·수정 후 14/14** 이므로 **이제 튜닝 착수 가능**. ⑹ **`brain_tag` 죽은 배선**: `repack_by_brain` 이 `number_scores` 에 `brain_tag` 를 안 넘겨 **뇌별 가중치 dict 가 한 번도 조회되지 않았다**. 처음 hint 절제가 `+0.0000` 으로 나온 게 이 버그의 증상(절제가 물리적으로 불가능했다) → `brain_tag=tag` 추가. 다른 5개 호출부는 전부 넘기고 있었고 발권 분석 경로 하나만 누락 · ⑺ **죽은배선 탐지 B6 신설** 후 hint 축을 열자 **즉시 또 검출** → `repack_by_brain` 이 spec 갈릴 때 직접 만들게 수정 · **실측(형이 걱정한 「예측번호 공유」의 크기)**: 3뇌 점수세트 번호겹침 Jaccard **0.664~0.687**(공유 14.2~14.5개) vs 무작위 기대 **0.250** = 약 **2.7배**, hint 가중치 0 으로 두면 **0.743 → 0.30** → **공유 hint 가 주원인 확정** · 점수세트 번호의 자기 pool 출신 비율 **0.79~0.82**(약 20% 가 pool 밖 유입) · **깨지지 않은 것**: 10세트 정확·set_no 1~10·번호형식·**pass0≠pass1**(「10세트가 실은 5세트」 의심은 사실 아님 · 3뇌 전부 난수 사용)·뇌간 동일세트 0건·pool 슬롯 2자리·RNG 독립·학습 교차오염 없음. 형 1건 선택 — **①과거학습 뇌(stat) 예측 튜닝 착수**(권장 · 형 예정대로 · **착수 전 백테스트 재생성 필수** — DB 리셋으로 learn_state·feedback 이 비어 피드백·boost 경로가 현재 무효) / ②뇌별 hint spec 값 차별화(배선·탐지기 완료 · **값 결정만 R38 게이트 필요** · 겹침 2.7배의 주원인이라 효과 큼) / ③1236+ 회차별 자동시스템 배선(형이 「이후 패치」로 미뤄둔 건) / ④트랙정지 |
| 승인필요 | 없음 (발권경로 `coordinator` 무변경 · 동결항목 무접촉 · DB 커밋 안 함) |
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
1. 첫줄 `[복귀] HEAD=69b9c7d · 지금=**K-BRAIN-INDEPENDENCE-AUDIT**(형GO · 버그사냥) — **INDEPENDENCE_OK 14/14**. 형 지시 「한번 더 버그를 찾아보자」로 **2건 추가 발견·수정** — ⑥`repack_by_brain` 이 `number_scores` 에 **`brain_tag` 미전달** → 뇌별 가중치 dict 가 **한 번도 조회 안 되는 죽은 배선**(첫 hint 절제가 `+0.0000` 이던 게 증상) ⑦hint 축 개방 직후 **또 죽은 배선 검출** → 호출자 누락에도 `repack_by_brain` 이 직접 만들게 수정 · **죽은배선 탐지 B6 신설**(dict 바꿔서 결과 안 바뀌면 실패) · **실측**: 3뇌 점수세트 번호겹침 Jaccard **0.664~0.687**(공유 14.2~14.5개) vs 무작위 기대 **0.250** = 약 2.7배 · hint 0 으로 두면 **0.743→0.30** → **공유 hint 가 주원인** · 10세트 완전성·pass0≠pass1·뇌간 동일세트 0건 통과 · hint 개방은 성적 무변화 실증 · 다음=K-STAT-TUNE-START-PICK`
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
