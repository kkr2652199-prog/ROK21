# RESTORE — ROK21 압축 복원 1순위 (이 파일 하나면 복원 완료)

> 새 세션 시작 큐 = **"동생, ROK21 RESTORE.md 읽고 시작해."**  
> **수치 SSOT:** `docs/benchmarks/*.json` · **결함:** `FINDINGS.md` · **명분 라벨:** `WARRANT.md`  
> BOOT/STATUS/RESTORE/RESUME_HERE 는 사본 — 충돌 시 위 원본이 이긴다.

---

## A) 30초 요약 (5줄)

1. **정체:** ROK21 = kweon 복사본 샌드박스 · `D:\ROK21` · 포트 **7021** · SSOT=`kkr2652199-prog/ROK21`
2. **3자 역할:** 형=결정 / 동생(Claude)=판단·지시서만 / 커서=실행·commit·push
3. **확정 결론:** 적중축 **폐기**. EV 배선 유지(Y풀 순1.033). **K-09 CLOSED**(실질 누수 무해)·전제라벨 제거
4. **물리 상수:** 1장 mean=**0.80** · best-of-15 천장=**2.27** (개선 목표 아님)
5. **현재 초점:** K-AB=3DB draws MAX **1234** 정합 · K-06 영구팬아웃은 안만 · (K-AC=압축대비 룰 보강)

---

## B) 턴 로그 (최신 ↑ · **최대 12행** · 초과 시 오래된 행 삭제)

| 일시 | 형 지시 요지 | 커서 실행 결과 | 판정 | 커밋 |
|------|--------------|----------------|------|------|
| 2026-07-27 | K-AC 압축대비 룰 | PART1답·RESTORE보정·drift0 · RULES초안승인대기 | K-AC OPEN | (push후) |
| 2026-07-27 | K-AB 회차갭정합 | hyodo INSERT 1232–1234 · mismatch0 · 회귀PASS | K-AB·07 PATCHED · K-06 OPEN | `e1a7cd2` |
| 2026-07-27 | K-AA 이론값적용·명분복귀 | 폴백138·AC8·consecPMF·배선PASS·실증2 · warrant동기 | K-AA·Z PATCHED | `bb3fa91` |
| 2026-07-27 | K-Z 이론값·상수대조 | 전수C45,6·AC8≠7·시뮬A거리↑ · 적용0 | K-Z→PATCHED(K-AA) | `3791727` |
| 2026-07-27 | K-Y 보조4 정밀감사 | 라벨강등·기여Δ·미소비키3 · 코드0 | K-Y OPEN · WARRANT개정 | `1c561bf` |
| 2026-07-27 | K-X review끝수 원인규명 | rate투영·폐루프없음·KS0.66 · 코드0 | 1차원인특정 · 교정대기 | `c7fe78d` |
| 2026-07-27 | K-W 정합성+명분라벨 | A/B/C거리·WARRANT·brain_warrant · 산출/dedup0 | K-W OPEN측정 · 라벨확정 | `5ebe898` |
| 2026-07-27 | K-V dedup 구현·검증 | E[k]97.09→100 · unresolved0 · 이표본OK · +0.015s | K-V PATCHED | `ba98f34` |
| 2026-07-27 | K-S선결+K-T/U/V 전제·포트 | as_of필수·CUTOFF기본ON·전제표·쌍null·k≈97 | K-S PATCHED · T/U/V OPEN | `fecb9a7` |
| 2026-07-27 | K-O~S 볼단위전환+WF설계 | 데이터감사·χ²균등·±30%·층화대기·WF설계 · 코드0 | K-M/N HOLD · 볼층위 | `93218f8` |
| 2026-07-27 | K-A~L부여+KB/C/D규명 | FINDINGS등재 · 표본비공유·best가중·fusion의도 | K-B SSOT=review JSON · 코드0 | `29d4594` |
| 2026-07-27 | SSOT확정+인코딩수정 | UTF-8로컬확인 · 규칙/훅/BOOT §4 · FINDINGS경위 | SSOT=ROK21 · kweon 264de3c동결 | `152e1bc` |

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

**OPEN (29):** K-00 · K-02 · K-05 · K-06 · K-08 · K-10 · K-11 · K-12 · K-A · K-B · K-C · K-D · K-E · K-F · K-G · K-H · K-I · K-J · K-K · K-L · K-O · K-P · K-Q · K-R · K-T · K-U · K-W · K-X · K-Y  

**HOLD (2):** K-M · K-N  

**PATCHED (참고):** K-07 · K-S · K-V · K-Z · K-AA · K-AB  

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
