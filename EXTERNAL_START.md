# EXTERNAL_START — 외부 에이전트 작업 흐름 진입점

> **이 파일 하나면 흐름 복구.** GitHub 404 / 로컬 미접근이면 형이 이 파일 전체를 채팅에 붙여넣는다.
> **젠스파크 압축 시:** `My_Drive_Sync/SUMMARY/GENSPARK_COMPRESS_RECOVER.md` 를 **같이** 붙여넣기 (채팅기억 불신·JSON 재페치).
> 상세 복사용 프롬프트: `My_Drive_Sync/SUMMARY/EXTERNAL_AI_BOOTSTRAP.md`
> **핀 베이스라인:** `My_Drive_Sync/SUMMARY/PINNED_BASELINE.md`
> 동생 큐(권한 있을 때): `My_Drive_Sync/SUMMARY/RESTORE.md`

## LIVE 작업 흐름 (자동 동기 · 외부AI 1순위)

| 키 | 값 |
|----|-----|
| HEAD(실측) | `8bd0eef` |
| BASELINE_PIN | `640cb67` |
| WORK | `IDLE` |
| 지금 | **SEED-NOISE-FLOOR v2**(n1183·seed24) — **FLOOR_NOT_ESTABLISHED**: 바닥 0.010127→**0.005087** · 잭나이프 95%CI **[−0.008244,0.018012]** 0 포함 → **「표본 늘려도 영원히 판정 불가」 철회**, 올바른 표현은 **「가용데이터로는 불가」** · **R39 신설**(σ 비교 전 σ/√(2(k−1)) 선검증 강제 · `tools/k_precision.py` 7/7) |
| 직전 | K-STAT-NOISE-SOURCE(잡음 유입점 **'뽑기' 확정** · 뇌별 팽창차 구분가능쌍 **0/3** → stat 전용대책 근거 없음 · 반사실 결정적절단 짝지은 p=0.7156 무손해) |
| BOOT다음 | ①1236+ 전향적 EV로그 ②seed 평균화 설계(형 GO 필요) ③바닥 0 여부 확정(seed 대폭 증량) 중 **형 1건 선택** · 발권가중 금지 |
| NEXT1 ID | **K-FLOOR-V2-NEXT-PICK** |
| NEXT1 할일 | 잡음바닥 seed24 재측정 완료 — **결론: FLOOR_NOT_ESTABLISHED**. 바닥 0.010127→**0.005087** · 잭나이프 95%CI **[−0.008244, 0.018012]** 로 0 과 구별 불가 → 「Δ+0.0047 < 바닥이니 표본 늘려도 영원히 판정 불가」 **철회**, 올바른 표현은 **「가용데이터(n=1183)로는 판정 불가」**(실무 처방은 동일). **R39 신설**(σ 비교 전 정밀도 선검증 강제). 형 확인 후 1건 선택 — **①회차 1236+ 전향적 EV 로그 시작**(권장 · 적중축은 어느 쪽 표현이든 지금 데이터로 닫혀 있고, 남은 인기회피축을 개입 없이 검증) / ②seed 평균화 설계(같은 회차 반복 뽑기→번호 득표 · 잡음 유입점이 '뽑기'로 확정됐으므로 √반복수만큼 감소 · random.choices 무수정이나 발권경로 변경이라 **형 GO 필수**) / ③바닥이 진짜 0 인지 확정(seed 대폭 증량 재측정 · 실익은 낮음 · 임계는 이미 잡음곡선에서 나옴) / ④트랙정지 |
| 승인필요 | 없음 (①③은 측정·기록만 · 발권경로 무변경) / ②는 형 GO 필수 |
| 선행 | 없음 |
| OPEN샘플 | K-00, K-02, K-05 |

### 역할
- 형=결정 · 동생(너)=판단·짧은 지시서 · 커서=실행·commit·push
- 너는 D:\ROK21 / 비공개 GitHub를 못 열 수 있다 → **이 LIVE 블록이 SSOT**
- 404 = 권한 없음(경로 오류 아님). D:\3kweon·memoy·1~3군 미접촉

### 본선 vs 인프라
- 테스트로또 **3예측+4보조 유지** (구조 해체 없음)
- K-AB~AF = 수집/문서/훅(예측력 무관) · 인프라 지시 남발 금지
- 형 방향 = 전제 실증·쓸모 (적중↑ 랜덤앱 아님)

### 네가 할 일
1. 첫줄 `[복귀] HEAD=8bd0eef · 지금=**SEED-NOISE-FLOOR v2**(n1183·seed24) — **FLOOR_NOT_ESTABLISHED**: 바닥 0.010127→**0.005087** · 잭나이프 95%CI **[−0.008244,0.018012]** 0 포함 → **「표본 늘려도 영원히 판정 불가」 철회**, 올바른 표현은 **「가용데이터로는 불가」** · **R39 신설**(σ 비교 전 σ/√(2(k−1)) 선검증 강제 · `tools/k_precision.py` 7/7) · 다음=K-FLOOR-V2-NEXT-PICK`
2. 승인 없으면 장문 지시서 금지 · 형에게 질문 1개
3. 추가 파일 필요 시: `형, SUMMARY/○○.md 붙여줘`

## 압축 복구 (젠스파크)
1. 채팅 기억·압축 전 장문 = **불신**
2. `GENSPARK_COMPRESS_RECOVER.md` 붙여넣기 + 증거체인 JSON raw fetch
3. `[복귀]` 한 줄 후, JSON과 불일치하는 기억은 폐기 선언

## 파일 지도 (권한 있을 때만)
| 용도 | 경로 |
|------|------|
| 복귀5줄 | `My_Drive_Sync/SUMMARY/RESTORE.md` |
| NEXT 1건 | `My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md` |
| 매턴요약 | `My_Drive_Sync/SUMMARY/FLOW_BRIEF.md` |
| **젠스파크압축복구** | `My_Drive_Sync/SUMMARY/GENSPARK_COMPRESS_RECOVER.md` |
| 결함 | `My_Drive_Sync/SUMMARY/FINDINGS.md` |
| 명분 | `My_Drive_Sync/SUMMARY/WARRANT.md` |
| 핀 베이스라인 | `My_Drive_Sync/SUMMARY/PINNED_BASELINE.md` |
| 수치 | `docs/benchmarks/*.json` |

_generated: 8bd0eef_
