# AI_COLLAB — 커서×젠스파크 협업 규칙 + 대화 요약

> **세션 압축 대비 SSOT.** 젠스파크 세션이 압축되면 이 파일 + EXTERNAL_START.md 를 읽어 복구.

## 1. 역할 분담

| 역할 | 담당 | 권한 |
|------|------|------|
| **형(오빠)** | 최종 결정·GO/HOLD 승인 | 모든 방향 결정권 |
| **커서** | 코드 실행·commit·push·지시서 작성·벤치마크 | D:\ROK21 직접 접근, GitHub push |
| **젠스파크** | 전략 분석·검토·지시서 초안·팩트체크 | GitHub raw 읽기 전용 |

### 원칙
- AI끼리 논의 OK, **방향 확정은 반드시 형 GO**
- 지시서 작성: 커서가 최종본 작성·실행 (젠스파크 초안 참고 가능)
- 수치 인용: `docs/benchmarks/*.json` SSOT만 (기억으로 쓰지 않음)

## 2. 세션 압축 대비 규칙

1. **GitHub = 영구 기억.** reports/, docs/benchmarks/, EXTERNAL_START.md, NEXT_ACTIONS.md, AI_COLLAB.md 가 SSOT
2. **압축되면 GitHub 파일 먼저 읽기.** 특히 EXTERNAL_START.md (현재상태) + AI_COLLAB.md (협업룰+대화요약)
3. **커서가 매 push 시 이 파일의 §3 대화요약을 갱신** → 압축 후에도 논의 맥락 복구 가능
4. 형이 젠스파크에 "GitHub 보고서 확인해줘" 하면 → 젠스파크가 raw URL로 읽고 팩트체크

## 3. 대화 요약 (커서가 매 push 시 갱신)

### 최신 상태 (2026-07-29 22:10 KST)
- **HEAD**: `89e4ec8`
- **현재 배선**: WIRE-V2 (ge3=0.1447 stored) — pin 유지 · live baseline ge3=0.1218
- **K-AUX-SIGNAL-01 (E1)**: **FAIL** — best miss_pattern@α=0.2 ge3=0.1303 p=0.042 · pin 미달
- **커서×젠스파크 합의**: E1 FAIL≠피벗 포기 · stored/live 갭(Δ0.0229)이 병목 · **다음 GO 후보=K-WINDOW-SIGNAL-01 survey**

### 논의 이력 (최신순)
1. **[22:51] 1군 vs ROK21 testlotto READ-ONLY 비교** — 6뇌+fusion vs 3+4 coordinator · `reports/20260729_MONEY1GUN_VS_ROK21.md`
2. **[22:10] 커서×젠스파크 브라우저 협의** — E1 null 대비 유의(p=0.042) but pin 미달 · stored 0.1447 vs live 0.1218 갭 핵심 · 우선순위 **window_signal→E2→E3** · 형 GO 1건=`K-WINDOW-SIGNAL-01 survey`
2. **[22:00]** K-AUX-SIGNAL-01 FAIL — hint inject survey n=1182 · best ge3=0.1303 · `20260729_KAUX_SIGNAL_SURVEY.md`
3. **[21:35]** 동행복권 로또6/45 공식 페이지 감사 — `20260729_DHLOTTERY_LOTTO_AUDIT.md`
4. **[21:00]** K-BENCH-01 postmortem SIGNAL_FOUND — `20260729_KBENCH_POSTMORTEM.md`

## 4. 파일 지도 (젠스파크용 GitHub raw URL)

| 용도 | URL |
|------|-----|
| 현재상태 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/EXTERNAL_START.md` |
| 협업룰+대화 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/AI_COLLAB.md` |
| NEXT 1건 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md` |
| 수치 SSOT | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/` |
| 보고서 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/` |
