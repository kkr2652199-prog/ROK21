# RESUME_HERE — 테스트로또 복원 앵커 (kweon)

> 매 작업 push 시 이 파일을 최신화한다. 압축 복원용 단일 진입점.

## 지금 어디까지

테스트로또 예측 3뇌+보조4뇌. 배선 전 백업(`backups/20260718_테스트뇌_배선전/`, SHA `fae01f67…`) 완료.
**20260725 READ-ONLY 실동작 진단 완료** — 결정론(비결정론 확인)·learn_state(freq 미연결 실측)·3뇌 정상·review≠predictions 확인.
통계요정 배선 지점 코드레벨 확정. **코드 수정 아직 0건.**

## 살아있는 진실 (헷갈림 방지)

- 실제 예측뇌 = `brains/predict_stat_fairy.py` `predict_flow_shaman.py` `predict_review_king.py`
- 내부 엔진 = `predict_statistical.py`(freq·random.choices), `predict_markov.py`
- 배선 현황: 복습왕=연결됨 · 통계요정=**freq 미연결 실측**(adj 0.5 DB 존재, 번호=base 동일) · 흐름술사=미연결
- 데이터: 상세=`testlotto_brain_review`(max 1231) ≠ 예측잔존=`lotto_predictions`(max 1232, 83회차만)
- R34: 1~3군=memoy · 4군/테스트로또=kweon

## 통계요정 배선 지점 (확정)

- **문제**: `predict_stat_fairy`가 base 번호 그대로 쓰고 adj는 reasoning만 (`실동작진단 20260725` 참조).
- **해결 위치**: `predict_statistical.py` `_statistical_predict` — 피드백 블록 다음 / `results=[]` 직전 (`174-177`).
- **추가**: `load_learn_state("stat")` → overdue/ending/carry boost → weights 재정규화.

## 다음 한 걸음

- 백업 확인 후 **`predict_statistical.py` learn_state→weights 배선 적용** (코드 1파일).
- 적용 후 walk-forward 재측정(별 지시) — 이번 READ-ONLY 진단에서는 WF·DB 쓰기 안 함.
- 흐름술사 배선은 stat 다음.
