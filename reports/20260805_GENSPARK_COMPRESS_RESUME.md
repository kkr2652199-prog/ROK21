# 젠스파크 세션 압축 복구 — 운영 가이드 (2026-08-05)

## 문제

젠스파크가 세션을 **압축**하면, 보고서를 읽고 쓴 긴 분석이 채팅 안에서 유실·왜곡된다.  
압축 직후 에이전트가 “보고서를 반영했다”고 해도 **신뢰할 수 없다**.

## 해결 (ROK21)

| 층 | 파일 | 역할 |
|----|------|------|
| LIVE | `EXTERNAL_START.md` | HEAD·지금·NEXT 1건 |
| **압축복구** | `My_Drive_Sync/SUMMARY/GENSPARK_COMPRESS_RECOVER.md` | 붙여넣기 블록 + **증거체인 raw URL** (R37 자동) |
| 대화 | `AI_COLLAB.md` §3 | 최근 판정 요약 |
| 수치 | `docs/benchmarks/*.json` | 유일한 숫자 SSOT |

## 형 30초 절차

1. `GENSPARK_COMPRESS_RECOVER.md` 전체 붙여넣기  
2. `EXTERNAL_START.md` 같이 첨부(404면 붙여넣기)  
3. 지시: 채팅기억 폐기 → 증거체인 JSON fetch → `[복귀]` + 팩트체크 표  
4. 압축 전 장문과 다르면 **JSON 승**

## 추가 아이디어 (반영·권고)

- **세션 지문:** 매 답 첫줄 `[복귀] HEAD=…` — HEAD가 안 맞으면 압축/구버전 감지  
- **이중 붙여넣기:** 짧은 LIVE + RECOVER 증거체인  
- **불신 선언 템플릿:** `압축감지: 채팅기억 폐기 · JSON 재페치 시작`  
- **보고서≠수치:** MD는 해설, 판정은 JSON만  
- **매 push 자동갱신:** `sync_all_resume_docs()`에 `genspark_recover` 포함  

## 금지

수치를 채팅 기억으로 인용 · wire/GO 없이 엔진 변경 · kweon 접촉
