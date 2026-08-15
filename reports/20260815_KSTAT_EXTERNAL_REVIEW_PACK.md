# K-STAT-EXTERNAL-REVIEW-PACK — 외부 에이전트 검토용

시각: 2026-08-15 · **DOC_OK** · 범위=**과거학습(stat)만** · 코드 APPLY 없음 · 1237아님

형: 이 파일 전체를 외부 AI 채팅에 붙여넣으면 된다.  
GitHub 404면 아래 **반드시 읽기** 파일을 순서대로 더 붙여넣기.

---

## 0) 30초 프레임 (추측 금지)

| 항목 | 값 |
|------|-----|
| SSOT | GitHub `kkr2652199-prog/ROK21` · main · 로컬 `D:\ROK21` · 포트 **7021** |
| 원본 kweon | `D:\3kweon` · `264de3c` · **쓰기·push·신규작업 금지** |
| 단계 | **양산前 테스트**. 마지막 확정 회차 **1236**. **1237은 예측/양산 아님** |
| 뇌 | 지금 작업=**과거학습(stat)만**. markov/review 숙제 코드는 보존·라이브 소비 OFF |
| 공유 허용 | `lotto_draws`(과거 당첨)만. 뇌 과정·hint·몰아주기 공유 금지 |
| 성적 | 1·2·3등 / 적중 mean으로 ‘좋아졌다’ **금지**. 이론 1장 E[hits]=**0.80** (K-O) |
| 게이트 | prefer/prize **비악화** (Δ < 0.005, 음수 OK) |
| 동결 | `random.choices` · `_get_draws_before` · boost 상한(carry 0.2 / ending 0.3 / overdue 0.2) |
| 수치 SSOT | `docs/benchmarks/*.json` · BOOT/STATUS는 사본 |
| 결함 SSOT | `My_Drive_Sync/SUMMARY/FINDINGS.md` |
| 다음 1건 | `K-AWAIT-HYUNG-NEXT` — 형 1건. #4는 새 아이디어 있을 때만 |

검토 목표: **패치가 설계대로 도는지 / 금지선을 넘었는지 / 빈칸이 있는지.**  
목표 아님: 3등P↑ 새 엔진, 1237 발권, 3뇌 동시튜닝, 동결 해제.

---

## 1) 지금 상태 (한 줄)

과거학습 **10세트+몰아주기** 리스트(S1~S5) 튜닝은 끝(S2는 HOLD).  
그 다음 정리 리스트 **#1 원장맞춤 · #2 프로세스감사 · #3 K-A 구표본** 도 끝.  
엔진이 완벽하다는 뜻이 아니다. 라이브는 stat만 숙제를 읽고, 원장은 **stat 3000**.

### 라이브 플래그 (코드에 켜진 것)

| 플래그 | 값 | 단계 |
|--------|-----|------|
| `ROLE_TIER_LEARN_BRAINS` | `{stat}` | 형 정정 후 |
| `COVER_SELECT_MODE` | `outside_union` | S1 APPLY |
| `SHAPE_CORE_MODE` | `set1` | S2 HOLD (합의코어 꺼짐) |
| `REPACK_ROLE_QUOTA_WIRE` | `True` | S3 APPLY |
| `REPACK_RECOMBINE_MODE` | `complement` | S4 APPLY |
| `COVER_MIN_HITS` | `3` | 표 빔 패치 |
| `STAT_POOL_LEARN_WIRE` | `True` | 배선 ON · 노브 HOLD |

### 최근 HARD 실측 (모니터 · 클레임 금지)

- 원장맞춤 200회: peek 0 · ledger **stat 3000** · 다른 뇌 0 · pred_1237 0 · draws MAX 1236
- 프로세스감사: 역할 5+3+2 일치 · S1 source `cover_r3_outside_union` **600/600** · S3 쿼터실패 0 · S4 Jaccard **0** · 라이브↔캐시 번호 불일치 0
- 3등 SPEC: 6~8은 3등 학습기 **아님**. 3등 형태는 9~10(5+1). 학습 부품 기각
- K-A 0.760 = **구표본 HOLD**. mean으로 패치/서열 금지

근거 JSON: `docs/benchmarks/20260815_KSTAT_LEDGER_REALIGN_BT200.json` · `20260815_KSTAT_PROCESS_AUDIT_S5LIVE.json` · `20260815_KSTAT_TIER3_ENGINE_SPEC.json` · `20260815_KA_STALE_DOC.json`

---

## 2) 진행 과정 (시간순 · 과거학습 캠페인)

채팅 기억이 아니라 **아래 보고서+JSON**이 원본이다.

```text
역할슬롯 도입 (LIST_V3)
  1~5 skill_native · 6~8 cover_r3 · 9~10 shape_r2 · 몰아주기 focus_r1
  등수P↑ 엔진이 아님 (포트폴리오 역할)

S0  SPEC  6~8=재샘플이지 3등학습기 아님 · 9~10=1번세트 1칸변형
S1  APPLY 덮기 = skill union 밖 번호 최대 (outside_union)
S2  HOLD  합의코어 — prefer Δ +0.012169 ≥ 0.005 인기↑ → 라이브 set1 유지
S3  APPLY 몰아주기 복사4: skill≥1 · cover≥1 · shape≤1
S4  APPLY 5번째 장 = 복사4에 없는 고점수 6개 (complement)
S5  PASS  리셋+stat 1037~1236 n200

(옆길) markov/review 숙제 WIRE+markov 200 — 형 정정: 지금은 과거학습만
        → 소비를 {stat}로 되돌림. markov 원장이 남아 갭 발생

#1  PASS  리셋 후 stat만 200 · 원장 stat3000 (갭 해소)
#2  PASS  S5라이브 프로세스 감사 (라벨·역할·n_pos)
3등  SPEC  3등 학습 부품 기각 · 휠은 S1과 반대기하
#3  DOC   FINDINGS K-A 0.760 = 구표본 HOLD
```

S1~S4 게이트(prefer/prize Δ, 설계 모니터)는  
`reports/20260815_KSTAT_FINAL_REVIEW_NEXT.md` §3 표.

---

## 3) 읽기 순서

### A. 반드시 (외부AI 진입 · 5분)

권한 있으면 레포에서 연다. 없으면 형이 **이 순서대로 붙여넣기**.

1. `EXTERNAL_START.md` (루트) — 지금 HEAD·NEXT 1건
2. **이 파일** `reports/20260815_KSTAT_EXTERNAL_REVIEW_PACK.md`
3. `reports/20260815_KSTAT_FINAL_REVIEW_NEXT.md` — 리스트 종료점검
4. `reports/20260814_KSTAT_ENGINE_EVOLVE_SPEC.md` — 엔진이 실제로 하는 일 (S0)

보조 1장: `My_Drive_Sync/SUMMARY/FLOW_BRIEF.md`

### B. 패치 본문 (단계마다 보고서 + JSON 같이)

숫자는 **JSON이 원본**. md는 설명.

| 단계 | 보고서 | 수치 JSON |
|------|--------|-----------|
| S1 | `reports/20260814_KSTAT_COVER_OUTSIDE_UNION.md` | `docs/benchmarks/20260814_KSTAT_COVER_OUTSIDE_UNION.json` |
| S2 | `reports/20260814_KSTAT_SHAPE_CONSENSUS_CORE.md` | `docs/benchmarks/20260814_KSTAT_SHAPE_CONSENSUS_CORE.json` |
| S3 | `reports/20260814_KSTAT_REPACK_ROLE_QUOTA.md` | `docs/benchmarks/20260814_KSTAT_REPACK_ROLE_QUOTA.json` |
| S4 | `reports/20260814_KSTAT_REPACK_MIX_RECOMBINE.md` | `docs/benchmarks/20260814_KSTAT_REPACK_MIX_RECOMBINE.json` |
| S5 | `reports/20260814_KSTAT_ENGINE_EVOLVE_BT200.md` | `docs/benchmarks/20260814_KSTAT_ENGINE_EVOLVE_BT200.json` |
| 소비정정 | `reports/20260815_KSTAT_ONLY_CONSUME_RESTORE.md` | `docs/benchmarks/20260815_KSTAT_ONLY_CONSUME_RESTORE.json` |
| #1 원장 | `reports/20260815_KSTAT_LEDGER_REALIGN_BT200.md` | `docs/benchmarks/20260815_KSTAT_LEDGER_REALIGN_BT200.json` |
| 3등분석 | `reports/20260815_KSTAT_TIER3_ENGINE_SPEC.md` | `docs/benchmarks/20260815_KSTAT_TIER3_ENGINE_SPEC.json` |
| #2 감사 | `reports/20260815_KSTAT_PROCESS_AUDIT_S5LIVE.md` | `docs/benchmarks/20260815_KSTAT_PROCESS_AUDIT_S5LIVE.json` |
| #3 K-A | `reports/20260815_KA_STALE_DOC.md` | `docs/benchmarks/20260815_KA_STALE_DOC.json` |

Drive 복사본(같은 내용): `My_Drive_Sync/커서보고서/` 아래 동명 md.

### C. 코드 (권한 있을 때 · 라이브 확인)

| 파일 | 볼 것 |
|------|--------|
| `app/testlotto/role_slots.py` | `COVER_SELECT_MODE` · `SHAPE_CORE_MODE` · `build_cover_r3_sets` · `build_shape_r2_sets` |
| `app/testlotto/signal_pool.py` | `ROLE_TIER_LEARN_BRAINS={stat}` · 쿼터 · `complement` · `assemble_signal_union` |
| `app/testlotto/role_homework.py` | `COVER_MIN_HITS=3` · as_of < target |
| `app/testlotto/stat_pool_learn.py` | `STAT_POOL_LEARN_WIRE` (노브 HOLD) |
| `My_Drive_Sync/SUMMARY/FINDINGS.md` | **K-A HOLD** · **K-O** · **K-P** · **K-E 동결** |

### D. 있으면 좋은 배경 (시간 날 때)

- `reports/20260812_KTIER_ROLE_SLOTS_ANALYSIS.md` — 왜 3등/2등 **슬롯 이름**이 엔진이 아닌지
- `reports/20260812_KNEXT_LIST_V3.md` — 역할슬롯 리스트 원안
- `My_Drive_Sync/SUMMARY/RESTORE.md` 섹션 B — 턴 로그 12행
- `My_Drive_Sync/SUMMARY/STATUS_LATEST.md` — 상태 표 (사본·압축하지 말 것)
- `My_Drive_Sync/SUMMARY/WARRANT.md` — 명분 라벨
- `My_Drive_Sync/SUMMARY/BENCH_PROTOCOL.md` — 성적 쓰는 법

### E. 지금 읽지 말 것

- `D:\3kweon` · memoy · 1~3군
- `data/*.db` 를 커밋/첨부 (public 레포)
- 유튜브/LSTM/WIN_1Y/HINT 0.15/ASSOC/S2 consensus 재탕 제안으로 바로 APPLY
- 채팅 압축본만 믿고 JSON을 안 여는 것

---

## 4) 검토 질문 (외부AI가 답하면 됨)

1. S1~S4가 **코드 플래그**와 **감사 JSON**과 같은가. 꺼진 S2를 켜라고 하면 안 되는 이유(prefer)를 파일에서 짚었는가.
2. 6~8을 3등 학습기로 오해한 문장이 남아 있는가. 3등 SPEC과 충돌하는가.
3. 0.760 / 0.83 / 4등12 / 5등55 를 성적 향상으로 쓴 문서가 있는가 (있으면 지적).
4. 원장 갭(한때 markov 3000)이 **지금** 해소됐는지 JSON census로 확인했는가.
5. 빈칸: 캐시가 pool `source`를 버리는 것, 보완 1장 라벨이 `score_repack`인 것, UI `backtest_runs=0` — 버그인지 SOFT인지 보고서에 맞게 읽었는가.
6. 다음에 **하지 말아야 할 것**과 **형 GO가 필요한 것**을 한 줄로.

답은 파일 인용. 없으면 **미확인**. 새 knob·패치 지시서는 형 승인 전 쓰지 말 것.

---

## 5) 금지 (검토자도 동일)

- 1237 예측/양산
- 원본 kweon 쓰기
- 동결 3종 수정
- ge3/등수/mean 서열로 APPLY
- 3뇌 합동 튜닝을 지금 시작
- DB 파일 커밋

---

## 6) 붙여넣기 최소 세트 (404일 때 형용)

1. `EXTERNAL_START.md`
2. 이 팩
3. `reports/20260815_KSTAT_FINAL_REVIEW_NEXT.md`
4. `reports/20260814_KSTAT_ENGINE_EVOLVE_SPEC.md`
5. (시간 되면) `#1` `#2` `3등SPEC` `#3` 보고서 4개

큐: **이 팩을 읽고 검토 질문 6개만 답해. 코드 APPLY 하지 마. 1237 아님.**
