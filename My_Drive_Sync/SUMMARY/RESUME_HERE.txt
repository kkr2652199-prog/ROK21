# RESUME_HERE — 테스트로또 복원 앵커 (kweon)

> 매 작업 push 시 이 파일을 최신화한다. 압축 복원용 단일 진입점.

## 현재 성적 기준선 (숫자로 박제)

- **stat 평균 적중**: 배선전 **1.70** → 배선후 **1.63** (구간 **1132~1231**, 100회, seed=20260725)
- **원인(가설)**: adj 6키 전부 **0.5 상한** → 과보정(over-boost)
- **현재 HEAD**: `555a11f` / **백업**: `fae01f67` (`backups/20260718_테스트뇌_배선전/`)
- **A배선 코드**: `predict_statistical.py` learn_state→weights · `predict_stat_fairy.py:43` conf 수정

## 절대 건드리지 말 것 (금지 목록)

- `random.choices` (`predict_statistical.py:187-188`) — **B단계 전 수정 금지**
- boost 상한 **0.5** = 튜닝 대상이지 고정값 아님
- **DB·learn_state 직접 수정 금지** (measure 스크립트는 측정 후 원복 필수)
- **백테 컨닝 금지** (`_get_draws_before`: target 이전 draws만)
- R34: memoy=1~3군 · kweon=4군/테스트로또

## 다음 한 걸음

- **추천 boost 적용** (역산 1위): `carry=0.2, ending=0.3, overdue=0.2` — `apply_feedback` 상한 0.5 튜닝 또는 배선 테스트
- 적용 후 WF 재측정 (1132~1231, seed=20260725, 1131 스냅샷)
- 역산 보고서: `My_Drive_Sync/커서보고서/20260725_stat_boost_최적값_역산.md` · JSON: `backups/20260725_boost_grid.json`
- 현재 0.5³ = **124/125위** (avg 1.6724) — 과보정 실측
