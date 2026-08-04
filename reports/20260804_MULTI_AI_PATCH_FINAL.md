# 다중 AI 협업 논의 → ROK21 최적 패치 최종안

📅 2026-08-04 KST · HEAD 작성시점 `d6231a3` (push 후 1커밋 지연 가능)  
📌 성격: **논의·최종안 보고** (이 문서만으로 코드 wire 없음)  
📌 역할 SSOT: `My_Drive_Sync/SUMMARY/AI_COLLAB.md`  
📌 수치 SSOT: `docs/benchmarks/*.json` · 결함: `FINDINGS.md`

---

## 0. 한 줄 최종안

**다음 대패치는 「계수 재탕」이 아니라 `K-EVOLVE-LOG` — 회차·뇌별 예측→채점→패턴(적중·오답)→DB축적→as_of절단 학습이다.**  
학습 입력에서 **best 단독(K-N 독)** 을 빼고, **구조 특징·세트 mean·조립 출처**만 진화 신호로 쓴다.  
hybrid wire·FULL 게이트는 유지·병행하고, **1236 자동은 루프 완성 후**.

---

## 1. 협업 테이블 (누가 무엇을 말했는가)

| 에이전트 | 역할 | 이번 논의에서의 주장 | 근거·제약 |
|----------|------|----------------------|-----------|
| **형** | 최종 결정 | 3뇌 독립 구조는 됨. 회차1→1235 **학습 진화**가 본선. 번호 암기 복습보다 적중·오답 패턴·DTA 축적. 지금은 수동 개발단 | 제품 의도 |
| **커서** | 실행·벤치·코드 SSOT | 구조·hybrid·pin갭 진단은 끝. 고정가중·짧은 EMA·best feedback이 병목. wire는 작은 단위·FULL/as_of 준수 | `signal_pool` · `learn_state` · 동결 3종 |
| **젠스파크** | 전략·지시서 초안·팩트 | 로드맵 I1~I3·rare HOLD·pin≠collapse. 외부 벤치=WF·calibration·covering. **ultra→ge3 기각** | 로드맵·GS-FACTCHECK |
| **벤치/게이트 (도구 AI)** | 수치 판정 | null은 eval_mode별 · n100 seed 민감(0.15↔0.10) · FULL early 약 · hybrid +0.04/+0.03 | JSON SSOT |
| **FINDINGS 감사** | 결함 라벨 | K-N HOLD(best 오인) · K-M HOLD(referee≈0) · K-P(5적중 학습신호 부재) | FINDINGS |
| **외부 문헌 역할** | 벤치 아이디어 | Walk-forward · Brier · covering · 구조빈도≠P | 로드맵 §4 |

> 실제 채팅에 전 AI가 동시 접속한 것은 아님.  
> **GitHub SSOT + 본 세션 대화 + AI_COLLAB 역할**을 한 테이블에 모아 “다중 관점 합의”로 재구성한 보고서다.

---

## 2. 합의된 현황 (논쟁 없음)

### 2.1 이미 갖춘 골격
- 뇌별 **10세트 미래예측** + **몰아주기** (독립 구조)
- FUTURE-WIRE live · hybrid wire: stat/review `hy_p45_r123` · markov baseline  
  - 검증 ge3(n=200): stat **0.165** · markov **0.130** · review **0.135**  
  - `docs/benchmarks/20260804_KREPACK_HYBRID_WIRE.json`
- as_of / `_get_draws_before` 철학 · 동결 토큰 유지
- eval_mode별 null · UI 즉시 백테

### 2.2 아직 “옛 틀”에 남은 것
- 학습 = 짧은 EMA + **best 피드백** 잔재 (K-N)
- referee 학습 → 발권 실효≈0 (K-M)
- W_HINT/W_FREQ/W_LEARN · SOLO_PRIOR 등 **고정 계수** 중심 튜닝
- **회차 전체(1→1235) 진화 로그 SSOT** 부재
- FULL pin 갭(Δ−0.0263) · early 약세 · seed 민감 — “자동 1236” 전에 게이트 필요

### 2.3 형의 진화 모델 (전원 수용)
```
회차 t: 예측(10+몰아주기) → 적중확인 → 패턴(적중·오답) → DB저장
       → 상태갱신(t 이하만) → 회차 t+1
회차 1: 학습 입력 없음 (정상)
… → 1235까지 축적 → (패치 완료 후) 1236~ 자동
```

---

## 3. 에이전트별 아이디어 (충돌·절충)

### 3.1 형 — 제품 비전
| 아이디어 | 요지 |
|----------|------|
| H1 | 학습 진화 = 회차 로그 축적이지 번호 복습이 아님 |
| H2 | 오답·적중 **둘 다** 분석해 신호 강화 |
| H3 | 3뇌 독립 파이프 유지, 세부 엔진·부품 대업데이트 |
| H4 | 지금은 수동·개발단, 자동은 전부 끝난 뒤 |

### 3.2 젠스파크 — 전략·리스크
| 아이디어 | 요지 | 절충 |
|----------|------|------|
| G1 | I2 FULL-first · n100 단독 wire 금지 | **채택** |
| G2 | I3 B1 feature 로그 가중0 | **K-EVOLVE에 흡수** |
| G3 | ultra rare→ge3 HOLD | **유지** |
| G4 | covering / mild λ는 중기 | EVOLVE 안정 후 |
| G5 | pin갭 진단 전 패치 금지 | I1 **완료** → 다음 축 전환 OK |

### 3.3 커서 — 구현 가능성
| 아이디어 | 요지 | 절충 |
|----------|------|------|
| C1 | 새 테이블 `evolve_log` (draw×brain×set) | **1순위 패치** |
| C2 | 학습 입력: mean / rank-hit / assemble source / 1D features | best **제외** |
| C3 | apply_feedback(best) 경로 HOLD→교체 survey | K-N 정합 |
| C4 | markov 80% fusion — evolve 가중은 보수 | markov는 로그 먼저, 가속 나중 |
| C5 | coordinator quota 이번 축에서 손대지 않음 | hybrid 때와 동일 |
| C6 | combined/FULL 재검증은 EVOLVE 전·후 스냅샷 | 게이트용 |

### 3.4 벤치·FINDINGS — 독/약 판정
| 판정 | 내용 |
|------|------|
| **독** | best단독 학습 · 미래참조 · 당첨번호 단순 재가중 · n100/seed42만으로 wire |
| **약** | as_of WF 로그 · 구조특징 · 세트 mean · 조립(hybrid source) 기여 · FULL 기간표 |
| **무력** | referee 미세가중(K-M) — 지금 손댈 ROI 없음 |
| **상한 착시** | 5적중 최적화(K-P) — 진화 목표로 쓰지 말 것 |

### 3.5 외부 벤치 역할 — 이식 가능한 것만
| 이식 | ROK21 형태 |
|------|------------|
| Walk-forward | evolve는 **항상 t 이전만** |
| Calibration | 신호 강도 vs 실제 hit — I6는 중기 |
| Covering | 발권 다양성 — fusion 슬롯 나중 |
| 구조빈도≠P | rare는 UX/로그 특징, ge3 wire 금지 |

---

## 4. 충돌 해소 (합의 결과)

| 쟁점 | 대립 | **합의** |
|------|------|----------|
| 과거 학습이 독? | 형=진화 필요 / FINDINGS=best는 독 | **진화=약, best암기=독** 분리 |
| 다음 1건 | FULL재검증 vs I2 vs 진화학습 | **진화학습 골격(K-EVOLVE-LOG) 1순위** · FULL 스냅샷은 부속 |
| markov 손대기 | fusion 본체라 위험 / 형 3뇌 동등 업데이트 | **3뇌 모두 로그** · 가중 적용은 stat/review 먼저 |
| 자동 1236 | 형 목표 / 커서 시기상조 | **루프+게이트 후** |
| 계수 튜닝 계속? | 익숙함 / ROI 감소 | **HOLD** — EVOLVE 전에는 W_* 그리드 남발 금지 |

---

## 5. 최종 패치안 (ROK21 최적)

### 5.1 프로그램명
**`K-EVOLVE`** — 회차 진화 학습 (개발단 수동 → 이후 자동)

### 5.2 Phase 0 — 동결·게이트 (이번에도 유지)
- `random.choices` / `_get_draws_before` / boost 상한 **미수정**
- kweon 미접촉 · ultra→ge3 HOLD
- 성적 인용: `docs/benchmarks` + eval_mode null
- wire 전: QUICK→(필요시) FULL · pin/null 병기

### 5.3 Phase 1 — `K-EVOLVE-LOG` (즉시 착수 권고 · **가중 0**)
**목적:** 형 흐름을 DB에 먼저 고정. 예측력 가중은 아직 0.

회차×뇌마다 저장 (제안 필드):
- `draw_no`, `brain_tag`
- pool 10 · repack 5 (nums, assemble, source)
- 세트별 hits · best · **mean**
- 특징: zone/parity/max_run/rarity 등 (I3 B1 흡수)
- 오답 태그: miss_pattern (기존 highway 태그 재사용 가능)
- `as_of = draw_no` (해당 회차 채점 후 기록, 다음 예측은 draw_no 미만만 읽음)

완료조건:
- 1035~1234 (또는 53~1234) 백필 READ-ONLY 가능
- UI/보고서에서 회차 1건 로그 조회
- **예측식·W_*·quota 변경 0**

### 5.4 Phase 2 — `K-EVOLVE-SIGNAL` (형 GO 후 survey)
학습 입력 교체 실험 (wire 전 ablation):
1. **차단:** `apply_feedback`의 best→실력 경로 (K-N)
2. **후보 신호 (가중 소량 λ sweep):**
   - set mean / rank별 hit rate
   - hybrid `source` (pool4/5 vs score_repack) 기여
   - 1D 구조 특징 (가중 상한 작게)
3. 뇌별: stat·review 먼저 · markov는 로그 대비만 또는 λ 절반
4. 게이트: QUICK n=200 · 통과 시 FULL · seed 2개 이상

### 5.5 Phase 3 — `K-EVOLVE-AUTO` (맨 마지막)
- 1235까지 로그·신호 안정 + I2 FULL-first 문서화
- 1236~ 자동 예측·채점·저장 파이프
- 지금은 **설계만** 문서에 남김

### 5.6 병행 HOLD / 낮은 우선
| 항목 | 조치 |
|------|------|
| W_HINT 그리드 | EVOLVE 전 HOLD |
| referee(K-M) 패치 | HOLD |
| ultra rare wire | HOLD |
| markov quota 변경 | HOLD |
| hybrid 추가 변형 | live 유지 · 재스윕 불급 |

### 5.7 부속 (Phase 1과 같은 주 가능)
- **FULL/combined 스냅샷** — hybrid wire 이후 baseline 고정 (회귀 비교용)
- **I2 한 줄 규칙** — “n100만 PASS면 wire 금지”를 BENCH_PROTOCOL에 명문화

---

## 6. 왜 이 최종안이 “우리 앱”에 가장 적합한가

1. **형 비전과 동일 축** — 회차 진화·오답/적중·DB축적  
2. **독(K-N)을 구조적으로 제거** — best 암기 복습과 분리  
3. **이미 만든 3뇌×10+몰아주기·hybrid를 폐기하지 않음** — 위에 로그·신호를 얹음  
4. **벤치 현실과 맞음** — seed/FULL/early 문제를 “운 좋은 계수”로 덮지 않음  
5. **협업 분업 명확** — 젠스파크=Phase설계 검토 · 커서=LOG구현·벤치 · 형=GO  

---

## 7. 형에게 부탁할 선택 (1개만)

| 선택 | 의미 |
|------|------|
| **A (권고)** | `K-EVOLVE-LOG` GO — 가중0 로그+백필+조회 |
| **B** | Phase1 + FULL/combined 스냅샷 동시 |
| **C** | EVOLVE 보류 · hybrid FULL 재검증만 |
| **D** | 계수/quota 쪽 재탕 (비권고) |

---

## 8. 근거 파일

| 파일 | 쓰임 |
|------|------|
| `docs/benchmarks/20260804_KREPACK_HYBRID_WIRE.json` | hybrid live 성적 |
| `docs/benchmarks/20260804_KREPACK_HYBRID_survey.json` | 조립 ablation |
| `docs/benchmarks/20260804_KPIN_GAP_DIAG.json` | pin갭·seed·K-M/N |
| `docs/benchmarks/20260803_KFUTURE_WIRE_FULL.json` | FULL 0.1184 |
| `reports/20260804_IMPROVEMENT_INVESTIGATION_ROADMAP.md` | I1~I7·외부벤치 |
| `My_Drive_Sync/SUMMARY/FINDINGS.md` | K-M/N/P |
| `My_Drive_Sync/SUMMARY/AI_COLLAB.md` | 3자 역할 |

---

## 9. 금지 (최종안에도 명시)

- 동결 3종 · kweon 쓰기  
- FINDINGS 무단 CLOSED  
- FAIL→auto-tune  
- best단독을 “진화 성공” 지표로 사용  
- n100·seed42 단독 PASS로 Phase2 wire  

---

**결론:** 다중 관점 합의 최종안 = **`K-EVOLVE-LOG` → `K-EVOLVE-SIGNAL` → (나중) `K-EVOLVE-AUTO`**.  
형이 **A 또는 B** 라고 하시면 커서 지시서·스키마 초안을 바로 작성한다.
