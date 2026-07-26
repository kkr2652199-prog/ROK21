# 20260726 — 형 계획: 세트 합집합 · 메타 선별

## 목적
형(사용자)이 부여한 **병행 진행 권한** 아래, 뇌 튜닝과 별도로  
「5세트×N뇌 예측 풀에서 6+보너스를 다시 조립」하는 흐름을 명문화·실측한다.

## 형 계획 원문 요지
1. 뇌당 5세트 예측 vs 당첨은 1세트(6+보너스1).  
   어떤 회차는 5세트에 흩힌 번호들을 잘 모으면 1~5등급 조합이 나온다.  
   25칸(또는 15×6) 안 중복을 구분해 선별하면 6개 적중 회차도 있다.  
   → **과거·그 과거** 정보가 핵심.
2. 현재 테스트로또 3예측+4보조. 이후 뇌 추가 후,  
   각 뇌 예측 번호에서 패턴을 찾아 **6개짜리 소수 세트**를 만드는 구조로 업그레이드 예정.  
   아이디어는 수시 게시.

## 운영 원칙 (형 지시)
- GitHub에 **무조건 히스토리 저장** (말 없어도 종료 시 commit+push)
- 원본 kweon 미접촉 · ROK21만
- 정답 보장 아님 · **명분·실험** 중심

## 실측 한 줄 (상세는 union_coverage.json)
3뇌 합집합이 당첨 6개를 풀에 담는 비율 **~27.9%** (단일 뇌 5세트는 **&lt;1%**).  
평균 풀 커버 **4.87** vs 최선 단일세트 적중 **2.22** → **메타 선별 갭이 형 계획의 본체**.

## Vote≥2 메타 WF (20260726) — 진행 방향 확인 + 단독은 기각
| 지표 | 값 (n=1233) |
|------|-------------|
| avg best 단일세트 | **2.22** |
| avg Vote≥2 (역사빈도) | **0.79** |
| avg Vote≥2+유사과거 | **0.78** |
| Vote≥2가 best 이김 | 4회 |
| 오라클 풀 cover (상한) | **4.87** |

→ **형 지시대로 tools에 올려 best 대비 WF한 것은 맞음.**  
→ 단독 Vote≥2는 best세트보다 열세 → 다음 **하이브리드 / Vote≥3 / cover=6 규칙**.  
파일: `vote2_wf_summary.json` · `tools/run_meta_vote2_wf.py`

## PIN 실행 결과 (20260726 P0~P5)
| Phase | 결과 |
|-------|------|
| P1 hybrid | seed/meta **0.80** vs oracle **2.22** · **pass_p1=false** · UI deferred |
| P2 cover6 | best rule `hist_only` hit~0.94 on cover6; all-WF meta still ~0.77 |
| P3 swarm | **KEEP L_ending** (lift +0.024); 나머지 REJECT |
| P4 KPI | unique~36.5 · cover6 27.9% · Jaccard 0.10 · **gate_pass** |
| P5 API | `GET/POST /api/testlotto/meta/*` · ui_enabled=false until pass |

문서: [PINNED_PLAN.md](PINNED_PLAN.md)

## 다음단계 (20260726) — L_ending 1슬롯 교체
- baseline 0.803 → **ending_r1 0.810** (+0.006, 소폭) · 2개 교체/풀top6은 악화
- 벤치: `hybrid_ending_wf_summary.json` · 기본 조립에 반영
- 여전히 oracle best 2.22에 크게 못 미침 → 시드 재설계는 형 승인

## 다음단계2 (20260726) — cover6 + 시드 A/B
- 시드 6종 비교 → **aux 유지** (변경 기각)
- cover6 재조립 최고 ~0.97 vs 최고장 2.50 → **장선택이 병목**
- `cover6_deep_seed_ab.json`

## 유사과거 (컨닝금지)
- `tools/scout_similar_past_patterns.py` · 최근20회 샘플 avg 유사과거 ~30.2 · top15∩actual ~1.8  
- 검색·past_next는 **target 이전만**
