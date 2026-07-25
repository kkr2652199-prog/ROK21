# RESUME_HERE — 테스트로또 복원 앵커 (kweon)

> 매 작업 push 시 이 파일을 최신화한다. 압축 복원용 단일 진입점.

## 현재 성적 기준선 (숫자로 박제)

- **boost 상한**: carry=0.2, ending=0.3, overdue=0.2 (`learn_state.py` + `predict_statistical.py` clamp)
- **stat 동적 WF (1132~1231, 회차별 seed)**: avg **1.75** — apply_feedback 경로 확인
- **stat 고정 boost (회차별 seed)**: 0.5³ 1.71 → 추천 1.75 (1132~1231) · 전구간 1.6724→1.7171
- **lotto_predictions**: **1,245행** · 83회차(3, 1120~1232 일부) · stat/markov/review 각 415 — **20260725 재기록 완료**
- **백업**: `backups/20260725_재기록전_DB전체/` · 배선전 `fae01f67`

## 절대 건드리지 말 것 (금지 목록)

- `random.choices` (`predict_statistical.py:187-188`) — **B단계 전 수정 금지**
- **백테 컨닝 금지** (`_get_draws_before`: target 이전 draws만)
- R34: memoy=1~3군 · kweon=4군/테스트로또

## 다음 한 걸음

- **B단계(선택)**: stat 결정론화 — `random.choices` → 시드 고정 샘플링 또는 대체
- UI에서 1232 stat 5세트·재기록 predictions 정상 노출 확인
- 보고서: `20260725_예측_초기화_재기록_완료.md`
