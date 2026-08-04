# 젠스파크 압축 복구 패킷 · 2026-08-04

> 형이 젠스파크 채팅에 **§붙여넣기 블록** 전체를 넣으면 과거→현재 흐름 복구.  
> GitHub raw: `EXTERNAL_START.md` → `AI_COLLAB.md` §3·§6 → 이 보고서.

**HEAD(작성 시점):** `27cc41d` (push 후 1커밋 지연 가능 · `git rev-parse`/`EXTERNAL_START` LIVE 우선)

---

## 붙여넣기 블록 (압축 직후용)

```
[ROK21 압축복구 · 2026-08-04 · pin갭진단 직전]

■ SSOT
- Repo: kkr2652199-prog/ROK21 · main · D:\ROK21 · 포트 7021
- kweon(D:\3kweon) 동결 · 쓰기·push·신규작업 금지
- 진입1순위: EXTERNAL_START.md (루트)
- 협업·대화: AI_COLLAB.md §3·§6
- NEXT: My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md
- 수치 SSOT: docs/benchmarks/*.json (기억 금지)

■ 지금 / 다음
- 지금: K-PIN-GAP-DIAG-REVIEW DOC — 젠스파크「K-PIN-GAP-DIAG GO」지시서 구조대조 완료
- 직전: K-IMPROVE-ROADMAP DONE — 권고 I1 pin갭진단 + I3 B1로그 · ultra wire HOLD
- 다음: 수정3건 반영한 K-PIN-GAP-DIAG GO · 또는 로드맵 A/B/C/D 형 선택
- 실행 금지: 수정 전 원본 지시서로 WF/wire 착수

■ live 성적 (확정 · JSON)
| 벤치 | n | ge3 | 비고 |
| FUTURE-WIRE N100 | 100 | 0.1500 | PASS · live |
| FUTURE-WIRE QUICK | 200 | 0.1350 | patch PASS · pin FAIL |
| FUTURE-WIRE FULL | 1182 | 0.1184 | pin 0.1447 · Δ−0.0263 FAIL |
| null best-of-5 | — | 0.1137 | fusion 5장 기준 |
| WIRE-V2 pin | — | 0.1447 | stored |
| quota FULL | — | markov 80% · review 20% · stat 0% | 고착 |

■ FULL by_period (n=각 394 · 「mid 붕괴」아님)
| 구간 | ge3 | vs pin |
| early | 0.0990 | −0.0457 최악 |
| mid | 0.1320 | −0.0127 상대 최선 |
| late | 0.1244 | −0.0203 |

※ N100 기간 n=25/25/50 은 FULL과 다른 창. pin갭 본체 진단은 FULL thirds.

■ K-PIN-GAP-DIAG 지시서 — GO 전 수정 3건 (커서 검토 확정)
1) 기간: FULL n=394 thirds. 「early/mid/late n=25/25/50」「mid 붕괴」문구 삭제
2) READ-ONLY: 1차=기존 JSON 분해. _k_future_wire_revalidate reset·WF는 별도 GO
3) 종료: ROK21 종료5종 + sync_all_resume_docs (EXTERNAL/AI_COLLAB/NEXT/FLOW만으로는 미달)

그 외 OK: 목적(Δ−0.0263) · markov80% · seed=42 · K-M/N 수치확인 · wire/engine/auto-tune/FINDINGS무단 금지

■ 최근 완료 타임라인 (과거→현재)
1. UI 즉시·프리로드 (BT DB 즉시표시)
2. K-BENCH-NULL-BY-EVAL (eval_mode별 null · best15 허위PASS 제거)
3. K-FUTURE-WIRE (+REVAL) live · FULL pin FAIL
4. K-RARE-BUNDLE / APPLY / NESTED — ultra→ge3 wire HOLD
5. K-GS-FACTCHECK — 젠스파크 대체로 PASS · 복귀HEAD 53decde 정정
6. K-IMPROVE-ROADMAP — I1+I3 권고 · ultra HOLD
7. K-PIN-GAP-DIAG-REVIEW — 지시서 구조 불일치 3건 DOC (본 패킷)

■ 로드맵 선택지 (형)
A = I1+I3 GO (수정된 pin갭진단 + B1로그)
B = B2 mild survey
C = pin 회복 패치 시도 (진단 전 비권고)
D = 중기만 (볼/Brier 등)
권고: A · 단 I1은 위 수정3건 반영본

■ 절대 금지
random.choices · _get_draws_before · boost상한 · kweon쓰기
engine/coordinator wire(GO없이) · FINDINGS무단 · FAIL→auto-tune · 1~3군기록

■ 젠스파크 할 일 (압축 복귀 후)
1. EXTERNAL_START.md + 이 블록으로 상태 확인
2. 수정3건 반영한 K-PIN-GAP-DIAG 지시서 재작성(또는 형에게 확인 질문 1개)
3. GO 없이 코드·백테·wire 금지
4. 첫줄: [복귀] HEAD=<EXTERNAL_START실측> · 지금=K-PIN-GAP-DIAG-REVIEW · 다음=수정GO/형선택
```

---

## 파일 지도 (권한 있을 때)

| 용도 | 경로 / raw |
|------|------------|
| LIVE | `EXTERNAL_START.md` |
| 협업+§6패킷 | `My_Drive_Sync/SUMMARY/AI_COLLAB.md` |
| NEXT 1건 | `My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md` |
| 흐름 | `My_Drive_Sync/SUMMARY/FLOW_BRIEF.md` |
| 로드맵 | `reports/20260804_IMPROVEMENT_INVESTIGATION_ROADMAP.md` |
| FULL JSON | `docs/benchmarks/20260803_KFUTURE_WIRE_FULL.json` |
| N100 JSON | `docs/benchmarks/20260803_KFUTURE_WIRE_N100.json` |

---

## 커서 측 복귀 (이 레포)

1. `EXTERNAL_START.md` LIVE + `BOOT.md` §1  
2. `NEXT_ACTIONS.md` → `K-PIN-GAP-DIAG-WAIT`  
3. 수치는 JSON만 · 수정 전 지시서로 실행 금지  
