# K-NEXT-LIST-V2 — 보강 순서리스트 (정밀·실수방지)

시각: 2026-08-12 KST · HEAD≈`81cc036` · **양산前** · **1237아님** · ge3/등수 **성적클레임 금지**  
선행: `20260812_KNEXT_UPPER_HIT_LIST` ①②완료 · 형 몰아주기 의도 정정  
**⚠ 실행 SSOT 승계:** → `reports/20260812_KNEXT_LIST_V3.md` (역할슬롯 보강)

형 지시: 갭 재정의(1~6·보너스·10세트 분산 저장·다음반영) + 뇌별10세트 엔진 중요 +  
이전에 준비했던 패치 정리해 **리스트 보강**. 실행은 **정밀·1건씩**. (백테 강제 재적재는 패치 안정 후)

---

## 0) 설계 합의 (이번 턴 확정 문구)

### 0-1. 적중 신호의 범위 (고정 1·2개 아님)
- 한 세트에 **운이 좋으면 1~6개 + 보너스**까지 맞을 수 있다.
- 같은 회차라도 그 번호들이 **10세트에 흩어져** 있을 수 있다.
- 과거 회차에서 그 **분산·중복·세트별 적중수·적중번호·보너스**를 저장하고,
  **다음 회차 예측(10세트→몰아주기)** 에 **적극 반영**해야 한다.
- 이것은 **과거 결과 확정 후 분석**이지, 타깃 회차 정답 컨닝이 아니다.

### 0-2. 두 기둥 (둘 다 필수 · 한쪽만 고치면 안 됨)

| 기둥 | 내용 | 현재 |
|------|------|------|
| **A. 뇌별 10세트 엔진** | stat=숙제 · markov=선호 · review=금액 — **스킬에 맞게** 10세트 예측 | knobs 일부 APPLY · 역할 분리 WIRE됨 · 품질 잔여 |
| **B. 몰아주기(10→5)** | 10세트는 **중요 예측물**이자 압축 재료. 과거 A기둥 산출물의 적중분포 신호를 읽어 5장 조립 | EMA 재계산(약함) · **정밀 원장 DB SSOT 없음** |

### 0-3. 프로세스 순서 (실수 방지)
```text
[과거 N-1 이하] 결과확정 → 그 회차 10세트 채점(1~6·보너스·분산) → DB 원장
        ↓
[타깃 N] 뇌별 엔진으로 10세트 예측(정답 미사용)
        ↓
[타깃 N] 원장+힌트로 몰아주기 5세트
        ↓
(별도) 클릭 발권 5장 = coordinator 쿼터 경로 · 지금은 10+5와 분리
```

### 0-4. 지표 규칙 (이미 실측으로 잠금)
| 경로 | 의미 | APPLY 근거로 쓰나 |
|------|------|------------------|
| pool/repack BT 등수 | 장수 많은 분석경로 | **아니오**(모니터) |
| 발권5장 | 현재 클릭 경로 | 모니터·병기 |
| prefer / prize | 축 게이트 | **예** |
| ge3·1~3등 | — | **클레임·단독게이트 금지** |

발권병기 실측: pool mean2.5/≥4=4 vs 발권 mean**1.64**/≥4=**0**  
(`20260812_KBT_ISSUE_PATH_METRIC`)

---

## 1) 이미 끝난 준비 패치 (다시 손대지 말 것 · 롤백 금지 기본)

| ID | 판정 | 요지 |
|----|------|------|
| 뇌독립 WIRE · HINT분리 · SCORE cand_B | APPLY/WIRE | 3뇌 역할 |
| markovBLEND0.55 · reviewBLEND0.85 · W_CROWD0.90 | APPLY/HOLD | 축 잠금 |
| HINT weeks52(stat) · HINT_WEIGHT0.15 | APPLY/HOLD | |
| ASSEMBLE signal_union · oversample m5 | APPLY | |
| referee 뇌별 · K-J SSOT · K-M/N · min_each1 | PATCHED | |
| K-I fallback · K-G ending ACTIVE · K-C STALE_CLOSE | PATCHED | |
| K-F LEARN_WIRED 효과없음 CLOSE | PATCHED | 재오픈 금지(형지시 전) |
| 상위리스트 ①TIER45 · ②ISSUE_PATH | AUDIT/METRIC_OK | BT≠발권 확정 |

동결 유지: `random.choices` · `_get_draws_before` · boost 상한 · kweon 원본 쓰기금지 · 1237양산 아님

---

## 2) 보강 순서리스트 (실행 SSOT · 1건씩)

> **규칙:** 한 턴에 리스트 1 ID만. 게이트 실패면 APPLY 금지·HOLD.  
> **강제BT 재적재:** 큰 배선(원장·몰아주기 SSOT) 안정 후에만. 지금 패치중=백테 강제 재실행 **보류**.

### L0 — 본 문서 보강 · **DOC_OK (본턴)**
- 설계 합의·완료패치·잔여 순서 고정. wire=False.

### L1(=구③) K-POST-REFILL-JOINT-SMOKE — **다음 실행 1건**
- refill_v2 후 prefer/prize/hit 합동 smoke (베이스라인 잠금).
- **왜 먼저:** 원장/엔진 손대기 **전** 드리프트 측정.
- 완료조건: JSON + SMOKE_OK/FAIL · ge3미클레임 · 1237아님.
- 도구후보: `tools/_k_brain_joint_smoke_v2.py` (또는 후속 v3).

### L2 K-POOL-HIT-LEDGER-SPEC — **설계(DOC→스키마)**
- **할일:** 원장 스펙 확정(코드 전).  
  회차×뇌×set_no: hits(0~6) · hit_nums · bonus_hit · 번호가 몇 개 세트에 흩어졌는지(scatter) · 중복출현.  
  **범위=1~6+보너스 전부**(1·2 고정 아님).  
  쓰기 시점=결과 확정 후 · 읽기 시점=다음 타깃 몰아주기. no_peek 검증 항목 포함.
- 기존 약함: `RollingSignalLearner` EMA 재계산 · `evolve_log.pool_hits_json` 비어있음(n0).
- 완료조건: 스펙 MD + 테이블/JSON 스키마안 · 형 확인 후 L3.
- 문헌/배울점: 정직한 WF 원장(누수 금지) · GH “예측AI” 기각.

### L3 K-POOL-HIT-LEDGER-WIRE — **쓰기 배선**
- 스펙대로 DB 영속 + 결과확정/피드백/WF 경로에서 기록.
- 완료조건: 샘플 회차 원장 실측 · 강제리셋 후에도 **재적재 절차** 문서화.
- **백테 강제 재적재는 이 단계 안정 후** (형: 패치중 백테 보류와 정합).

### L4 K-REPACK-READ-LEDGER — **몰아주기가 원장 SSOT 소비**
- 다음 예측 시: 「어느 세트에서 번호를 가져올지」가 **원장 기반**(EMA만 의존 탈피).
- 게이트: prefer/prize 비악화 · 발권경로 모니터 병기 · 선별신호 없으면 HOLD.
- 완료조건: WIRE + 게이트 JSON.

### L5 K-BRAIN10-SKILL-AUDIT — **뇌별 10세트 엔진 정밀감사 (READ)**
- 각 뇌가 **자기 스킬**대로 10세트를 만드는지 재실측.  
  - stat: 숙제/패턴 · markov: 선호 · review: 몫EV  
- 포함: hint분리·RNG독립·pool1~5=발권5 정합(기존 C7/C8)·역할 드리프트.
- 완료조건: AUDIT_OK + 뇌별 결함 리스트(있으면 L6~L8로만 패치).

### L6 K-STAT-10SET-SKILL — 과거학습 10세트 (L5 결함 시만)
- 축: hit 모니터 + prefer/prize 비악화. mean 서열화 금지(K-O).

### L7 K-MARKOV-10SET-SKILL — 선호 10세트 (L5 결함 시만)
- 축: prefer · prize iso0.

### L8 K-REVIEW-10SET-SKILL — 금액 10세트 (L5 결함 시만)
- 축: prize · prefer iso0.

### L9(=구④) K-REPACK-PRESERVE-PROBE — 조립 잔여
- union/slots 소형 스윕. L4 이후. 신호 없으면 HOLD.

### L10(=구⑤) K-TICKET-COVER-LITE — 발권5 겹침↓
- 부분당첨 기회 분산. buy-the-pot 금지.

### L11(=구⑥⑦⑧ 잔여) 축 심화
- review EV · markov prefer · stat homework — **L5~L8 이후** 중복 스윕 금지(이미 HOLD/APPLY된 노브 재탕 주의).

### L12 (후순위·형승인) 발권 경로와 10+5 통합?
- 형이 “패치 후 10세트도 발권” 의도. **제품 결정 후** 별도 ID. 지금 강제 병합 금지.

---

## 3) 구 리스트 매핑

| 구 # | 신 ID | 상태 |
|------|-------|------|
| ① | (완료) TIER45 | AUDIT_OK |
| ② | (완료) ISSUE_PATH | METRIC_OK |
| ③ | **L1** smoke | **NEXT** |
| — | **L2~L4** 원장·몰아주기 SSOT | **신규 보강(형 갭)** |
| — | **L5~L8** 뇌별10세트 스킬 | **신규 보강** |
| ④ | L9 preserve | 대기 |
| ⑤ | L10 cover | 대기 |
| ⑥~⑧ | L11 | 대기 |

---

## 4) 금지 (실수 방지 체크리스트)

- [ ] 타깃 회차 정답으로 그 회차 몰아주기 만들기 (컨닝)
- [ ] 1·2개만 신호로 하드코딩 (1~6·보너스 누락)
- [ ] BT pool등수로 APPLY
- [ ] ge3/1등 성적클레임
- [ ] 동결3종·kweon쓰기·1237양산
- [ ] 강제BT를 패치 도중에 습관적으로 돌리기 (원장 안정 전 보류)
- [ ] 뇌 교차 hint/점수 공유
- [ ] L5 감사 없이 L6~L8 손대기

---

## 5) 진행 상태

| ID | 판정 |
|----|------|
| L0 리스트V2 | **DOC_OK** (본턴) |
| L1 smoke | **NEXT** |
| L2~L12 | 대기 |

---

## 경로
- `reports/20260812_KNEXT_LIST_V2.md` ← **이후 순서 SSOT**
- 구버전 유지: `reports/20260812_KNEXT_UPPER_HIT_LIST.md` (①② 이력)
- 발권병기: `docs/benchmarks/20260812_KBT_ISSUE_PATH_METRIC.json`
