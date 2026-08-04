# GENSPARK_COMPRESS_RECOVER — 젠스파크 세션 압축 복구 SSOT

> **압축되면 채팅 기억 버리고 이 파일 + EXTERNAL_START만 신뢰.**
> 형 큐: `동생, GENSPARK_COMPRESS_RECOVER 붙여넣을게. JSON만 다시 읽어.`
> 자동생성 HEAD=`eab094f` · R37 `sync_all_resume_docs()`

## 0) 왜 필요한가

- 젠스파크가 세션 압축하면 긴 분석·보고서 해석이 **유실/왜곡**될 수 있다.
- 압축 직후 에이전트가 '보고서를 읽었다'고 해도, 그 내용은 **신뢰 불가**.
- 복구 = **GitHub raw 재페치** + 아래 붙여넣기 블록.

## 1) 형 → 젠스파크 30초 복구 절차

1. 이 파일(또는 아래 ``` 블록) 전체를 채팅에 붙여넣기
2. `EXTERNAL_START.md` raw도 함께 첨부(404면 붙여넣기)
3. 에이전트에게: **증거 체인 JSON을 fetch한 뒤 [복귀] 한 줄 + 팩트체크 표**
4. 압축 전 장문과 다르면 JSON을 따르고, 틀린 기억은 명시적으로 폐기 선언

## 2) 붙여넣기 블록 (자동)

```
[ROK21 젠스파크 압축복구 · HEAD=eab094f]

■ 신뢰 규칙 (필수)
- 압축된 채팅 기억·긴 요약 = **불신**. 수치·판정은 아래 raw URL JSON만.
- 보고서 '읽었다'고 말해도 JSON을 다시 fetch하기 전엔 확정 금지.
- 당첨P↑·wire GO·quota 변경 = 형 명시 승인 전 금지.

■ LIVE
- HEAD: eab094f · WORK=IDLE · SSOT=ROK21/7021
- 지금: **K-COVER-DIAG** — 중복+cold-free · **NORMAL/IMPROVE**
- 직전: K-COLD-EXCLUDE-DIAG
- BOOT다음: 각도3(early) · **형 GO**
- NEXT1: K-COVER-DIAG-DONE — covering 진단 완료 · 결과 확인 · **각도3(early 취약성) 진행**
- kweon(D:\3kweon) 동결 · 1~3군 미기록

■ 증거 체인 (반드시 재페치)
- `20260805_KCOVER_DIAG` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260805_KCOVER_DIAG.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260805_KCOVER_DIAG.md
- `20260805_KCOLD_EXCLUDE_DIAG` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260805_KCOLD_EXCLUDE_DIAG.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260805_KCOLD_EXCLUDE_DIAG.md
- `20260805_KEMA_MARKOV_DIAG` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260805_KEMA_MARKOV_DIAG.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260805_KEMA_MARKOV_DIAG.md
- `20260805_KREVIEW_QUOTA_SIM` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260805_KREVIEW_QUOTA_SIM.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260805_KREVIEW_QUOTA_SIM.md
- `20260805_KSTAT_SEED_DIAG` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260805_KSTAT_SEED_DIAG.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260805_KSTAT_SEED_DIAG.md
- `20260805_KQUOTA_D_WIRE` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260805_KQUOTA_D_WIRE.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260805_KQUOTA_D_WIRE.md
- `20260805_KPATCH_1235_PREP` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260805_KPATCH_1235_PREP.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260805_KPATCH_1235_PREP.md
- `20260805_KPATTERN_BC_MEASURE` → https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260805_KPATTERN_BC_MEASURE.json
  - report: https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/20260805_KPATTERN_BC_MEASURE.md

■ 진입 파일
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/EXTERNAL_START.md
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/GENSPARK_COMPRESS_RECOVER.md
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/AI_COLLAB.md
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/FLOW_BRIEF.md

■ 복구 후 할 일
1. 첫줄: [복귀] HEAD=eab094f · 지금=**K-COVER-DIAG** — 중복+cold-free · **NORMAL/IMPROVE** · 다음=K-COVER-DIAG-DONE
2. 위 JSON 중 지금 ID 관련 1~2개 fetch → 표로 팩트체크
3. 압축 전 장문과 불일치하면 **JSON 승** · 채팅 기억 폐기
4. 승인 없으면 장문 지시서 금지 · 질문 1개

■ 금지
random.choices · _get_draws_before · boost상한 · kweon쓰기
engine wire(GO없이) · auto-tune · 채팅기억으로 수치 인용
```

## 3) 추가 아이디어 (운영)

| 아이디어 | 설명 |
|----------|------|
| 이중 붙여넣기 | 짧은 LIVE(EXTERNAL_START) + 이 RECOVER 증거체인 |
| 세션 지문 | HEAD+지금ID를 매 답 첫줄에 강제 → 압축 감지 |
| 불신 선언 템플릿 | `압축감지: 채팅기억 폐기 · JSON 재페치 시작` |
| 보고서≠수치 | MD는 해설, 판정·숫자는 항상 `docs/benchmarks/*.json` |
| 커서 동시갱신 | 매 push 후 sync가 이 파일을 갱신(본 자동화) |
| 드라이브 사본 | `My_Drive_Sync/커서보고서`의 동명 MD도 교차확인 |

## 4) 파일 지도

| 용도 | raw |
|------|-----|
| 본 복구 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/GENSPARK_COMPRESS_RECOVER.md` |
| LIVE | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/EXTERNAL_START.md` |
| 대화요약 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/AI_COLLAB.md` |

_generated: eab094f_
