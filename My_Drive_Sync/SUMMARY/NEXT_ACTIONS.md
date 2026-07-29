# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-ATTACK-HOLD
- 할일: V2 pin ge3=0.1447 유지 · E3 PATTERN-HINT-03 survey는 형 GO 후 · coordinator/AUX/window hint 배선 금지
- 완료조건: 형 지정 축 대기 또는 E3 GO
- 승인필요: 예
- 선행완료: 2026-07-30 (K-WINDOW-SIGNAL-01 FAIL — best w4_zone_mix@α=0.1 ge3=0.1328 p=0.023 · pin 미달)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- V2 pin ge3=0.1447 · mean=1.7504 (stored)
- **K-WINDOW-SIGNAL-01** — 4/8/12/52/all×4signal×α · n=1182 seed=42 · best ge3=0.1328 · `20260729_KWINDOW_SIGNAL_SURVEY.md`
- **K-POSTMORTEM-SIGNAL-02** — ge3+ bin lift 미약(odd=2 +0.031) · E3 단일bin 의존 비권장 · `20260729_KPOSTMORTEM_SIGNAL02.md`
- **K-AUX-SIGNAL-01** — best miss_pattern@α=0.2 ge3=0.1303 p=0.042 · pin 미달
- **4AUX_FEEDBACK_REVIEW** — 4보조=채점 · set_no_asc AUX 컷 없음 · `reports/20260729_4AUX_FEEDBACK_REVIEW.md`
- K-BENCH-01 **SIGNAL_FOUND** — 쿼터갭43.6%·markov best 52.5% · AUX↔hit 무상관
- K-BENCH-02 **FAIL** — baseline ge3=0.1100 최고 · confidence/AUX 정렬 하회
