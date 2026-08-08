# RESTORE — ROK21 압축 복원 1순위 (이 파일 하나면 복원 완료)

<!-- ROK21_RESUME_BLOCK -->
## 동생 복귀 5줄 (자동 · guard_boot와 동일 소스)

1. **HEAD:** `69b9c7d` · WORK=`IDLE`
2. **지금:** **K-BRAIN-INDEPENDENCE-AUDIT**(형GO · 버그사냥) — **INDEPENDENCE_OK 14/14**. 형 지시 「한번 더 버그를 찾아보자」로 **2건 추가 발견·수정** — ⑥`repack_by_brain` 이 `number_scores` 에 **`brain_tag` 미전달** → 뇌별 가중치 dict 가 **한 번도 조회 안 되는 죽은 배선**(첫 hint 절제가 `+0.0000` 이던 게 증상) ⑦hint 축 개방 직후 **또 죽은 배선 검출** → 호출자 누락에도 `repack_by_brain` 이 직접 만들게 수정 · **죽은배선 탐지 B6 신설**(dict 바꿔서 결과 안 바뀌면 실패) · **실측**: 3뇌 점수세트 번호겹침 Jaccard **0.664~0.687**(공유 14.2~14.5개) vs 무작위 기대 **0.250** = 약 2.7배 · hint 0 으로 두면 **0.743→0.30** → **공유 hint 가 주원인** · 10세트 완전성·pass0≠pass1·뇌간 동일세트 0건 통과 · hint 개방은 성적 무변화 실증
3. **다음1건:** K-STAT-TUNE-START-PICK — 형 지시 「한번 더 버그를 찾아보자 · 없으면 과거학습 뇌부터 튜닝」 → **버그 2건 발견·수정 후 14/14** 이므로 **이제 튜닝 착수 가능**. ⑹ **`brain_tag` 죽은 배선**: `repack_by_brain` 이 `number_scores` 에 `brain_tag` 를 안 넘겨 **뇌별 가중치 dict 가 한 번도 조회되지 않았다**. 처음 hint 절제가 `+0.0000` 으로 나온 게 이 버그의 증상(절제가 물리적으로 불가능했다) → `brain_tag=tag` 추가. 다른 5개 호출부는 전부 넘기고 있었고 발권 분석 경로 하나만 누락 · ⑺ **죽은배선 탐지 B6 신설** 후 hint 축을 열자 **즉시 또 검출** → `repack_by_brain` 이 spec 갈릴 때 직접 만들게 수정 · **실측(형이 걱정한 「예측번호 공유」의 크기)**: 3뇌 점수세트 번호겹침 Jaccard **0.664~0.687**(공유 14.2~14.5개) vs 무작위 기대 **0.250** = 약 **2.7배**, hint 가중치 0 으로 두면 **0.743 → 0.30** → **공유 hint 가 주원인 확정** · 점수세트 번호의 자기 pool 출신 비율 **0.79~0.82**(약 20% 가 pool 밖 유입) · **깨지지 않은 것**: 10세트 정확·set_no 1~10·번호형식·**pass0≠pass1**(「10세트가 실은 5세트」 의심은 사실 아님 · 3뇌 전부 난수 사용)·뇌간 동일세트 0건·pool 슬롯 2자리·RNG 독립·학습 교차오염 없음. 형 1건 선택 — **①과거학습 뇌(stat) 예측 튜닝 착수**(권장 · 형 예정대로 · **착수 전 백테스트 재생성 필수** — DB 리셋으로 learn_state·feedback 이 비어 피드백·boost 경로가 현재 무효) / ②뇌별 hint spec 값 차별화(배선·탐지기 완료 · **값 결정만 R38 게이트 필요** · 겹침 2.7배의 주원인이라 효과 큼) / ③1236+ 회차별 자동시스템 배선(형이 「이후 패치」로 미뤄둔 건) / ④트랙정지 (승인필요=없음 (발권경로 `coordinator` 무변경 · 동결항목 무접촉 · DB 커밋 안 함) · 선행=없음)
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
| 2026-08-08 | 「한번 더 버그를 찾아보자 · 없으면 stat 튜닝」 | **버그 2건 발견·수정 · 14/14** — ⑥`repack_by_brain` 이 `brain_tag` 미전달 → **뇌별 가중치 죽은 배선**(hint절제 +0.0000 이 증상) ⑦hint 축 개방 직후 또 검출 → 자동생성으로 수정 · **B6 죽은배선 탐지 신설** · 겹침 Jaccard 0.66~0.69 vs 기대 0.25(2.7배) · hint 0 → 0.30 = **공유 hint 주원인** · pass0≠pass1 확인 | **INDEPENDENCE_OK** | (본턴) |
| 2026-08-08 | 나머지 2뇌도 독립 패치 + 예측DB 리셋 | ④`expand_pool` 3뇌 **한 난수흐름**(stat→markov 오염) → 뇌별 시드리셋 ⑤pass0 시드=`seed+draw_no` → **pool1~5＝발권5세트**(C8) · 뇌별 상수dict 개방(값동일) · **hint 는 여전히 공유(명시)** · DB 3뇌예측 **7094행 삭제**(원천보존) · 검증 **9/9** | **WIRE_CONFORMS** | (본턴) |
| 2026-08-08 | 「성적판정 말고 신호강한세트로 몰아주기」 배선수정 GO | **배선결함 3건 수정** — ①3뇌 성적표공유(`for _tag`)→뇌별분리 ②`for sn in (4,5)`하드코딩→위치EMA상위(이탈률 1.0/1.0/0.9) ③markov 슬롯0→3뇌동일 · 검증 7/7 · 게이트대상아님(설계일치) | **WIRE_CONFORMS** | d338ac7 |
| 2026-08-08 | 몰아주기 정상작동 패치+과거학습 계속 | stat단독 n1183×seed5 · pool최고 0.2152=무작위**10장** 0.2143 → **전제붕괴(장수산수)** · 특성11개 상관≈0 · 선별전략 전부 현행이하 | **POOL=RANDOM** | d3c2059 |
| 2026-08-08 | ②seed평균화GO | n300·outer10×안쪽8 · R8 σ비 1.38배(√R 2.83 미달) · 해상도상한 1.4647배 · **회차로사면 5.99배싸다** → **배선안함** | **NOISE_CUT_NO** | 01e1bac |
| 2026-08-08 | ①바닥재측정GO | n1183·seed24 · 바닥0.0101→**0.005087** CI[−0.0082,0.0180] 0포함 → 「영원히판정불가」**철회** · R39신설(k_precision 7/7) | **FLOOR_NO** | (본턴) |
| 2026-08-08 | ②stat잡음원인GO | n400·seed24 · 유입점=뽑기확정(점수·repack결정적) · **전제붕괴**: 뇌별팽창차 구분가능쌍0/3 · 반사실 짝지은 p0.7156 무손해 | **PREMISE_NO** | 392320f |
| 2026-08-08 | ①seed전구간GO | n1183·seed10 · 바닥b=0.010127 · ~~FULL-WFΔ<바닥~~ **상단 재측정에서 철회됨** | ~~FLOOR확정~~ | 0fe62b1 |
| 2026-08-08 | ①게이트승격GO | k_gate공용모듈·R38강제·자기검증8/8·184벤치위반0·프로브exit=1확인 | **COMPLIANT** | 5675df6 |
| 2026-08-08 | 합리적패치+학습순서 | 눈금확정 n50K10잡음p95=0.16=적용상수Δ · 순서불변2.4e-17 · 문제답nopeek0.274<무작위0.311 | **RULER_COARSE** | 9a44877 |
| 2026-08-08 | 1번GO+감사+차원+자문 | 당첨자수NB2 FW p0.0004 인기편향실증·태그무신호·감사잔여6건·3차셀1.74 | **TAGS_NO** | de5d2da |
| 2026-08-08 | 논문벤치튜닝 | log-score15셀 전부 null미달·r0.985·PBO0 | **NO_SKILL** | 36156c1 |
| 2026-08-08 | KEEP GO | decay 0.005/0.05 확정 · 후보미채택 | **KEEP** | 45dba8e |
| 2026-08-08 | YT신뢰벤치 | 4축채택·tipster기각·decay보류권고 | **SURVEY** | f5db94d |
| 2026-08-08 | decay세부 | 후보 L0.01/S0.05 · fusion0.135 · 미적용 | **CAND** | 96fdc33 |
| 2026-08-08 | 틀잠금 | FRAME_LOCKED · 세부는다음 | **LOCK** | 0e14774 |
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