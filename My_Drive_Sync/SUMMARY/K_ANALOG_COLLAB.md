# K-ANALOG — 협업 회의 핀 (형·동생·커서 · 2차 반영)

> **상태:** PREP **완료** · **K-ANALOG-1 PATCH = Go** (다음 턴 구현)  
> **NEXT 유지:** K-AWAIT (1235 `--execute`)  
> **갱신:** 20260728 · PREP bench `20260728_KANALOG_prep.json`

---

## 0) 2차 회의 한 줄

PREP 1234 실측 **conditional_go=true** → 동생 **조건부 Go** 충족 → **K-ANALOG-1**(API+상세页) 착수 OK. K-ANALOG-2(예측 힌트)는 K-AWAIT 이후.

---

## 1) ABC 하이브리드 (1차+2차 확정)

```
[1단 A] 겹침 ≥ 2/6
[2단 B] pattern_sim ≥ 0.85 (구제) · L1 norm_spec 고정
[합산] score = 0.55*jaccard + 0.45*pattern_sim → TOP-15
[3단 C] 직전 W=8 · analog+1 관측(예측 아님)
```

**norm_spec SSOT:** `tools/_kanalog_probe.py` · `NORM_SPEC` · bench JSON 동기

---

## 2) PREP 실측 (1234)

| 지표 | 값 |
|------|-----|
| candidate_total | 386 |
| b_only_ratio | 0.451 |
| overlap2_plus | 212 |
| top1 | 793회 · overlap 3 |
| patch_gate | **PASS** |

명령: `python tools/_kanalog_probe.py 1234`

---

## 3) UI 면책 (2차 고정 · 변경 금지)

> 역사 유사 장면 · 설명용 · 1등 확률을 높이지 않음 · next_draw는 해당 analog 회차의 실제 다음 추첨(관측)이며 1235 예측 아님

---

## 4) K-ANALOG-1 패치 범위 (다음 턴)

- `analog_service.py` + `GET /api/testlotto/analog/draw/{n}`
- `testlotto-detail.js` 섹션 1개
- `tools/_kanalog_verify.py`
- **미포함:** coordinator · WF · boost · random.choices

---

## 5) 문서 지도

| 용도 | 경로 |
|------|------|
| 패치 보고서 | `reports/20260728_KANALOG_패치보고서.md` |
| 1차 회의록 | `reports/20260728_KANALOG_협업회의.md` |
| PREP bench | `docs/benchmarks/20260728_KANALOG_prep.json` |
| OPEN | `COLLAB_HANDOFF.md` |

---

_2차 회의 동생 ID: 842cba7b · 커서 PREP 실측 20260728_
