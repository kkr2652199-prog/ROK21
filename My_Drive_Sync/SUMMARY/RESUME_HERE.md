# RESUME_HERE — 테스트로또 복원 앵커 (kweon)

> 매 작업 push 시 이 파일을 최신화한다. 압축 복원용 단일 진입점.

## 지금 어디까지

**A배선 완료** — `predict_statistical.py` learn_state→weights 연결 + `predict_stat_fairy.py:43` conf 버그 수정.
1132~1231 stat WF: 배선 전 avg **1.70** → 배선 후 **1.63** (동일 시드·1131 스냅샷). freq 연결은 **동작 확인**, 100회 성적은 **소폭 하락**.
백업: `backups/20260718_테스트뇌_배선전/` (SHA `fae01f67…`).

## 살아있는 진실 (헷갈림 방지)

- 예측뇌 = `brains/predict_stat_fairy.py` 등 · 내부 엔진 = `predict_statistical.py` / `predict_markov.py`
- **stat 배선**: `load_learn_state` → overdue/ending/carry → weights 재정규화 (`predict_statistical.py` 피드백 블록 직후)
- **흐름술사** = 아직 미연결 · **random.choices** = B단계(미착수)
- 데이터: `brain_review`(max 1231) ≠ `lotto_predictions`(max 1232)
- R34: memoy=1~3군 · kweon=4군/테스트로또

## 통계요정 배선 지점 (확정 → 적용됨)

- 적용 위치: `_statistical_predict` — `get_feedback_summary` 직후 / `results=[]` 직전
- 보고서: `My_Drive_Sync/커서보고서/20260725_A배선_전후성적비교.md`
- JSON: `backups/20260725_배선전_성적.json`, `배선후_성적.json`

## 다음 한 걸음

- **흐름술사(markov)** learn_state→weights 배선 (stat과 동일 패턴) **또는** stat boost 강도(0.5 상한) 재검토.
- B단계: `random.choices` 결정론/시드 (별 지시).
