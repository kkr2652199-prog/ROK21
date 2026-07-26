# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-26 KST (cover6 심층 + 시드 A/B)

## PIN 메타
- 시드=보조4뇌 **유지** (vote/conf/ending/hist/overlap 전부 열세)
- 끝자리 1칸 교체 유지 · avg **0.81** ≪ 최고장 **2.22**
- cover6에서 번호 재조립 최고 ~0.97 vs 그 회차 최고장 **2.50** → **장선택이 병목**

## 산출
- `tools/run_cover6_deep_and_seed_ab.py`
- `cover6_deep_seed_ab.json`

## 다음
- 15장 중 장선택 규칙 학습 (과거 피처만, 컨닝금지)

## 최신 보고서
- `reports/20260726_ROK21_cover6시드비교.md`
