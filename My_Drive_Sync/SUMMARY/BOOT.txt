# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
ROK21 = kweon 원본 복사본. 4군+테스트로또+효도로또. SSOT=`kkr2652199-prog/ROK21` · `D:\ROK21` · 포트 **7021**.
원본 kweon 미접촉. 1~3군 memoy 기록 금지(R34).

## 1) 현재 스레드 (매턴 3줄만 갱신)
- 지금: 테스트로또 1단계 완료 — draws MAX1234 · 아틀라스 · 1235예측15세트
- 직전: 준비감사(3+4배선·벤치갭)
- 다음: 1235 추첨 후 채점·분석 / 2단계(수학 이식)는 형 지시

## 2) 숫자 (근거 없으면 미확인)
testlotto draws/features/tiers/detail MAX=**1234**
1232~1234 avg_match: 0.40 / 0.93 / 0.80 (각 n=15)
1235 predictions: stat/markov/review ×5 · prior max=1234(정직)
아틀라스 합계 mean 138.262 · 상위번호 34,27,12,13,18

## 3) 열린 과제 -> FINDINGS.md
K-00·K-02·K-05·K-06·K-07 OPEN. (K-07 testlotto 동기 갭 → 1단계에서 1234까지 해소)

## 4) 주의
- 패턴=역사 신호 · 독립 추첨 · 당첨 보장 아님
- boost 상한 코드 클램프 유지 · random.choices 동결
- DB `lotto_testlotto.db` 로컬 갱신(대용량 · 커밋 신중)

## 5) 더 필요하면
reports/20260726_ROK21_테스트로또_1단계_빅데이터정렬.md
tools/_testlotto_pattern_atlas_1234.json · _testlotto_stage1_baseline_1232_1234.json
