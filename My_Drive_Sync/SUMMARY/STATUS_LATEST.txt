# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-26 KST (Vote≥2 메타 WF + 유사과거)

## git / 원격
- `D:\ROK21` · `kkr2652199-prog/ROK21` · 원본 kweon **미접촉**
- 규칙: 말 없어도 **commit+push로 히스토리 저장**

## 형 계획 (병행)
- 5세트×N뇌 풀 → 메타 재조립 · 과거 유사패턴 · 컨닝금지
- Vote≥2 tools WF **완료** → 단독 기각 · 하이브리드 다음

## 실측 (Vote≥2)
- avg Vote≥2 **0.79** vs best세트 **2.22** (n=1233)
- oracle 풀 cover **4.87** (상한) · vote2 beats best **4회만**
- 유사과거 스카우트(최근20): 유사~30.2 · top15∩actual ~1.8

## 산출물
- `tools/run_meta_vote2_wf.py` · `tools/scout_similar_past_patterns.py`
- `docs/benchmarks/20260726_형계획_세트합집합_메타선별/`

## 다음
- best세트 시드 + Vote 하이브리드
- cover=6 선별 규칙
- 유사렌즈 swarm (역할분담 A/B)

## 최신 보고서
- `reports/20260726_ROK21_Vote2메타_유사과거.md`
