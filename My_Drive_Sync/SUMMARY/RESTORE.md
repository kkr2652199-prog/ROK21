# RESTORE — ROK21 압축 복원 1순위 (이 파일 하나면 복원 완료)

<!-- ROK21_RESUME_BLOCK -->
## 동생 복귀 5줄 (자동 · guard_boot와 동일 소스)

1. **HEAD:** `2beb17c` · WORK=`IDLE`
2. **지금:** **K-BRAIN-PACKAGE-PHASE3** — review_brain 구현 · 동치 PASS n=200 ge3/mean/nums 100%
3. **다음1건:** K-BRAIN-PACKAGE-PHASE4 — coordinator → stat/markov/review_brain.predict.run 배선 · **동치 n=200** (draw 1035~1234 · ge3·mean·nums 허용오차 0) (승인필요=미확인 · 선행=없음)
4. **SSOT충돌:** 수치=`docs/benchmarks/*.json` · 결함=`FINDINGS.md` · 라벨=`WARRANT.md` 가 원본. BOOT/STATUS/RESTORE는 사본.
5. **금지요약:** 동결토큰·kweon미접촉·컨닝금지·DB전체초기화금지·1~3군기록금지·채팅간략≠문서압축.

> 큐: **동생, EXTERNAL_START.md(또는 RESTORE) 읽고 시작해. GitHub 404면 형이 붙여준 LIVE 블록만 써.**
<!-- /ROK21_RESUME_BLOCK -->


> 새 세션 시작 큐 = **"동생, EXTERNAL_START.md 읽고 시작해."** (GitHub 404면 형이 파일 전체 붙여넣기)  
> **수치 SSOT:** `docs/benchmarks/*.json` · **결함:** `FINDINGS.md` · **명분 라벨:** `WARRANT.md`  
> BOOT/STATUS/RESTORE/RESUME_HERE 는 사본 — 충돌 시 위 원본이 이긴다.  
> 외부AI 진입 1순위(루트): `EXTERNAL_START.md` · 보조: `FLOW_BRIEF.md` · `EXTERNAL_AI_BOOTSTRAP.md`

---

## A) 30초 요약 (5줄)

1. **정체:** ROK21 = 독립 SSOT · `D:\ROK21` · 포트 **7021** · GitHub=`kkr2652199-prog/ROK21`
2. **3자 역할:** 형=결정 / 동생(Claude)=판단·지시서만 / 커서=실행·commit·push
3. **확정 결론:** 적중축 **폐기**. EV 배선 유지(Y풀 순1.033). **K-09 CLOSED**(실질 누수 무해)·전제라벨 제거
4. **물리 상수:** 1장 mean=**0.80** · best-of-15 천장=**2.27** (개선 목표 아님)
5. **현재 초점:** **PINNED_BASELINE** `640cb67` · K-Z~AG 완료분 고정 · 다음 P1~P4.

---

## B) 턴 로그 (최신 ↑ · **최대 12행** · 초과 시 오래된 행 삭제)

| 일시 | 형 지시 요지 | 커서 실행 결과 | 판정 | 커밋 |
|------|--------------|----------------|------|------|
| 2026-08-01 | K-BRAIN-PACKAGE-PHASE3 GO | review_brain engine/learn/aux/predict · 동치 PASS n=200 nums 200/200 · deprecated 1줄 | **PHASE3 PASS** | `2beb17c` |
| 2026-08-01 | K-BRAIN-PACKAGE-PHASE2 GO | markov_brain engine/learn/aux/predict · 동치 PASS n=200 nums 200/200 · deprecated 1줄 | **PHASE2 PASS** | pending |
| 2026-08-01 | K-BRAIN-PACKAGE-PHASE1 GO | stat_brain engine/learn/aux/predict + shared db_facts/diversity · 동치 PASS n=200 nums 200/200 | **PHASE1 PASS** | pending |
| 2026-08-01 | K-BRAIN-PACKAGE-PHASE0 GO | stat/markov/review_brain+shared 스켈레톤 19파일 · 기존 미변경 · ge3벤치 생략 | **PHASE0 OK** | `d9dbdf4` |
| 2026-08-01 | K-BRAIN-PACKAGE-C 설계 | 3뇌 A/B/C · 뇌+전용보조 패키지 · GO조건 | **DOC OK** | pending |
| 2026-08-01 | 세션 논의 정리·push | tier·3+4·pool·뇌패키지·백테·RESUME_HERE · ARCHITECTURE_NOTES | **DOC OK** | pending |
| 2026-08-01 | K-MARKOV-LEARN-SURVEY GO | wired ge3=0.105 p=0.683 · stored old=0.165 · predict 롤백 | **LEARN FAIL** | `91e1cda` |
| 2026-08-01 | K-ARCHITECTURE-REVIEW READ-ONLY | 학습 markov미소비·ending 0.3·referee σ≈0.003 · Jaccard≈0.09 · pin FULL1182 | **REVIEW OK** | pending |
| 2026-08-01 | K-ATTACK-HOLD 문서 마감 | STATUS·TEST_PRIORITY·HEAD sync · coordinator 미배선 확인 · survey HOLD 확정 | **HOLD OK** | pending |
| 2026-08-01 | K-EXCLUDE-SURVEY GO | QUICK n=200 λ sweep · best exclude ge3=0.145=baseline · λ0.25=0.135 · kill≤11% | **EXCLUDE FAIL** | pending |
| 2026-08-01 | 종료체크·SELECT-FULL 마감 | full n=1182 combined ge3=0.1218 FAIL · EXCLUDE-HIST·LEAKAGE · 20260801 세션보고서 | **FULL FAIL** | pending |
| 2026-07-30 | TESTLOTTO backtest pool PIN | eval reset cache miss → backtest auto-WF · PATCH_PINS · backfill · 1136/1234 QA | **PIN OK** | pending |
| 2026-07-30 | tail-100 백테스트·UI 단일버튼 | repack ge3=0.23 combined=0.15 · run_id 3·4 · 「3뇌 예측」만 · pred/cache eval reset | **T100 OK** | pending |
| 2026-07-30 | TESTLOTTO 클릭 예측·재시작 로딩 금지 | prewarm 제거 · cache-only API · 「3뇌 예측」 · 1214 tier·1232 miss QA | **CLICK OK** | pending |
| 2026-07-30 | TESTLOTTO 4·5등 적중 표시 버그 | pool-view SSOT 채점 · hero·모달·카드 일치 · 1214/1234/1200/1235 QA | **FIX OK** | pending |
| 2026-07-30 | TESTLOTTO 로딩+15세트 UI | pool-view SQLite 캐시 hit ~4ms · accordion · sub-tabs · B-03 해결 | **LOAD OK** | pending |
| 2026-07-30 | TESTLOTTO UI/UX만 | B-04 스피너·스켈레톤 · CSS spacing · chevron · GenSpark UI 라운드 | **UI OK** | pending |
| 2026-07-30 | 7021 테스트로또 브라우저 QA | MCP 6항목 PASS · 버그5(이모지·K-SIGNAL summary 수정2) · pool-view 12~31s | **QA PASS** | pending |
| 2026-07-30 | TESTLOTTO UI+DB·10+5·한글 | backtest_runs 2건·pool-view API·7021 UI · REPORT_STYLE 과제表 | **UI OK** | pending |
| 2026-07-30 | 보고서 한국어·3등 긍정 | REPORT_STYLE·BENCH_TEMPLATE 용어表 · REPACK 보고서 한글화 · r3=1 복습 | **DOC OK** | pending |
| 2026-07-30 | 형 몰아주기(repack) GO | signal repack survey n=200 · top5 ge3=0.085 · combined=0.145 · DB reset 1260행 | **5장 FAIL** | pending |
| 2026-07-30 | TEST_PRIORITY 큐·숙제형 문서 | P0~P3 11건·용어表·BOOT/STATUS/AI_COLLAB 링크 | **DOC OK** | pending |
| 2026-07-30 | K-QUICK-GATE+SIGNAL-SELECT GO | BENCH§9·bench_quick_gate·combined QUICK ge3=0.145 n=200 | **QUICK PASS** | pending |
| 2026-07-30 | K-WINDOW-SIGNAL-01 GO·E2 | window hint 61variants n=1182 · best ge3=0.1328 · E2 bin lift | **FAIL** | pending |
| 2026-07-29 | 신호셋트 아키텍처·GenSpark 3turn | Tier0~4·통합5·구현순서7단계 · KWINDOW running 900/1182 | ARCH OK | pending |
| 2026-07-29 | K-AUX-SIGNAL-01 GO | hint inject live WF n=1182 · 5 variants×α · best ge3=0.1303 | **FAIL** | `579495e` |
| 2026-07-29 | DHLOTTERY 로또 감사 | lt645 result/stats/판매점 READ-ONLY · K-AUX-SIGNAL 3아이디어 · 보고서 | AUDIT OK | `394e790` |
| **K-BENCH-01-WIRE** | tier 피드백 live WF ge3=0.1142 · 롤백 · AUX_SIGNAL_PIVOT | WIRE FAIL | `pending` |
| 2026-07-29 | K-BENCH-01 GO | postmortem WF n=1182 · 쿼터갭43.6%·markov52.5% · AUX무상관 | BENCH01 SIGNAL | `pending` |
| 2026-07-29 | GenSpark+4보조·피드백 논의 | READ-ONLY 코드확인·형가설 판정·보고서·GenSpark 6문답 교차 | REVIEW OK | `pending` |
| 2026-07-29 | K-BENCH-02 GO | confidence 5축 live · baseline ge3=0.1100 최고 · AUX/conf 하회 | BENCH02 FAIL | `pending` |
| 2026-07-29 | K-BENCH-05·03 GO | baseline행·WF/tier 분리 · BENCH_REPORT_TEMPLATE · 보고서예시2 | PROTOCOL OK | `pending` |
| 2026-07-29 | 1군→ROK21 교훈 정리 | 배울·갖춘·금지 3섹션 · 1131~1231 3등15 · K-MONEY1-LESSONS | LESSONS OK | `pending` |
| 2026-07-29 | K-STAT-TUNE-WIRE·GO | ge3=0.1176 p=0.35 · 롤백 gap30/hot5 · NEXT=HOLD | WIRE FAIL | `bfa7222` |
| 2026-07-29 | K-STAT-TUNE·종료체크 | best0.1523>0.1447 p=3.6e-05 · NEXT=WIRE | TUNE PASS | `688805c` |
| 2026-07-29 | HOLD판단·팩트체크·push | HOLD맵 · 실레버공백 · 새벤치無 · V2유지 · 형A/B | HOLD맵 | `9d29038` |
| 2026-07-29 | GENMIX·팩트체크·push | GENMIX FAIL · live0.1303<pin · trunc동일 · NEXT=HOLD | GENMIX FAIL | `d8650db` |
| 2026-07-29 | AUX/생성레버·팩트체크·push | AUX-BLEND FAIL · live r=0.0134 · V2유지 · NEXT=HOLD | AUX-BLEND FAIL | `4ca44bf` |
| 2026-07-29 | 새직교축·팩트체크·push | GENDIV FAIL · Q1 ge3 0.1224 · V2유지 · NEXT=HOLD | GENDIV FAIL | `18848dc` |
| 2026-07-29 | K-POSTHOC-ANALYSIS | 50시드×50회 best ge3=0.18 p=0.109 · 무신호 · V2 pin유지 | POSTHOC 무신호 | `pending` |

---

## C) 확정 사실 (뒤집으려면 새 실측 · 재논쟁 금지)

| 사실 | 수치 | 근거파일 | 최종확인 커밋해시 |
|------|------|----------|------------------|
| 빈도 χ² p (main/bonus) | 0.965 / 0.877 | `docs/benchmarks/20260726_랜덤성검정/` | 미확인 |
| OOS 상위6 mean (freq/markov/recency) | 0.748 / 0.769 / 0.752 | 동상 step2 | 미확인 |
| OOS CI하한 > 0.80 | **없음** → 적중학습축 폐기 | K-11 · 랜덤성검정 보고서 | 미확인 |
| 인기도 Ridge Spearman / 수령배율 | 0.440 / 1.180× | 동상 step3 | 미확인 |
| all3 mean (최근100) | 0.797 CI[0.75, 0.845] | 뇌감사 audit | 미확인 |
| 1장 E[적중] | **0.80** | 초기하 · K-O | `93218f8` |
| AC 이론 최빈 / 합 이론평균 | **8** / **138** | `docs/benchmarks/20260727_KZ_theory_constants.json` | `3791727` |
| pattern/balance 명분 | **실증** | `WARRANT.md` · K-AA | `bb3fa91` |
| DEDUP E[k] (ON) | **100.000** | `docs/benchmarks/20260727_KV_dedup_verify.json` | `ba98f34` |
| DB MAX lotto4 / testlotto / hyodo | **1234 / 1234 / 1234** | `docs/benchmarks/20260727_KAB_draw_gap.json` · DB실측 | `e1a7cd2` |

---

## D) 절대 금지 (7줄)

1. `random.choices` **라인 수정** 금지 (oversample 후 선별은 허용)
2. `_get_draws_before` 변경 금지
3. boost 상한 변경 금지 (carry 0.2 / ending 0.3 / overdue 0.2)
4. 백테 컨닝 금지 (target 이후 draws·피드백 사용)
5. 원본 kweon(`D:\3kweon`)·memoy 쓰기 금지
6. DB 전체초기화 비권고·금지에 준함
7. STATUS·BOOT 본문·reports **압축 금지** (채팅 「간략」은 채팅만)

---

## E) 열린 결함 (FINDINGS.md 원본 · 여기 사본)

**OPEN (23):** K-00 · K-02 · K-05 · K-08 · K-10 · K-11 · K-12 · K-A · K-C · K-E · K-F · K-G · K-I · K-J · K-K · K-L · K-O · K-P · K-Q · K-R · K-T · K-U · **K-Y(이력)**  

**HOLD (2):** K-M · K-N  

**PATCHED (참고):** K-06 · K-07 · K-S · K-V · K-Z · K-AA · K-AB · K-AC · K-AD · K-AE · K-AF · **K-AG** · **K-X** · **K-W** · **K-B** · **K-H** · **K-D** · **K-P3** · **K-P5**  

**CLOSED:** K-01 · K-03 · K-04 · K-09  

※ **K-07 = PATCHED** (OPEN 아님). 상세·비고는 `FINDINGS.md`만 수정.

---

## F) 더 읽을 파일 우선순위

1. `BOOT.md`
2. `STATUS_LATEST.md`
3. `FINDINGS.md`
4. `WARRANT.md` (명분 라벨)
5. 최신 `reports/YYYYMMDD_*.md` (예: `20260727_KAB_회차갭정합.md` · `20260727_KAC_*.md`)  
   ※ 구 단독패턴 `YYYYMMDD_ROK21` 접두는 더 이상 권장하지 않음.