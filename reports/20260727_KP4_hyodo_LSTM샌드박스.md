# K-P4 hyodo LSTM 재학습 샌드박스 — 보고서

📅 2026-07-27 KST · HEAD `(커밋 전)` · SSOT=ROK21

## 목표

효도로또(hyodo) LSTM **재학습·체크포인트 격리** 샌드박스. 적중↑ 목표 아님 · PMF·as_of·프로덕션 ckpt 무침범 검증.

## 변경

| 파일 | 내용 |
|------|------|
| `app/hyodo/predict_lstm.py` | `ROK21_HYODO_LSTM_SANDBOX` · `resolve_ckpt_path()` · `reset_lstm_runtime()` · `lstm_runtime_status()` · `ROK21_LSTM_EPOCHS` |
| `app/hyodo/routes.py` | `GET /api/hyodo/lstm/status` (READ-ONLY) |
| `tools/_kp4_hyodo_lstm_sandbox.py` | as_of=1235 컷오프 검증 → 벤치 JSON |

**동결 유지:** `_get_draws_before` · fusion/engine 배선 미변경.

## 샌드박스 사용법

```powershell
$env:ROK21_HYODO_LSTM_SANDBOX='1'
$env:ROK21_LSTM_EPOCHS='8'   # 선택 · 기본 30
python tools/_kp4_hyodo_lstm_sandbox.py
```

- 체크포인트: `models/_kp4_sandbox/lstm_hyodo.pt`
- 프로덕션: `models/lstm_hyodo.pt` (검증 시 mtime 불변)

## 검증 (`20260727_KP4_hyodo_lstm.json`)

| 체크 | 결과 |
|------|------|
| verify_pass | **true** |
| draw_count (as_of 1235) | 1234 |
| PMF sum | 1.0 |
| PMF spread (non-uniform) | 0.0135 |
| sandbox ckpt | 작성됨 · trained_len=1234 |
| prod ckpt | **미변경** |
| cutoff_changes_pmf | short(130) vs full top1·spread 상이 |

device: cuda (로컬 실측)

## 명분

- K-S as_of 컷오프와 정합: `_get_draws_before(AS_OF)` 만 학습·추론 입력.
- WF 전체·적중 백테는 본 턴 범위 외.

## 다음

`K-PIN-CLOSE` — P1~P4 스택 마감 · drift·3DB 재스모크 (형 지시 시).
