# K-EVOLVE-AUTO — Phase3 설계문서 (실행 wire 없음)

📅 2026-08-05 KST · **DOC** · HEAD 실측은 push 후 SSOT  
📌 다중AI안 §5.5 · 「지금은 설계만」준수 · **코드 자동실행/가중학습 wire 금지**

---

## 0) 초보용 한 줄

1236회부터는 「예측 → 추첨 후 채점 → 로그 저장」을 **자동으로 반복**하려는 설계다.  
지금은 **도면만** 그린다. 스위치를 켜지 않는다.

---

## 1) 목표 / 비목표

| 구분 | 내용 |
|------|------|
| **목표** | 신규 회차(1236~)마다 live 예측·채점·`evolve_log` 축적을 **수동 백필 없이** 돌리는 파이프 |
| **비목표** | best번호 복습 학습(K-N) · λ/covering 실패축 재wire · W_*/quota/boost 자동튜닝 · 1등확률 보장 |
| **성공 정의** | (나중) 회차 마감 후 로그 3뇌 행이 생기고, mean 피드백만 기존 규칙으로 갱신되며, 운영자가 API/UI로 조회 가능 |

---

## 2) 선행 상태 (설계 입력 · 20260805 기준)

| 항목 | 상태 | 근거 |
|------|------|------|
| Phase1 LOG | PASS · n=1182 (53~1235 구간 확장) | `20260804_KEVOLVE_LOG_EXPAND.json` |
| Phase2 SIGNAL | mean 피드백 live · λ n200은 과적합 | `FEEDBACK_MATCH_MODE=mean` · REVAL HOLD |
| feature λ | **OFF** | `FEATURE_LAMBDA_WIRE=False` |
| structure/pair cover | 모듈만 · ge3↓ · **WIRE=False** | COVER surveys HOLD |
| FULL fusion | ge3=0.1184 Δ=0 | `20260804_KFUTURE_FULL_POST_EVOLVE.json` |
| hybrid | live | schema≥2/3 · hy_p45_r123 |

**AUTO 실행 게이트(설계상 필수, 현재 미달 가능):**

1. evolve_log가 최신 확정회차까지 연속 존재  
2. λ/covering 등 **실패한 가중축은 OFF 유지**  
3. QUICK(n=200) 회귀: hybrid+mean 스택이 직전 스냅샷 대비 붕괴 없음  
4. 형 GO (문서만으로는 실행 금지)

---

## 3) 파이프라인 (1236~ 1회차 생애)

```
[T0 추첨 전]
  1) target = next_draw_no
  2) predict_sets / build_pool_and_repack (기존 live · seed=42)
  3) pool_view_cache 저장 (현재 schema)
  4) (선택) UI「3뇌 예측」과 동일 산출물 노출
  ※ 학습 가중 변경 없음 · weight_applied=0 로그 예약만

[T1 공식 번호 확정 후]
  5) lotto_draws upsert (기존 수집 경로)
  6) 채점: pool10+repack5 hits / features / miss_tags
  7) evolve_log upsert × 3뇌  (Phase1과 동일 스키마)
  8) coordinator._auto_feedback(mean)  — 기존 경로만
  9) API: GET /evolve/log/{draw} · /evolve/summary 갱신 가능

[T2 운영]
 10) 실패 시 dead-letter + 알림(설계) · 자동 재시도 1회
 11) 주 1회 QUICK smoke (설계) — ge3 붕괴 시 AUTO pause
```

---

## 4) 컴포넌트 분해

### 4.1 이미 있음 (재사용)

| 부품 | 위치 |
|------|------|
| 예측·pool·hybrid | `signal_pool.build_pool_and_repack` |
| 캐시 | `pool_view_cache` |
| 로그 행 생성/upsert | `evolve_log.build_evolve_row` / `upsert_evolve_row` |
| mean 피드백 | `coordinator.FEEDBACK_MATCH_MODE=mean` |
| 조회 API | `/api/testlotto/evolve/log/{draw}` · `/evolve/summary` |
| 과거 백필 | `backfill_expand_wf` / `_k_evolve_log_expand.py` |

### 4.2 새로 만들 것 (구현 시 · 지금 안 함)

| ID | 부품 | 책임 |
|----|------|------|
| A1 | `evolve_auto_runner.py` (가칭) | 회차 상태머신: PREDICT / WAIT_DRAW / SCORE / DONE |
| A2 | 스케줄 진입점 | cron/수동 CLI `python tools/_k_evolve_auto_tick.py` |
| A3 | `testlotto_evolve_auto_state` 테이블 | last_draw · phase · error · paused |
| A4 | pause 스위치 | env/`EVOLVE_AUTO=0` 기본 · 형 GO 후에만 1 |
| A5 | 회귀 훅 | tick 후 QUICK 샘플 또는 최근 20회 mean_hits 감시 |

### 4.3 절대 넣지 말 것 (동결·실패축)

- `random.choices` / `_get_draws_before` 변조 / boost 상한 상향  
- best-of-5를 학습 입력으로 사용 (K-N)  
- `FEATURE_LAMBDA` · `STRUCTURE_COVER` · `PAIR_COVER` wire 재개 (HOLD 유지)  
- FAIL→자동 계수 탐색 루프  
- 원본 kweon 경로 접촉  

---

## 5) 데이터 계약

### 5.1 evolve_log (유지)

- PK `(draw_no, brain_tag)`  
- `weight_applied = 0` 기본 (AUTO도 Phase1과 동일; 가중 wire는 별도 형 GO)  
- `as_of = draw_no` (기록 시점) · 학습/버킷은 항상 `draw < target`  
- pool_json / repack_json / hits / features / miss_tags / assemble_mode  

### 5.2 auto_state (신설 예정)

```
last_completed_draw INTEGER
phase TEXT  -- idle|predicted|scored|paused|error
last_error TEXT
updated_at TEXT
```

### 5.3 회차 번호 규칙

- 확정 번호가 DB에 들어온 뒤에만 SCORE  
- 미추첨(예: 최신+1)은 PREDICT만  
- MAX(lotto_draws) 기준으로 tick  

---

## 6) 게이트·롤백

| 게이트 | 조건 | 실패 시 |
|--------|------|---------|
| G0 형 GO | 명시 승인 | 실행 금지 |
| G1 플래그 | `EVOLVE_AUTO=1` | no-op |
| G2 로그 연속 | 직전 N회 evolve_log 3뇌 완비 | pause + 백필 요청 |
| G3 회귀 | 최근 창 mean/ge3 참고지표가 급락 | pause (학습축 자동변경 금지) |
| G4 동결 | 동결 토큰 diff 없음 | CI/수동 확인 |

롤백 = `EVOLVE_AUTO=0` + 예측/로그는 수동 경로로 복귀. DB 로그는 삭제하지 않음.

---

## 7) 구현 단계 (형 GO 이후)

| Step | 내용 | 산출 |
|------|------|------|
| S0 | 본 설계 확정 | 이 문서 |
| S1 | auto_state + tick CLI (dry-run) | 코드 · dry-run 로그 |
| S2 | SCORE만 자동 (예측은 기존 UI/캐시) | 1235 이전 재현 테스트 |
| S3 | PREDICT+SCORE 통합 | staging 1회차 |
| S4 | 운영 on (`EVOLVE_AUTO=1`) | 형 GO · 모니터링 1주 |

**현재 허용 범위 = S0만.**

---

## 8) UI/API (나중)

- 상태: `GET /api/testlotto/evolve/auto/status`  
- 수동 tick: `POST .../evolve/auto/tick` (관리자)  
- pause: `POST .../evolve/auto/pause`  
- 기존 log/summary 유지  

---

## 9) 위험과 명분

| 위험 | 대응 |
|------|------|
| 자동이 곧 ‘학습 강화’로 오해 | weight=0 · mean만 · 문서에 명시 |
| covering/λ 재도입 유혹 | HOLD 목록 고정 · 별도 지시서 없이 금지 |
| FULL 붕괴 재발 | G3 · n100-only wire 금지(I2) |
| DB 비대화 | evolve_log는 텍스트 JSON · 주기 vacuum 운영노트 |

명분: 회차 진화·오답/적중 **축적**은 형 비전과 동일.  
AUTO는 그 축적의 **운송 벨트**이지, 당첨확률 엔진이 아니다.

---

## 10) 판정

| 항목 | 값 |
|------|-----|
| 문서 | **DONE** |
| 코드 wire | **없음** |
| 다음 | 형 GO → S1 dry-run · 또는 다른 개선축 |

---

## 11) 관련 파일

| 파일 | 역할 |
|------|------|
| `reports/20260804_MULTI_AI_PATCH_FINAL.md` §5.5 | AUTO 위상 정의 |
| `app/testlotto/evolve_log.py` | 로그 SSOT |
| `docs/benchmarks/20260804_KEVOLVE_LOG_EXPAND.json` | 1182 로그 |
| `docs/benchmarks/20260804_KEVOLVE_FEAT_LAM_REVAL.json` | λ HOLD |
| `docs/benchmarks/20260805_KSTRUCTURE_COVER_survey.json` | cover HOLD |
| `docs/benchmarks/20260805_KPAIR_COVER_survey.json` | pair HOLD |

근거 본문: `reports/20260805_KEVOLVE_AUTO_DESIGN.md`
