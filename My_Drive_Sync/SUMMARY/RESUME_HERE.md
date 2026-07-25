# RESUME_HERE — 테스트로또 복원 앵커 (kweon)

> 매 작업 push 시 이 파일을 최신화한다. 압축 복원용 단일 진입점.

## 지금 어디까지

테스트로또(`app/testlotto/`) 예측 3뇌(통계요정·흐름술사·복습왕)+보조4뇌 구조.
배선 수정 **착수 직전** — 전체백업(`backups/20260718_테스트뇌_배선전/`, SHA `fae01f67…`) 완료.
통계요정 배선 지점 **코드레벨 확정 완료**(아래 참조). 아직 코드 수정 0건.

## 살아있는 진실 (헷갈림 방지)

- 실제 예측뇌 = `brains/predict_stat_fairy.py` `predict_flow_shaman.py` `predict_review_king.py`
- 내부 엔진 = `predict_statistical.py`(freq 계산·번호추출), `predict_markov.py`
- 배선 현황: 복습왕=연결됨 · 통계요정=신뢰도만(freq 미연결) · 흐름술사=미연결
- R34: 1~3군=memoy(`D:\MONEY lol`) · 4군/테스트로또=kweon(`d:\3kweon`)

## 통계요정 배선 지점 (확정)

- **문제**: `predict_stat_fairy.predict_sets`가 `_statistical_predict`로 번호를 먼저 확정한 뒤,
  learn_state 조정값을 confidence·reasoning에만 씀 → 번호선택에 미반영.
  - 근거: `predict_stat_fairy.py:14-43` (base=`_statistical_predict`, adj는 conf/reasoning만)
- **해결 위치**: `predict_statistical.py`의 `_statistical_predict` 안,
  피드백 반영 블록(`get_feedback_summary`) **바로 다음 / `results=[]` 직전** (`174-177`행).
  이미 freq/weights에 overdue×1.3/1.15, hot×1.2, 피드백 ×0.8/1.15 곱셈 hook 존재 → 여기 learn_state 3줄 추가.
- **추가할 것** (READ-ONLY 해제 후):
  1. `load_learn_state("stat")` 호출로 adjustments 로드
  2. overdue_boost → gap≥30 번호 freq에 곱
  3. ending_digit_boost → 끝수별 freq에 곱, carry_over_boost → 직전회차 번호 freq에 곱
  4. 곱한 뒤 weights 재정규화(sum=1.0) 유지

## 다음 한 걸음

- 위 배선 실제 적용(백업 확인 후) → walk-forward 재측정 → freq 반영 전후 성적 비교.
- 흐름술사(markov)는 그다음. DB 수정·백테 컨닝 금지.
