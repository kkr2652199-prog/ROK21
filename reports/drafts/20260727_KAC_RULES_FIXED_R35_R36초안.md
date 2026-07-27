# [초안 · 형 승인 대기] RULES_FIXED.md — R35 · R36

📅 초안: 2026-07-27 · K-AC · **형이 RULES_FIXED.md에 직접 추가할 때만 유효. 커서/동생 미적용.**

---

## R35 (NEW 동생 복원 규칙)

- 동생(Claude)은 **압축 후 첫 턴**에 아래를 **반드시** 읽는다 (순서 고정):
  1. `RESTORE.md`
  2. `BOOT.md`
  3. `FINDINGS.md`
  4. `CURSOR_RULES.md` §6 (현행 뇌 체계)
- **읽기 전 지시서 작성 금지.**
- 지시서의 **모든 수치**에 출처파일 병기 (`docs/benchmarks/*.json` · DB실측 · FINDINGS ID).
- 지시서에 없는 값 **추정 금지.** 불확실하면 **"미확인"**으로 형에게 질문.
- (참고) 구 R33의 kweon/README_START 복원 경로는 **ROK21 작업에 쓰지 않는다.** ROK21=RESTORE 우선. R33 개정은 형 별도 결정.

## R36 (NEW 문서 SSOT 충돌)

| 종류 | 원본 (이김) | 사본 (짐) |
|------|-------------|-----------|
| 수치 | `docs/benchmarks/*.json` (+ DB 실측) | BOOT §2 · STATUS · RESTORE C · RESUME_HERE |
| 결함 상태 | `FINDINGS.md` | BOOT §3 · RESTORE E · STATUS 요약 |
| 명분 라벨 | `WARRANT.md` | `brains/warrant.py` · 보고서 재서술 |

- 충돌 시 **원본이 이긴다.** 사본은 원본에 맞춰 고친다.
- 드리프트 검사: `tools/_doc_drift_check.py` (자동수정 금지 · 보고만).
