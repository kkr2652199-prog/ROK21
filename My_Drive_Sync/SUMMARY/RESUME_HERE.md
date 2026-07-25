# RESUME_HERE — 테스트로또 복원 앵커 (kweon)

> 매 작업 push 시 이 파일을 최신화한다. 압축 복원용 단일 진입점.

## 현재 성적 기준선 (숫자로 박제)

- **stat (회차별 seed, 1132~1231)**: 0.5³ **1.71** → 추천 0.2/0.3/0.2 **1.75** (+0.04)
- **stat (회차별 seed, 2~1231)**: 0.5³ **1.6724** → 추천 **1.7171** (역산 그리드 **완전 재현**)
- **구 seed(1회) 1132~1231**: 0.5³·추천 모두 **1.63** — 측정 프로토콜 문제(폐기)
- **백업(재기록전)**: `backups/20260725_재기록전_DB전체/` · predictions 1245
- **HEAD**: (이번 push) · 배선전 백업 `fae01f67`

## 절대 건드리지 말 것 (금지 목록)

- `random.choices` (`predict_statistical.py:187-188`) — **B단계 전 수정 금지**
- **DB·learn_state 직접 수정 금지** (측정은 READ-ONLY monkeypatch)
- **백테 컨닝 금지** (`_get_draws_before`: target 이전 draws만)
- R34: memoy=1~3군 · kweon=4군/테스트로또

## 다음 한 걸음

- **4단계**: boost 효과 확인됨 → `lotto_predictions` DELETE + walk-forward 재기록 (백업 선행 유지)
- WF 3단계 재측정 시 seed **회차별** (`20260725+draw×9973`) 필수
- boost 상한: `learn_state.py` BOOST_CAPS · `predict_statistical.py` clamp
- 보고서: `20260725_seed정렬_boost재검증.md`
