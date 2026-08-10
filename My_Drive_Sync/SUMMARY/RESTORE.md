# RESTORE — ROK21 압축 복원 1순위 (이 파일 하나면 복원 완료)

<!-- ROK21_RESUME_BLOCK -->
## 동생 복귀 5줄 (자동 · guard_boot와 동일 소스)

1. **HEAD:** `88fe1d9` · WORK=`IDLE`
2. **지금:** **K-GENSPARK-IDEA-CHECK** — 4안 READ-ONLY 실측 · BLEND=단일노브+다seed cn보조 · 뇌별W·stat튜닝 HOLD
3. **다음1건:** K-GENSPARK-IDEA-CHECK-DONE — **젠스파크 아이디어 사전검증 완료**. 형→젠스파크에 `reports/20260810_KGENSPARK_IDEA_CHECK.md` 붙여넣기. 젠스파크가 커서 의견 합산 후 **BLEND 소튜닝 지시서** 작성. 커서 대기. (즉시반영=단일 BLEND_STRENGTH+EV/prefer게이트+다seed cn보조 · HOLD=뇌별W·stat튜닝·cn단독하드) (승인필요=형(붙여넣기) → 젠스파크 지시서 · 선행=없음)
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
| 2026-08-10 | 젠스파크 4아이디어 사전검증 | seed5 cn안정 · weight0 · referee균등 · 게이트3 PASS · 의견제출 | **CHECK_DONE** | (본턴) |
| 2026-08-10 | 다음패치전 논문·GH 정밀분석 | Thaler-Ziemba/conscious/Hai4320 등 · 배울점·금지점 · wire否 | **DOC_SURVEY** | 9d2670a |
| 2026-08-10 | 종료체크·20260810보고서없음 | HOLD_OFF를 `20260810_*`로 재기록·커서보고서동기 · 오명0808삭제 | **DOC_FIX** | 373a1c8 |
| 2026-08-10 | 홀딩 챕 다시 풀어줘 | `FOCUS_HOLD=false` · predict/strategy-x/hyodo 복원 · autoload 복원 | **HOLD_OFF** | 0c4f640 |
| 2026-08-08 | 다음진행·패치OK→독립튜닝 | SCORE_WEIGHTS cand_A **APPLY** · prefer+0.023 · prize−0.027 · hit+0.005 · V1/V2유지 | **APPLY** | 536360f |
| 2026-08-08 | 3뇌독립·hint분리·EV게이트 | hint 3축 분리 V1~V5 **5/5** · EV Δ−0.09 **MARGINAL** consistent · PREDICT실뇌 | **WIRE_CONFORMS** | 9582ac7 |
| 2026-08-08 | 선호번호·금액뇌 재구조·과거학습 판단진행 | 흐름술사→선호번호 · 복습왕→금액뇌 · crowd_signal+문헌 · SMOKE_OK · ge3주장없음 | **WIRE_SMOKE_OK** | e652318 |
| 2026-08-08 | 가장 추천방식(①기록채우기) GO | 1216~1235 **20/20** · stat숙제5장강제 · pred200(stat100) · learn3 · evolve60 · pool60 · 298초 | **FILL_OK** | (본턴) |
| 2026-08-08 | 전략X홀딩·테스트만 | UI HOLD·기본testlotto·예측autoload OFF | **HOLD** | 741de31 |
| 2026-08-08 | 과거학습 뇌 패치준비 체크·인간관점 | READ-ONLY · 방향준비·기록미준비 · 확정길=회차숙제 | **READY_DIR/NOT_TUNE** | 11a6890 |
| 2026-08-08 | 「한번 더 버그를 찾아보자 · 없으면 stat 튜닝」 | **버그 2건 발견·수정 · 14/14** — ⑥`brain_tag` 죽은배선 ⑦hint축 또 검출·자동생성 · B6 신설 · 겹침 2.7배=공유hint | **INDEPENDENCE_OK** | 69b9c7d |
| 2026-08-08 | 나머지 2뇌도 독립 패치 + 예측DB 리셋 | ④`expand_pool` 3뇌 **한 난수흐름**(stat→markov 오염) → 뇌별 시드리셋 ⑤pass0 시드=`seed+draw_no` → **pool1~5＝발권5세트**(C8) · 뇌별 상수dict 개방(값동일) · **hint 는 여전히 공유(명시)** · DB 3뇌예측 **7094행 삭제**(원천보존) · 검증 **9/9** | **WIRE_CONFORMS** | (본턴) |
| 2026-08-08 | 「성적판정 말고 신호강한세트로 몰아주기」 배선수정 GO | **배선결함 3건 수정** — ①3뇌 성적표공유(`for _tag`)→뇌별분리 ②`for sn in (4,5)`하드코딩→위치EMA상위(이탈률 1.0/1.0/0.9) ③markov 슬롯0→3뇌동일 · 검증 7/7 · 게이트대상아님(설계일치) | **WIRE_CONFORMS** | d338ac7 |
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