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

### 최신 상태 (2026-07-29 23:45 KST)
- **HEAD**: `bcaf29b` (push 후 갱신)
- **K-WINDOW-SIGNAL-01**: **running** ~900/1182 (kill 금지) · pin ge3=0.1447 대비
- **형 신호셋트 아키텍처**: 5→10세트→신호셋트5 · Tier0~4 프레임 · `reports/20260729_SIGNAL_SET_ARCHITECTURE.md`
- **3자 합의**: 10세트=조건부찬성 · 신호셋트=**통합5** · 선별=(b)overlap→(a)bin→(c)Jaccard · coordinator wire=형 GO 전 금지

### 논의 이력 (최신순)
1. **[23:45] 신호셋트 아키텍처 3라운드** — GenSpark: 「조건부 찬성」「통합5」「QUICK_GATE tail-200 p<0.15」「QUICK_GATE는 SIGNAL-SELECT 후」→ 구현순서 §6 확정 · GenSpark browser 3-turn
2. **[23:10] 1군 벤치·이식 인벤토리** — deterministic_sets/honesty/fusion/QUICK_GATE P0~P3 · `_k_window_signal_survey.py` --n-eval 패치 필요 · `reports/20260729_MONEY1GUN_BENCH_INVENTORY.md`
2. **[22:51] 1군 vs ROK21 testlotto READ-ONLY 비교** — 6뇌+fusion vs 3+4 coordinator · `reports/20260729_MONEY1GUN_VS_ROK21.md`
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
