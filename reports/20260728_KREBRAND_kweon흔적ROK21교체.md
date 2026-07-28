# K-REBRAND — kweon 흔적 ROK21 교체

**일자:** 20260728  
**HEAD:** `440eb18`  
**범위:** 앱 UI·런타임·검증 도구·SSOT 진입 문서 (DB·과거 reports 제외)

---

## 요약

사용자-facing 문구·브랜딩에서 kweon/복제/「지식 도서관」 흔적을 제거하고 **ROK21 독립 SSOT** 정체성으로 통일.

---

## 변경 파일 (18)

| 구분 | 파일 | 내용 |
|------|------|------|
| UI | `app/static/index.html` | 타이틀·브랜드·효도/테스트로또 힌트 |
| UI | `app/static/testlotto-detail.html` | 상세页 타이틀 |
| JS | `hyodo.js` · `testlotto.js` · `lotto4.js` | 카톡 복사 헤더 ROK21 |
| 패키지 | `app/hyodo/__init__.py` · `app/testlotto/__init__.py` | docstring |
| 서버 | `run_v13.py` | kweon 비교 문구 제거 |
| tools | `verify_*.py` ×3 | API **6124→7021** |
| tools | `*_pipeline.json` 등 | `D:\3kweon` → `D:\ROK21` |
| SSOT | `README_START.md` · `RESTORE.md` §A | 독립 SSOT 한 줄 |

---

## 미포함 (의도)

- `reports/` 과거 보고서 · `.cursor/rules/kweon-core.mdc` (동결 규칙)
- `v13_*` brain_tag (DB 식별자)
- `data/*.db` 워킹트리 변경 (본 커밋 제외)

---

## 후속

- **K-REVIEW-RUN:** `brain_review` 1~1234 walk-forward 재복습 (숫자 SSOT)
- **K-AWAIT:** 1235 발표 후 execute
