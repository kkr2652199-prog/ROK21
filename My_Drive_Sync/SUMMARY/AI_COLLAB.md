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

### 최신 상태 (2026-07-30 13:30 KST)
- **HEAD**: `b956fb0`
- **TESTLOTTO UI/UX**: **DONE** — B-04 스피너·스켈레톤 · sticky탭·카드여백 · chevron · `reports/20260730_TESTLOTTO_UIUX_REFRESH.md`
- **K-SIGNAL-SELECT-01**: **QUICK PASS** — combined ge3=0.145 p=0.102 · tail n=200
- **다음**: K-SIGNAL-SELECT-FULL (1182) · repack wire 불필
- **GenSpark UI 라운드 (20260730)** — genspark.ai 랜딩 OK · 채팅 미로그인 · 추론 아이디어 4건:
  1. 회차 히어로=KPI(당첨6+1·ge3 배지·pool/repack 적중 요약)
  2. 10+5=2단 아코디언(pool 접힘·repack 5장 히어로·신호 점수 바)
  3. 백테스트=ge3 스파크라인·combined vs repack 색 분리·회차별 드로어
  4. pool-view 대기=progress bar + 경과초 (백엔드 캐시 없이 UX만)
- **GenSpark 전략 (기존)**: repack artifact vs 5장 공정 — 「장수 줄이면서 신호 유지 repack 변형?」

### 논의 이력 (최신순)
1. **[13:25] TESTLOTTO UI/UX 리프레시** — B-04 로딩 · CSS grid/spacing · GenSpark UI 라운드 · `20260730_TESTLOTTO_UIUX_REFRESH.md`
2. **[12:40] K-SIGNAL-REPACK-01 (형 몰아주기)** — 번호 repack survey · DB reset 1260행 · `20260730_KSIGNAL_REPACK_SURVEY.md`
2. **[12:05] K-SIGNAL-SELECT-01 QUICK** — combined PASS ge3=0.145 · overlap 단독 FAIL · `20260730_KSIGNAL_SELECT_SURVEY.md`
2. **[00:10] K-WINDOW-SIGNAL-01 완료** — best w4_zone_mix ge3=0.1328 · E2 bin lift 미약
3. **[23:45] 신호셋트 아키텍처 3라운드** — GenSpark QUICK_GATE tail-200 p<0.15 합의
3. **[22:10] 커서×젠스파크 브라우저 협의** — E1 null 대비 유의 but pin 미달 · 우선순위 window→E2→E3
4. **[22:00]** K-AUX-SIGNAL-01 FAIL — best ge3=0.1303 · `20260729_KAUX_SIGNAL_SURVEY.md`
5. **[21:00]** K-BENCH-01 postmortem SIGNAL_FOUND — `20260729_KBENCH_POSTMORTEM.md`

## 4. 파일 지도 (젠스파크용 GitHub raw URL)

| 용도 | URL |
|------|-----|
| 현재상태 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/EXTERNAL_START.md` |
| 협업룰+대화 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/AI_COLLAB.md` |
| NEXT 1건 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md` |
| 수치 SSOT | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/` |
| 보고서 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/` |
| 보고서 언어 규칙 | `My_Drive_Sync/SUMMARY/REPORT_STYLE.md` |

## 5. 언어 규칙 (Cursor × 형 · 2026-07-30)

- **형이 읽는 모든 보고서·STATUS·UI 문구 = 한국어** (초보 친화). 코드·JSON 필드명만 영어.
- 영어 약어는 **한국어(괄호)** — 예: ge3(3개 이상 적중률) · repack(몰아주기) · p(유의확률).
- 용어表 SSOT: `REPORT_STYLE.md` · `reports/BENCH_REPORT_TEMPLATE.md` §용어表.
- 형의 **긍정 결과**(예: REPACK 3등 1회)는 복습·STATUS에 반드시 명시.
