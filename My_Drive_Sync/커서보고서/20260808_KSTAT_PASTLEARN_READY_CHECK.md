# K-STAT-PASTLEARN-READY-CHECK — 과거학습 뇌 패치 준비 점검

- 생성: 2026-08-08 · HEAD `3ceb0e8` · READ-ONLY
- 질문: 「확정 길(회차 숙제 N = 재료 1..N-1)로 패치할 준비가 된 뇌인가?」

## 1. 판정

| 항목 | 상태 | 근거 |
|---|---|---|
| 회차 숙제 방향(워크포워드) | **준비됨** | `_get_draws_before(1235)` → last=1234 · `predict` target=`draws[-1]+1` |
| 컨닝 차단 | **준비됨** | `ROK21_LEARN_CUTOFF` · `set_learn_as_of` 없으면 learn_state 로드 차단(실측) |
| 파이프 본체 | **준비됨** | `transition(OFF) → engine(v2 ON) → aux → past_learn soft → diversity` |
| 과거학습 soft·태그 | **켜짐** | `PAST_LEARN_WIRE=True` · `ENGINE_V2=True`(past_learn 경유) · ASSOC OFF |
| 명분(reasoning) 문자열 | **약함·있음** | 예: `과거학습: 빈도가중+끝수…+이월… [과거학습:1yHot…]` — 설명은 있으나 **채점 후 명분 누적 DB는 비어 있음** |
| 학습 고리(피드백·learn_state) | **비어 있음** | 리셋 후 `learn_state=0` · `predictions=0` · `hit_warrant_log=0` · `evolve_log=0` |
| 성적 튜닝 착수 | **아직 아님** | 재료(하드코딩·decay) 손대는 단계는 게이트 필요 · 지금은 **흐름·명분 점검 단계** |

**한 줄:** 방향(회차 숙제)으로는 준비됐고, **학습·명분 기록이 비어 있어 “튜닝 패치” 직전 단계는 아니다. 먼저 숙제→채점 기록을 채워야 한다.**

## 2. 실측 스냅샷 (1235 예측)

- 재료: draw_no ≤ 1234 (1234건)
- 출력 예: method=`과거학습` · tags=`1yHot[...]` · 학습조정 이월×1.00 끝수×1.00 (중립=학습상태 없음)

## 3. 인간 관점 권장 순서

1. 확정 길을 문서·BOOT에 잠근다 (이미 합의)
2. 백테스트/회차 숙제로 **기록부터 채운다** (빈 DB로 숫자 튜닝 금지)
3. 한 회차 샘플로 “왜 이 번호인가”가 읽히는지 본다
4. 그다음 재료(창·핫·피드백)만 손댄다 · R38 게이트
