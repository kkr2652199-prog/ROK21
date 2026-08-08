# EXTERNAL_AI_BOOTSTRAP — 외부AI용 (GitHub 못 열 때)

> 형 → 외부AI 채팅에 **`EXTERNAL_START.md`(레포 루트) 전체** 또는 아래 LIVE 블록을 붙여넣는다.  
> 404 원인: 레포 비공개/토큰 없음. **경로 오류 아님.**

<!-- ROK21_LIVE_FLOW -->
## LIVE 작업 흐름 (자동 동기 · 외부AI 1순위)

| 키 | 값 |
|----|-----|
| HEAD(실측) | `3ceb0e8` |
| BASELINE_PIN | `640cb67` |
| WORK | `IDLE` |
| 지금 | **K-STAT-PASTLEARN-READY-CHECK**(READ-ONLY) — 과거학습 뇌가 「회차 숙제」 길로 패치 준비됐는지 점검. **방향·컨닝차단·파이프는 준비됨** · **학습/명분 DB는 리셋으로 비어 튜닝 직전 아님**. 실측: _get_draws_before(1235)→last1234 · cutoff 없으면 learn 로드 차단 · wire ON·v2 ON·ASSOC OFF · reasoning 태그 있음(1yHot) · learn_state/predictions/hit_warrant/evolve=0 |
| 직전 | K-BRAIN-INDEPENDENCE-AUDIT 14/14 · RNG독립·예측DB리셋 |
| BOOT다음 | **형 GO** — ①회차 숙제 백테스트로 기록 채우기(권장·튜닝 전 필수) ②한 회차 명분 샘플 리뷰 ③재료 튜닝(게이트) 중 1건 |
| NEXT1 ID | **K-STAT-HOMEWORK-FILL-PICK** |
| NEXT1 할일 | **K-STAT-PASTLEARN-READY-CHECK 완료** — 형 질문 「확정 길(회차 숙제)로 패치 준비된 뇌인가?」에 대한 실측 답. **방향·컨닝차단·파이프는 준비됨 / 학습·명분 DB는 비어 튜닝 직전 아님.** 실측: `_get_draws_before(1235)`→last=1234 · `set_learn_as_of` 없으면 learn 로드 차단 · `PAST_LEARN_WIRE=ON`·`ENGINE_V2=ON`(past_learn경유)·ASSOC OFF · reasoning에 `1yHot` 태그 존재 · `learn_state/predictions/hit_warrant/evolve_log=0`. **확정 길 잠금**: 예측=N 숙제 · 재료=1..(N-1) · 채점=N 정답 · 깊은 패턴은 재료일 뿐 본선 아님. 형 1건 선택 — **①회차 숙제 백테스트로 기록 채우기**(권장 · 빈 DB로 decay/하드코딩 튜닝 금지) / ②한 회차(예 1235) 명분 샘플을 형이 읽고 부족한 점 지적 / ③재료 튜닝(게이트·성적주장) / ④트랙정지 |
| 승인필요 | 없음 (READ-ONLY 점검 · 발권/동결 무접촉) |
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
1. 첫줄 `[복귀] HEAD=3ceb0e8 · 지금=**K-STAT-PASTLEARN-READY-CHECK**(READ-ONLY) — 과거학습 뇌가 「회차 숙제」 길로 패치 준비됐는지 점검. **방향·컨닝차단·파이프는 준비됨** · **학습/명분 DB는 리셋으로 비어 튜닝 직전 아님**. 실측: _get_draws_before(1235)→last1234 · cutoff 없으면 learn 로드 차단 · wire ON·v2 ON·ASSOC OFF · reasoning 태그 있음(1yHot) · learn_state/predictions/hit_warrant/evolve=0 · 다음=K-STAT-HOMEWORK-FILL-PICK`
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
