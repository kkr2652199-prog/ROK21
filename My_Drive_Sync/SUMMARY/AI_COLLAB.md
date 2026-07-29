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

### 최신 상태 (2026-07-29 21:50 KST)
- **HEAD**: `fa5db9c`
- **현재 배선**: WIRE-V2 (ge3=0.1447) — pin 유지
- **K-BENCH-05·03**: baseline행(0.8/0.1137)·WF/tier 분리 프로토콜·템플릿 **완료**
- **다음**: K-ATTACK-HOLD · 형 GO 후 K-BENCH-02 confidence survey

### 논의 이력 (최신순)
1. **[21:50]** 형 GO — K-BENCH-05·03 즉시: BENCH_PROTOCOL §6·§7 · BENCH_REPORT_TEMPLATE · 02·01은 GO 후
2. **[19:35]** 1군(MONEY lol)→ROK21 교훈 정리 완료 — 배울점/갖춘점/금지점 · 1131~1231 3등15건 표
2. **[18:26]** 형 아이디어: 랜덤 시드별 백테스트 → 좋은 결과 역추적 → 신호 좁히기. 커서+젠스파크 동의
3. **[18:14]** 젠스파크 K-LIVE-GRID 지시서 초안 작성. markov override 검토 요청
4. **[18:09]** 커서→젠스파크: 세션압축 대비 규칙 4가지 공유 + REVIEW-TUNE FAIL 결과 전달
5. **[17:50]** 젠스파크 전략 분석: set_no_asc가 잠긴 레버, 뇌 생성 로직 자체가 실질 레버
6. **[17:30]** 커서-젠스파크 연결 성공. AI_COLLAB.md 제안 합의

## 4. 파일 지도 (젠스파크용 GitHub raw URL)

| 용도 | URL |
|------|-----|
| 현재상태 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/EXTERNAL_START.md` |
| 협업룰+대화 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/AI_COLLAB.md` |
| NEXT 1건 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md` |
| 수치 SSOT | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/` |
| 보고서 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/` |
