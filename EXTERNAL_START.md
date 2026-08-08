# EXTERNAL_START — 외부 에이전트 작업 흐름 진입점

> **이 파일 하나면 흐름 복구.** GitHub 404 / 로컬 미접근이면 형이 이 파일 전체를 채팅에 붙여넣는다.
> **젠스파크 압축 시:** `My_Drive_Sync/SUMMARY/GENSPARK_COMPRESS_RECOVER.md` 를 **같이** 붙여넣기 (채팅기억 불신·JSON 재페치).
> 상세 복사용 프롬프트: `My_Drive_Sync/SUMMARY/EXTERNAL_AI_BOOTSTRAP.md`
> **핀 베이스라인:** `My_Drive_Sync/SUMMARY/PINNED_BASELINE.md`
> 동생 큐(권한 있을 때): `My_Drive_Sync/SUMMARY/RESTORE.md`

## LIVE 작업 흐름 (자동 동기 · 외부AI 1순위)

| 키 | 값 |
|----|-----|
| HEAD(실측) | `0fe62b1` |
| BASELINE_PIN | `640cb67` |
| WORK | `IDLE` |
| 지금 | **K-STAT-SEED-NOISE-FLOOR** — n1183·seed10 전구간 · stat ge3 폭 **0.035503** · 분산적합 `a²/n+b²` → **바닥 b=0.010127**(R²0.9985) · **FULL-WF Δ+0.0047 < 바닥 → 표본 늘려도 판정 불가** |
| 직전 | R38 게이트 강제 가동(k_gate 공용모듈 · COMPLIANT) · DECISION-GATE(win26/mix0.8=NOISE_SELECTION_CONFIRMED · 순서불변 2.429e-17) |
| BOOT다음 | ①1236+ 전향적 EV로그 ②stat 잡음저감(팽창1.27 · markov 0.73 대비 최악) ③legacy 판정 게이트 소급적용 중 **형 1건 선택** · 발권가중 금지 |
| NEXT1 ID | **K-NOISE-FLOOR-NEXT-PICK** |
| NEXT1 할일 | 잡음 하한 확정 완료(**바닥 b=0.010127** · FULL-WF Δ+0.0047 이 바닥 미만 → 적중축은 표본을 늘려도 판정 불가로 확정) 형 확인 후 1건 선택 — **①회차 1236+ 전향적 EV 로그 시작**(권장 · 적중축이 닫혔으므로 유일하게 남은 인기회피축을 개입 없이 검증) / ②stat 잡음 저감 진단(팽창 stat 1.2739 vs markov 0.7329 — 왜 stat만 잡음을 더하는지 원인 특정) / ③legacy 132건 중 상수·배선에 실제 영향 준 판정만 게이트 소급적용 / ④트랙정지 |
| 승인필요 | 없음 (①~③ 모두 측정·기록만 · 발권경로 무변경) |
| 선행 | 없음 |
| OPEN샘플 | K-00, K-02, K-05 |

### 역할
- 형=결정 · 동생(너)=판단·짧은 지시서 · 커서=실행·commit·push
- 너는 D:\ROK21 / 비공개 GitHub를 못 열 수 있다 → **이 LIVE 블록이 SSOT**
- 404 = 권한 없음(경로 오류 아님). D:\3kweon·memoy·1~3군 미접촉

### 본선 vs 인프라
- 테스트로또 **3예측+4보조 유지** (구조 해체 없음)
- K-AB~AF = 수집/문서/훅(예측력 무관) · 인프라 지시 남발 금지
- 형 방향 = 전제 실증·쓸모 (적중↑ 랜덤앱 아님)

### 네가 할 일
1. 첫줄 `[복귀] HEAD=0fe62b1 · 지금=**K-STAT-SEED-NOISE-FLOOR** — n1183·seed10 전구간 · stat ge3 폭 **0.035503** · 분산적합 `a²/n+b²` → **바닥 b=0.010127**(R²0.9985) · **FULL-WF Δ+0.0047 < 바닥 → 표본 늘려도 판정 불가** · 다음=K-NOISE-FLOOR-NEXT-PICK`
2. 승인 없으면 장문 지시서 금지 · 형에게 질문 1개
3. 추가 파일 필요 시: `형, SUMMARY/○○.md 붙여줘`

## 압축 복구 (젠스파크)
1. 채팅 기억·압축 전 장문 = **불신**
2. `GENSPARK_COMPRESS_RECOVER.md` 붙여넣기 + 증거체인 JSON raw fetch
3. `[복귀]` 한 줄 후, JSON과 불일치하는 기억은 폐기 선언

## 파일 지도 (권한 있을 때만)
| 용도 | 경로 |
|------|------|
| 복귀5줄 | `My_Drive_Sync/SUMMARY/RESTORE.md` |
| NEXT 1건 | `My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md` |
| 매턴요약 | `My_Drive_Sync/SUMMARY/FLOW_BRIEF.md` |
| **젠스파크압축복구** | `My_Drive_Sync/SUMMARY/GENSPARK_COMPRESS_RECOVER.md` |
| 결함 | `My_Drive_Sync/SUMMARY/FINDINGS.md` |
| 명분 | `My_Drive_Sync/SUMMARY/WARRANT.md` |
| 핀 베이스라인 | `My_Drive_Sync/SUMMARY/PINNED_BASELINE.md` |
| 수치 | `docs/benchmarks/*.json` |

_generated: 0fe62b1_
