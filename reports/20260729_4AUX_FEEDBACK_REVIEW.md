# 4보조 심사/피드백 구조 검토 (READ-ONLY) + GenSpark 확인

📅 2026-07-29 · **코드 수정·DB write 없음** · HEAD 실측 `d6f6750`

## 1) GenSpark 브라우저

- 탭: `genspark.ai/agents?id=f37431fd-be0f-4863-83cc-03158c40944b`
- 최근 주제: 3뇌4보조 구조 · DB 리셋 찬반 · K-BENCH-02 FAIL · 형 6질문 답변
- GenSpark 결론(쉬운 말):
  - 전체 DB 리셋 **반대** · coordinator 패치 후 UI 확인 시에만 **범위 삭제** 찬성
  - 4보조는 **검증된 심사관이 아님** · DB 분업 분석팀 아님 · **15장에 점수만**
  - WIRE-V2에선 AUX가 **컷하지 않음** (set_no_asc 쿼터)
  - 피드백 뼈대는 있으나 **등수별 축적은 약함**
  - 최소 다음: K-BENCH-01(READ-ONLY) → hit draw 특성 → (형 GO 후) 등수 피드백 태그

## 2) 코드 핵심 답 (A~D)

### A) 4보조 = DB 분업 분석? → **아님**
- `coordinator._apply_aux_scoring`: 후보 세트마다 `score_set` → confidence에 반영
- miss/pattern/balance/referee는 **채점자** (과거 draws 참고 가능, 역할별 DB 분할 분석 아님)

### B) 최종 5장에서 AUX 컷? → **현재 배선에선 안 함**
- 점수 부여 후 `apply_markov_wire_quota`가 **set_no_asc**로 markov3+stat1+review1
- `markov_wire_method: "set_no_asc"` — confidence 정렬로 발권하지 않음
- K-BENCH-02: baseline set_no_asc ge3=**0.1100** > confidence/AUX 정렬(0.0990~0.1024) → AUX 정렬 **역효과**

### C) 피드백이 3뇌에 쌓이나?
| 경로 | 내용 |
|------|------|
| 쌓임 | `walkforward` → `apply_feedback` → `testlotto_brain_learn_state` / weights / `brain_review` |
| 소비 | **stat·review** 생성 시 `load_learn_state` adjustments · referee `recent_avg_match` 가중 |
| 약함 | **markov**는 learn_state 미사용(코드상) · 등수(1~5등)별 세분 피드백 없음 · 패턴 miss 태그+평균적중 위주 |

### D) 형 제안(당첨/미당첨→피드백 축적)
- **방향 맞음** · 뼈대(`apply_feedback`)는 있음 · **등수·근접 분석 루프는 부족**

## 3) 쉬운 말 판정

| 형 가설 | 판정 |
|---------|------|
| 4보조가 예전부터 “검증된 심사” | **틀림** (미입증·기각 명분 다수) |
| DB 과거를 나눠 분석 | **틀림** (15장 채점) |
| 4보조 컷으로 신호 유실 | **현재 발권에선 틀림** (set_no_asc가 고름) · 다만 confidence 경로였다면 **맞는 우려**였고, BENCH-02가 그 경로가 더 나쁨을 보임 |
| 4보조 심사 미검증 | **맞음** |
| 당첨/미당첨→피드백 축적 필요 | **맞음** (부분 구현·부족) |

**한 줄:** 형 감각(미검증 보조·피드백 강화)이 코드·벤치와 맞고, 우리는 “증명 전 배선 금지”로 보수적이었음 — 둘 다 맞음.

## 4) GenSpark 후속
- GenSpark가 형 6질문에 이미 팩트 답변 완료(위 §1).
- 커서 교차확인: 위 A~D와 **일치**.
- 제안 순서(GenSpark): K-BENCH-01 → hit-draw 특성 → (GO) ge3/ge4 피드백 태그.

## 근거 파일
- `app/testlotto/brains/coordinator.py`
- `app/testlotto/brains/aux_*.py`
- `app/testlotto/learn_state.py` · `walkforward.py`
- `reports/20260729_KBENCH_CONFIDENCE_SURVEY.md`
