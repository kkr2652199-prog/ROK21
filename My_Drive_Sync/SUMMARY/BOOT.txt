# BOOT — 외부 AI 30초 복원 (ROK21 / 복사본)

## 0) 한 줄
**SSOT=`kkr2652199-prog/ROK21` · main · `D:\ROK21` · 포트 7021.**  
원본 kweon(`D:\3kweon` · 6124 · `kkr2652199-prog/kweon` · HEAD `264de3c`) **동결 — 쓰기·push·신규작업 금지**.

## 1) 현재 스레드 (매턴 이 섹션만 3줄 갱신)
- 지금: K-A~K-L 등재 · K-B/C/D 원인규명(표본비공유·best누적가중·fusion의도)
- 직전: testlotto 정밀정찰 READ-ONLY
- 다음: K-B SSOT선언 후 K-A · hyodo동기화(형승인)

## 2) 숫자 (근거 파일 없으면 미확인)
| 지표 | 값 | 출처 |
|------|-----|------|
| LEARN_CUTOFF OFF해시 | **동일** | K09컷오프 |
| 누수 Δ(X−Y) mean/CI | −0.010 [−0.024,+0.004] | 동상 |
| review mean X/Y | 0.767 / 0.767 | 동상 |
| Y풀 EV 순배율/CI | **1.033** [1.019, 1.048] | 동상 |
| K-09 / 전제라벨 | **CLOSED** / **제거** | FINDINGS |
| EV·CUTOFF env 기본 | 둘 다 **OFF** | — |
| testlotto MAX | 1234 | DB |
| kweon 동결 HEAD | **264de3c** | `D:\3kweon` 실측 |

## 3) 열린 과제 -> FINDINGS.md
K-00·02·05~08·10~12 OPEN. **K-09 CLOSED.**  
K-A~K-L OPEN (K-12b→K-L). 우선: **K-B** → K-C/J → K-A.

## 4) 주의 (붕괴 방지)
- 이 레포=ROK21 (kweon 20260726 04:38 복사본). SSOT=ROK21 main
- kweon 은 20260726 `264de3c` 에서 동결. 신규 작업 금지
- 외부 AI 는 ROK21 만 조회할 것
- **「간략 보고」= 채팅창 그 턴만.** STATUS·BOOT 본문·reports·벤치는 압축 금지.
- BOOT §1만 3줄. 평가 시 **mean 병기**(K-08). best-of-N 천장≈2.27 인지.
- 동결: `random.choices` 미수정 · `_get_draws_before` · boost 상한.
- 원본 kweon 미접촉. DB 전체초기화 비권고.
- 분석→결론→튜닝. 추가뇌/세트확장은 best 목적으론 후순위.

## 5) 더 필요하면
1. `RESTORE.md`
2. `STATUS_LATEST.md`
3. `reports/20260727_ROK21_SSOT확정_인코딩수정.md`
4. `reports/20260726_ROK21_K09컷오프_EV재검증.md`
