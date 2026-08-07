# K-BRAIN-RENAME-STAT — 통계요정 → 과거학습 (2026-08-08)

- **판정:** `PASS` · tag=`stat` 유지 · 표시명만 변경
- 신규 method/UI: **과거학습**
- 구명칭 `통계요정` → `METHOD_TO_TAG` 호환 유지 (DB 잔존 method)

## 변경 파일
- `app/testlotto/brains/registry.py`
- `app/testlotto/brains/stat_brain/predict.py`
- `app/testlotto/brains/predict_stat_fairy.py`
- `app/static/js/testlotto.js` · `testlotto-detail.js`
- 도구 BRAIN_KO / STEP4 smoke 호환

## 비변경
- brain_tag=`stat` · engine/quota/WIRE · 과거 벤치 JSON 본문(역사 기록)
