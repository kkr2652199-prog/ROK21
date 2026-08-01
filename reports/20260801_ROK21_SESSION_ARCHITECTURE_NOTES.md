# ROK21 세션 정리 — 아키텍처·tier·뇌구조·백테 (2026-08-01)

HEAD `04a90fd` · NEXT **K-ATTACK-HOLD** · 코드 변경 없음(본 문서만)  
SSOT 수치: `docs/benchmarks/*.json`

---

## 1. 세션 타임라인 (완료)

| ID | 결과 | 핵심 |
|----|------|------|
| K-ARCHITECTURE-REVIEW | OK | markov learn 미소비 · Jaccard≈0.09 · pin=FULL1182 artifact |
| K-MARKOV-LEARN-SURVEY | **FAIL** | wired ge3=0.105 · stored old=0.165 · **코드 롤백** |
| (채팅) tier·구조 논의 | 문서화 | ge3≠3등 · 3+4 역할 · pool·뇌패키지 제안 |

---

## 2. ge3 vs 로또 「3등」 (용어)

| 용어 | 의미 |
|------|------|
| **ge3** | matched≥3 · 벤치 지표 · **대부분 5등(3개 적중)** |
| **r3 (3등)** | 5개 적중 · FULL 5910장 기대 **≈0.17장** · 실측 **0** |
| **r4/r5** | 4등·5등 · 이론·실측 **일치** (K-BENCH·K10SET FULL) |

**결론:** 「3등이 안 나온다」= **티어 r3(5개)** · 「4·5등은 나온다」= **ge3 대부분 r5** · **1·2등 집중 구조 아님**.

---

## 3. 3+4 뇌 프로세스 (live coordinator)

```
draws → [3뇌 predict_sets] → 15장(번호 확정)
           ↓
      [4보조 score_set] → confidence·reasoning만 (nums 불변 · K-PIPE-A)
           ↓
      [wire quota 5] → markov3+stat1+review1
```

- **3뇌 = 번호 생성** · **4보조 = 채점·정렬** (세트 생성 없음 · K-Y)
- **몰아주기(repack)** = `signal_pool.py` · UI/survey · **live 5장과 별 트랙**

---

## 4. 뇌별 코드 규모 (실측)

| 구분 | 파일 | 실코드≈ |
|------|------|--------|
| stat | `brains/predict_stat_fairy.py` + `predict_statistical.py` | ~289 |
| markov | `brains/predict_flow_shaman.py` + `predict_markov.py` | ~202 |
| review | `brains/predict_review_king.py` | ~97 |
| aux 4 | `aux_*.py` | ~195 |
| 배선 | `coordinator.py` | ~237 |
| 몰아주기 | `signal_pool.py` | ~238 |

**형 지적:** `brains/`만 보면 얇음 → **엔진이 루트에 분산** (kweon 레거시 어댑터).

---

## 5. 구조 개선 논의 (패치 전 · HOLD)

### 5.1 pool·몰아주기

| 구조 | 비고 |
|------|------|
| live | 3×5 → wire 5 |
| survey/UI | **10 pool → 5 repack** (뇌별) |
| 제안 | **8 pool → 7 repack** (약한 몰아주기) · QUICK+FULL survey 후보 `K-POOL87` |

벤치: pool10 QUICK ge3=0.145 · FULL=0.1218 collapse · det_topk **FAIL**.

### 5.2 보조 3+1 분배 (설계안)

| aux | 1차 담당 뇌 |
|-----|------------|
| miss | review |
| pattern | markov |
| balance | stat |
| referee | 공통 |

업그레이드: aux **hint → 해당 뇌 engine** (repack/live 통합).

### 5.3 뇌 패키지 리팩터 (설계안)

```
brains/stat/{engine,learn,predict}.py
brains/markov/...
brains/review/...
brains/shared/{diversity,cutoff}.py
```

- **목적:** 유지보수·뇌별 실험 · ge3↑ **자동 보장 없음** · 동치 벤치 필수
- **HOLD 중:** 문서·스켈레톤만 · 형 GO 후 stat부터 이동

### 5.4 QUOTA-GAP

15중 best > 선택5 **43.6%** → set_no_asc 대안 survey 후보.

---

## 6. 백테스트 현황

| run | survey | n | ge3 |
|-----|--------|---|-----|
| 1~2 | REPACK/SELECT QUICK | 200 | 0.275 / 0.145 |
| 3~4 | TAIL100 | 100 | 0.23 / 0.15 |

**FULL n=1182 backtest DB run 없음** · survey FULL(0.1218)만 존재.

---

## 7. 해외 유튜브 벤치 (요약)

- **WIRED/EV:** jackpot split·인기 회피 → ROK21 **EV 축**과 정합 · ge3 벤치 아님
- **Bet Angel:** 로또 예측 불가 · **crowding avoidance**
- **AI Lotto/hot-cold:** K-Q·K-MARKOV-LEARN과 **중복 기각**
- **Derren Brown:** 일루션 · 개발 무관

---

## 8. ge3 3층 (혼동 금지)

| | ge3 |
|--|-----|
| null | 0.1137 |
| live FULL | **0.1218** |
| pin stored | 0.1447 |

---

## 9. 다음 (형 GO 전)

- **K-ATTACK-HOLD** 유지 · predict/coordinator/wire 패치 금지
- GO 후 후보: `K-POOL87-SURVEY` · `K-AUX-ROUTING` · `K-BACKTEST-FULL` · `K-BRAIN-PACKAGE`(동치)

---

## 10. 복귀 시 읽기 순서

1. `EXTERNAL_START.md` · `RESTORE.md` · `NEXT_ACTIONS.md`
2. `reports/20260801_K_ARCHITECTURE_REVIEW.md`
3. `reports/20260801_KMARKOV_LEARN_SURVEY.md`
4. **본 문서**
5. `My_Drive_Sync/SUMMARY/RESUME_HERE.md`
