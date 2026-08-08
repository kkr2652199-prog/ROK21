# EXTERNAL_AI_BOOTSTRAP — 외부AI용 (GitHub 못 열 때)

> 형 → 외부AI 채팅에 **`EXTERNAL_START.md`(레포 루트) 전체** 또는 아래 LIVE 블록을 붙여넣는다.  
> 404 원인: 레포 비공개/토큰 없음. **경로 오류 아님.**

<!-- ROK21_LIVE_FLOW -->
## LIVE 작업 흐름 (자동 동기 · 외부AI 1순위)

| 키 | 값 |
|----|-----|
| HEAD(실측) | `d338ac7` |
| BASELINE_PIN | `640cb67` |
| WORK | `IDLE` |
| 지금 | **K-REPACK-SIGNAL-WIRE**(형GO · 배선수정) — **WIRE_CONFORMS 7/7**. 몰아주기가 설계와 어긋난 3건 수정: ①3뇌가 `pos/num EMA` **한 장 공유**(`for _tag` 로 태그 버림) → **뇌별 분리** + `brain_signal()` 해석기 ②`for sn in (4,5)` **하드코딩** → `signal_top_set_nos()` 로 **위치 EMA 상위 2세트**(실측 4·5 이탈률 markov 1.000/review 1.000/stat 0.900) ③markov 만 pool 슬롯 0개 → **3뇌 동일**. 검증 1216~1235: C1 뇌별분리·C2 신호상위·C2b 4·5이탈·C3 3뇌동일·C4 세트통째보존·C5 결정성·C6 미래참조없음. **성적 주장 아님 → R38 게이트 대상 아님** · 발권경로(`coordinator`) 무변경 · 보존 슬롯수 2는 구 4·5 와 동수 유지(장수는 튜닝이라 범위 외) |
| 직전 | K-REPACK-SELECT-DIAG(POOL_EQUALS_RANDOM · pool 10세트=무작위10장 · 「좋은세트 놓침」 전제 오독 확인) · K-SEED-AVERAGE-DESIGN(배선안함) |
| BOOT다음 | **선생님 먼저** — ①과거학습 뇌(stat) 예측 튜닝 ②당첨금(인기회피) 축 ③1236+ 전향적 EV로그 중 **형 1건 선택** · 발권가중 금지 |
| NEXT1 ID | **K-SIGNAL-WIRE-NEXT-PICK** |
| NEXT1 할일 | 형 지시 「몰아주기 정상작동 패치」 **완료 · WIRE_CONFORMS 7/7**. 형 지적(「백테스트 성적으로 몰아주기를 판정하지 말라 · 선생님이 잘 가르쳐야 학생 성적이 오른다」)이 정확했고, 코드를 다시 읽어 **설계와 어긋난 배선 3건**을 찾아 고쳤다 — ①`update_from_pool` 이 `for _tag` 로 뇌를 버려 3뇌가 성적표 한 장을 공유(stat 3번 세트 성적에 markov·review 3번 성적이 겹침 = 뇌를 개선해도 전달 불가) → 뇌별 분리 + `brain_signal()` ②`assemble_hybrid_p45_r123` 의 `for sn in (4, 5)` 하드코딩(신호 0 인 세트도 항상 발권·신호 최고 세트는 버림) → `assemble_signal_top()` 위치 EMA 상위 2세트 · **실측 4·5 이탈률 markov 1.000 / review 1.000 / stat 0.900** = 신호가 4·5 를 가리키는 건 20회 중 2회뿐이었다 ③markov 만 pool 슬롯 0개 → 3뇌 동일. **이 수정은 성적 주장이 아니라 설계일치이므로 R38 게이트 대상이 아니다**(코드 판독으로 확정). 보존 슬롯수 2는 구 4·5 와 동수 유지 — 「몇 장 보존할지」는 성적 주장이 필요하므로 범위 제외. 이제 **통로가 뚫렸으므로 선생님 차례**. 형 확인 후 1건 선택 — **①과거학습 뇌(stat) 예측 튜닝**(권장 · 형이 말한 「과거 회차를 분석해서 번호를 예측하는 뇌 튜닝」 · 뇌가 좋아지면 이제 그 신호가 몰아주기까지 실제로 전달된다) / ②당첨금(인기회피) 축 설계(저번호·저합 sum β−0.0575) / ③1236+ 전향적 EV 로그 시작 / ④트랙정지 |
| 승인필요 | 없음 (발권경로 `coordinator` 무변경 · 동결항목 무접촉) |
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
1. 첫줄 `[복귀] HEAD=d338ac7 · 지금=**K-REPACK-SIGNAL-WIRE**(형GO · 배선수정) — **WIRE_CONFORMS 7/7**. 몰아주기가 설계와 어긋난 3건 수정: ①3뇌가 `pos/num EMA` **한 장 공유**(`for _tag` 로 태그 버림) → **뇌별 분리** + `brain_signal()` 해석기 ②`for sn in (4,5)` **하드코딩** → `signal_top_set_nos()` 로 **위치 EMA 상위 2세트**(실측 4·5 이탈률 markov 1.000/review 1.000/stat 0.900) ③markov 만 pool 슬롯 0개 → **3뇌 동일**. 검증 1216~1235: C1 뇌별분리·C2 신호상위·C2b 4·5이탈·C3 3뇌동일·C4 세트통째보존·C5 결정성·C6 미래참조없음. **성적 주장 아님 → R38 게이트 대상 아님** · 발권경로(`coordinator`) 무변경 · 보존 슬롯수 2는 구 4·5 와 동수 유지(장수는 튜닝이라 범위 외) · 다음=K-SIGNAL-WIRE-NEXT-PICK`
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
