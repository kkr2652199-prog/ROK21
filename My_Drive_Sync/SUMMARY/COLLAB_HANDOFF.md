# COLLAB_HANDOFF — 형·동생·커서 협업 (1235 루프)

> **목적:** 외부 AI·형·커서가 같은 그림으로 움직이기.  
> 진입: `EXTERNAL_START.md` → 이 파일 → `NEXT_ACTIONS.md` 1건.

## 역할 (고정)

| 역할 | 담당 | 하지 않는 것 |
|------|------|----------------|
| **형** | 본선 1건 결정 · 승인·동결 해제 | 장문 지시서 작성 |
| **동생(외부AI)** | 짧은 지시서 · OPEN 후보 제안 · 질문 1개 | D:\ROK21 직접 실행·commit |
| **커서** | 코드·DB·verify·보고서·문서 동기 | 형 승인 없는 동결 토큰 수정 |

## 1235 본선 루프 — 5단계 (합의)

| # | 단계 | 담당 | 명령/근거 |
|---|------|------|-----------|
| 0 | **준비 확인** | 커서 | `python tools/_kawait_1235_loop.py` (READ-ONLY) |
| 1 | **수집+팬아웃** | 커서 | lotto4 `collect_latest_forward` → testlotto/hyodo |
| 2 | **1235 채점** | 커서 | `refresh_prediction_scores` + WF review + feedback |
| 3 | **1236 예측** | 커서 | `run_coordinated_prediction(1236)` · prior=1235만 |
| 4 | **3DB·drift 게이트** | 커서 | `_pin_3db_smoke.py` · (선택) `_kpin_close_verify.py` |
| 5 | **보고·NEXT 1건** | 커서 | `reports/` → `커서보고서/` · NEXT 갱신 |

**실행 트리거 (형 1줄):**  
「1235 루프 실행」→ 커서: `python tools/_kawait_1235_loop.py --execute`

## 현재 스냅샷 (20260728 · K-00 후)

| 항목 | 값 |
|------|-----|
| 3DB MAX | **1234** (1235 미발표) |
| API 1235 | **없음** (probe 재확인) |
| 숙제 SSOT | `testlotto_brain_review` · 3698행 · verify_pass |
| predictions 희소 | distinct **122** / review-only **1112** |
| 1235 예측(선행) | **15세트** (stage1) |
| 블로커 | 1235 당첨번호 공개 전 `--execute` 불가 |

## OPEN 후보 (형 선택 · 본선 아님)

| ID | 요지 | 선행 |
|----|------|------|
| K-00 | 과거 예측 숙제 확장 (review 아카이브) | **완료** |
| **K-ANALOG** | 유사 과거 회차·연쇄 분석 (ABC 하이브리드) | **PREP 핀** → `K_ANALOG_COLLAB.md` · 형 1줄 승인 |
| K-02 | 외부 철학 벤치 추가 (명분=WARRANT) | docs/benchmarks README |
| K-05 | 2단계 수학 이식 후보 스캔 (lotto4→testlotto) | K-AWAIT 이후 권장 |

## 협업 규칙 (R37)

1. **수치 SSOT** = `docs/benchmarks/*.json` (BOOT/STATUS는 사본)
2. **NEXT 1건** = `NEXT_ACTIONS.md` 만 (여러 건 나열 금지)
3. **채팅 「간략」** ≠ STATUS·BOOT·reports 압축
4. **동결** = random.choices · _get_draws_before · boost 상한
5. **평가** = 적hit↑ 폐기 · 명분=WARRANT · 3예측+4보조 유지

## 파일 지도

| 용도 | 경로 |
|------|------|
| 루프 스크립트 | `tools/_kawait_1235_loop.py` |
| stage1 원본 | `tools/run_testlotto_stage1_bigdata.py` |
| readiness 벤치 | `docs/benchmarks/20260728_KAWAIT_readiness.json` |
| 명분 | `My_Drive_Sync/SUMMARY/WARRANT.md` |
| 결함 | `My_Drive_Sync/SUMMARY/FINDINGS.md` |

_갱신: K-00 · HEAD=`d88a8ff`_
