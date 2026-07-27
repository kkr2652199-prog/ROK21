# K-B BENCH SSOT 고정·기계검증 — 보고서

📅 2026-07-28 KST · HEAD `(커밋 전)` · SSOT=ROK21

## 목표

K-B(표본 2종 충돌)를 **프로토콜+검증 스크립트**로 닫는다.  
실력 비교 SSOT = `testlotto_brain_review` 전세트 mean. `lotto_predictions`는 UI/캐시만.

## 검증 (`20260727_KB_bench_ssot.json`)

| 게이트 | 결과 |
|--------|------|
| verify_pass | **true** |
| review 창 100회 완결 | 뇌당 **100** |
| pred 희소 | review보다 **적음** |
| pred 갭 1149–1179 | **31회 전부 부재** |
| 교집합 세트 동일 | **0** (stat 샘플) |
| null mean | **0.8** |
| mean 단독 승자선언 | **금지**(프로토콜) |

## 도구

```powershell
python tools/_kb_bench_ssot_verify.py
```

## 함의

- K-A 패치 전제(비교 프로토콜) **충족** — 단 K-A 자체 패치는 별도 형 지시
- K-C/K-N(best→referee)는 **HOLD** 유지
- 적중↑·서열 승자 선언 아님

## 다음

`K-AWAIT` — 후보: 1235 루프 · K-D 문서정합 · K-H 죽은 AUX
