# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-UI-HOLD-OFF-DONE
- 할일: **UI HOLD 해제 완료** — `ROK21_TESTLOTTO_FOCUS_HOLD=false` · 두뇌예측·전략X·효도 다시 표시. 하드 리로드(Ctrl+F5) 후 탭 확인. 형 1건 — **①군중 BLEND 소튜닝** / ②1235 명분리뷰 / ③정지
- 완료조건: 형이 ①~③ 중 1건 지정 (또는 UI 확인만)
- 선행완료: app/static/js/lotto4.js · docs/benchmarks/20260808_KUI_TESTLOTTO_FOCUS_HOLD_OFF.json
- 승인필요: 없음
- 선행조건: 없음
- 최종갱신: 2026-08-10


## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- 재홀딩: `lotto4.js` → `ROK21_TESTLOTTO_FOCUS_HOLD = true`
