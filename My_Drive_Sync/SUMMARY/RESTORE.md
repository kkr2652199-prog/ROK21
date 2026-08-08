# RESTORE — ROK21 압축 복원 1순위 (이 파일 하나면 복원 완료)

<!-- ROK21_RESUME_BLOCK -->
## 동생 복귀 5줄 (자동 · guard_boot와 동일 소스)

1. **HEAD:** `5c93cda` · WORK=`IDLE`
2. **지금:** **K-STAT-NOISE-SOURCE**(n400·seed24) — 잡음 유입점 **'뽑기' 단계로 확정**(점수·repack 결정적) · 그러나 **PREMISE_NOT_ESTABLISHED**: 뇌별 팽창차(stat1.2739/markov0.7329)가 seed10 오차 안(구분가능쌍 **0/3**) · 뇌수준 std 도 stat0.016040/markov0.015184/review0.013584 **동일** → stat 전용 대책 근거 없음
3. **다음1건:** K-NOISE-SOURCE-NEXT-PICK — stat 잡음 원인 진단 완료 — **결론: 질문의 전제가 무너짐(PREMISE_NOT_ESTABLISHED)**. 뇌별 팽창차(stat 1.2739 / markov 0.7329)는 seed10 측정오차 안이라 구분가능쌍 **0/3**. 잡음 유입점은 **'뽑기' 단계로 확정**(점수·repack 모두 결정적). 형 확인 후 1건 선택 — **①잡음바닥 seed 16+ 재측정**(권장 · 현 바닥 b=0.010127 이 seed10 기반이라 바닥 자체의 오차가 미상 · 이 값이 앞으로 모든 판정 임계를 정함 · stat↔markov 구분에 seed 16이면 충분) / ②회차 1236+ 전향적 EV 로그 시작 / ③seed 평균화 설계(같은 회차 반복 뽑기→번호 득표 · random.choices 무수정 · 발권경로 변경이라 형 GO 필요) / ④트랙정지 (승인필요=없음 (①②는 측정·기록만 · 발권경로 무변경) / ③은 형 GO 필수 · 선행=없음)
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
| 2026-08-08 | ②stat잡음원인GO | n400·seed24 · 유입점=뽑기확정(점수·repack결정적) · **전제붕괴**: 뇌별팽창차 구분가능쌍0/3 · 반사실 짝지은 p0.7156 무손해 | **PREMISE_NO** | (본턴) |
| 2026-08-08 | ①seed전구간GO | n1183·seed10 · 바닥b=0.010127(R²0.9985) · FULL-WFΔ0.0047<바닥 | **FLOOR확정** | 0fe62b1 |
| 2026-08-08 | ①게이트승격GO | k_gate공용모듈·R38강제·자기검증8/8·184벤치위반0·프로브exit=1확인 | **COMPLIANT** | 5675df6 |
| 2026-08-08 | 합리적패치+학습순서 | 눈금확정 n50K10잡음p95=0.16=적용상수Δ · 순서불변2.4e-17 · 문제답nopeek0.274<무작위0.311 | **RULER_COARSE** | 9a44877 |
| 2026-08-08 | 1번GO+감사+차원+자문 | 당첨자수NB2 FW p0.0004 인기편향실증·태그무신호·감사잔여6건·3차셀1.74 | **TAGS_NO** | de5d2da |
| 2026-08-08 | 논문벤치튜닝 | log-score15셀 전부 null미달·r0.985·PBO0 | **NO_SKILL** | 36156c1 |
| 2026-08-08 | KEEP GO | decay 0.005/0.05 확정 · 후보미채택 | **KEEP** | 45dba8e |
| 2026-08-08 | YT신뢰벤치 | 4축채택·tipster기각·decay보류권고 | **SURVEY** | f5db94d |
| 2026-08-08 | decay세부 | 후보 L0.01/S0.05 · fusion0.135 · 미적용 | **CAND** | 96fdc33 |
| 2026-08-08 | 틀잠금 | FRAME_LOCKED · 세부는다음 | **LOCK** | 0e14774 |
| 2026-08-08 | 후보적용 | win26/mix0.8·tune재현·fusionΔ0 | **PASS** | d5b466d |
| 2026-08-08 | engine스윕 | 후보 win26/mix0.8 ge30.28 · 미적용 | **CAND** | addc82b |
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