# RESTORE — ROK21 압축 복원 1순위 (이 파일 하나면 복원 완료)

<!-- ROK21_RESUME_BLOCK -->
## 동생 복귀 5줄 (자동 · guard_boot와 동일 소스)

1. **HEAD:** `eef6fe2` · WORK=`IDLE`
2. **지금:** **K-UI-BT-STRUCT-FIX** — backtest 회차 accordion UI 통일 · JS `20260803e` · **local**
3. **다음1건:** K-UI-BT-STRUCT-FIX — backtest-only 회차(1210 등) 3뇌 accordion UI 통일 · JS `20260803e` · Ctrl+F5 QA · 형 GO 시 commit+push (승인필요=미확인 · 선행=없음)
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
| 2026-08-03 | backtest 회차 UI붕괴 수정 | draw-index stub 제거 · accordion 통일 · JS 20260803e · 1210 QA OK | **FIX** | local |
| 2026-08-03 | 종료체크 commit+push | actuals+pool-index batch · JS 20260803c · draw switch 0-fetch | **DONE** | 710d5a3 |
| 2026-08-03 | 서버 종료후 재가동 | 7021 kill→run_v13 · home=200 · draw-index n=200 | **OK** | cc05d38 |
| 2026-08-03 | 200회DB즉시적용·버그확인 GO | draw-index 프리로드 · init수정 · JS 20260803b · 서버재기동 | **DONE** | 37e945b |
| 2026-08-03 | 백테DB→즉시반응 GO | K-UI-BT-INSTANT · GET 자동WF 제거 · backtest_only 즉시 · 1100≈86ms | **DONE** | 6536464 |
| 2026-08-03 | 재검증 진행 GO | 리셋 WF · QUICK200 ge3=0.1350 · FULL ge3=0.1184 · patch PASS · pin FAIL | **REVAL** | 144461e |
| 2026-08-03 | 제자리분석→패치 GO | K-FUTURE-WIRE · 독립뇌 RNG+aux_hint · smoke PASS · n=100 ge3=0.1500 | **PASS** | ae582fb |
| 2026-08-03 | K-FUSION-INNOVATION GO | conf bucket+AUX reweight · smoke PASS · n=100 ge3=0.0900 tie · INNOVATION 롤백 | **FAIL** | dcc20b3 |
| 2026-08-03 | 젠스파크 동기화 GO | 20260803 보고서 · AI_COLLAB §3·§6 · RESTORE commit열 | **DOC** | 8b20473 |
| 2026-08-02 | K-FUSION-DYNAMIC-V2 GO | solo×ref quota · referee-only 0.06→solo prior 0.09 · plan 4/0/1 · gate FAIL 1bp | **FAIL** | f97312c |
| 2026-08-01 | K-QUOTA-MARKOV80-REV2 GO | floor 4/5 · smoke PASS · n=100 ge3=0.0900 quota 80/20/0 · gate FAIL · rollback | **FAIL** | 289f4b1 |
| 2026-08-01 | K-FUSION-QUOTA-FIX GO | DEFAULT 25/60/15 · smoke 5/5 · n=100 ge3=0.0800 quota 20/60/20 · +0.02 vs 0.06 | **FAIL** (>0.09) | bc8c32e |
| 2026-08-01 | K-ENGINE-PHASE1-HOLD GO | window100 롤백 · fusion diag ge3=0.0900 quota=0.40 aux=0.67 | **AUX_PATH_BOTTLENECK** | f1ae730 |

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