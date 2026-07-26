# 아이디어 게시판 (형 계획 병행) — 수시 추가

> 정답 없음. 명분·실험 후보만. 채택 시 날짜·커밋으로 박제.

## I-01 메타선별기 (Meta-Picker) — **우선 후보**
- 입력: 회차 t에 대한 3뇌×5세트 (나중 N뇌×5) 번호 멀티셋
- 출력: 재조립 6수 세트 1~K개 (+보너스 후보)
- 학습: 과거 t에서 풀이 당첨을 얼마나 담았는지(cover)와,  
  투표/빈도/보조뇌 점수로 **고른 6개**의 matched_count walk-forward
- 명분: 형 관찰(「세트는 달라도 풀에서 6개가 나온다」) + 실측 cover≪풀·≫단일세트

## I-02 출현 투표 (Vote≥2)
- 15세트(또는 5세트) 중 **2회 이상** 나온 번호만 후보
- 희소 노이즈 제거 · 풀 축소 → 조합 탐색 부담↓

## I-03 보조4뇌로 풀 재채점
- miss/pattern/balance/referee를 **재조립 후보 세트**에 그대로 적용
- 생성(예측뇌)과 선별(보조+메타) 분리 — 지금 아키텍처와 맞음

## I-04 커버 회차만 심층 학습
- `union_can_make_6=True` 인 과거 회차만 모아  
  「풀 안에서 당첨 6개를 고르는 규칙」을 지도 학습/규칙 탐색
- 커버 실패 회차는 메타선별 이전에 **예측 다양성** 문제

## I-05 보너스 7번째 신호
- 풀에 보너스가 들어온 비율 실측 ~80%대 →  
  2등(5+보너스) 경로를 메타 출력의 별도 슬롯으로

## I-06 뇌 추가 전 다양성 지표
- 뇌 추가 시 Jaccard(세트 간 겹침) 감시  
  겹치면 풀 unique↓ · cover 이득 없음
- 「똑똑한 뇌」보다 **서로 다른 렌즈**가 합집합 전략의 전제

## I-07 ending_digit 수정 이후 재측정
- detect 수정·learn 리셋 후, 동일 union 지표를 창(예: 최근 100회)으로 재집계  
  튜닝이 풀 품질에 미치는지 추적

## I-08 (보류) lotto4 기법 이식
- CDM/gapZ/EV는 **새 예측 렌즈**로 풀 다양성↑ 목적일 때만 A/B

## I-09 Vote≥2 WF 결과 (20260726) — **기각(단독)** / 하이브리드로 승격
- 실측: avg Vote≥2 **0.79** vs best단일세트 **2.22** (n=1233) → 단독 메타로는 열세
- 원인 가설: vote≥2 풀 ~25개 + 역사빈도로 6수 조립 → 이미 강한 단일세트 신호를 희석
- 다음: **하이브리드** = best세트 시드 + vote≥2 보강 / Vote≥3 / cover=6 회차만 규칙학습
- 스크립트: `tools/run_meta_vote2_wf.py` · 요약 `vote2_wf_summary.json`

## I-10 유사과거 패턴 (형 방향성 · 컨닝금지)
- 「지금 구조와 비슷한 과거 회차 → 그 다음 당첨 분포」를 target **이전만**으로 스카우트
- 스크립트: `tools/scout_similar_past_patterns.py` · `similar_past_scout.json`
- 무리(swarm) 후보: 홀짝/고저/합/AC · 끝수 · 갭 · 구간 · 학자 필터 등 역할분담 A/B

## I-11 L_ending 결합 (20260726) — **소폭 채택**
- ending_r1: avg 0.810 (+0.006 vs baseline 0.803), closer_to_oracle
- 시드 혼합·r2·풀top6은 악화 → **1슬롯만** 메타 기본에 반영
- `tools/run_meta_hybrid_ending_wf.py` · `hybrid_ending_wf_summary.json`

## I-12 cover6·시드 A/B (20260726) — **시드 변경 기각**
- 시드 후보 6종(+ending_r1): **aux가 all/cover6 모두 1위** → PIN 시드 유지
- cover6 재조립 hist_ending ~0.97 ≪ 그 회차 최고장 2.50
- 병목=**15장 중 장선택** · 다음 I-13 후보
- `tools/run_cover6_deep_and_seed_ab.py` · `cover6_deep_seed_ab.json`

## I-13 장선택 학습 (20260726) — **미채택**
- 선형 ridge WF: picker 0.80 ≪ aux 0.81 · adopt=false
- `tools/run_set_picker_wf.py` · `set_picker_wf_summary.json`
- 다음: 순위학습/트리 등 재시도 또는 짧은 오탐 점검

## I-14 판단 메모
- 튜닝 vs 메타 · DB초기화: `JUDGMENT_튜닝vs메타.md`
- 권고: 고르기 우선 · DB 전체초기화 비권고 · 3+4 역할 유지
