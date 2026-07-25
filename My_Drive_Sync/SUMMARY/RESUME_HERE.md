# RESUME_HERE — 테스트로또 복원 앵커 (kweon)

> 매 작업 push 시 이 파일을 최신화한다. 압축 복원용 단일 진입점.

## 현재 성적 기준선 (숫자로 박제)

- **stat 평균 적중 (1132~1231, seed=20260725 1회)**: 배선전 **1.70** → A배선(0.5³) **1.63** → boost상한적용 후 **1.63** (개선 없음)
- **역산 그리드 (회차별 seed, 2~1231)**: 0.5³ **1.6724** → 추천 0.2/0.3/0.2 **1.7171**
- **백업(재기록전)**: `backups/20260725_재기록전_DB전체/` · review 3689 · predictions 1245
- **A배선+boost코드 HEAD**: (이번 push) · **배선전 백업**: `fae01f67`

## 절대 건드리지 말 것 (금지 목록)

- `random.choices` (`predict_statistical.py:187-188`) — **B단계 전 수정 금지**
- **DB·learn_state 직접 수정 금지** (measure 스크립트는 측정 후 원복 필수)
- **백테 컨닝 금지** (`_get_draws_before`: target 이전 draws만)
- R34: memoy=1~3군 · kweon=4군/테스트로또

## 다음 한 걸음

- **3단계 재검증**: `_measure_stat_wf_range.py` seed를 역산과 동일(`20260725+draw×9973`)으로 정렬 후 1132~1231 재측정
- **통과 기준**: avg **> 1.67** (이번 1.63으로 4단계 재기록 **중단됨**)
- boost 상한 코드 적용됨: `learn_state.py` BOOST_CAPS · `predict_statistical.py` clamp
- 보고서: `My_Drive_Sync/커서보고서/20260725_boost적용_재기록_결과.md`
