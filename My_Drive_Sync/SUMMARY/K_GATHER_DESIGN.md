# K-GATHER-DESIGN — 뇌내 몰아주기 +5세트 전담 로직 명세

📅 2026-07-29 · 핀③ · `PINNED_GATHER_POS.md`  
📌 **뼈대만** — 고도 튜닝은 이후 핀

---

## 0) 확정 정의

| 항목 | 값 |
|------|-----|
| 단위 | **예측뇌 1개** (stat / markov / review 각각) |
| 입력 | 해당 뇌 **기존 5세트** (nums · confidence · reasoning) |
| 출력 | **몰아주기 5세트** 신설 태그 `gather` (또는 set_no 6~10) |
| 결과 구조 | 뇌당 **10세트** · 전체 **30세트** |
| 금지 | 3뇌 합집합 몰아주기 · `random.choices` 경로로 번호 뽑기 |

---

## 1) 전담 모듈 (신설)

제안 경로: `app/testlotto/brains/gather_repack.py`

```
repack_sets(brain_tag, base_sets: list[5], draws_before, target_draw_no) -> list[5]
```

- WF·coordinator에서 predict 5세트 직후 호출 (⑤ WIRE 시)
- ④ PILOT은 동일 함수를 오프라인으로만 호출

---

## 2) 알고리즘 뼈대 (v0 · 비랜덤)

### Step A — 후보 풀 V
- \(V =\) 5세트 nums의 **합집합** (보통 17~25개)
- (옵션) confidence 상위 세트에서 나온 번호에 가중 플래그

### Step B — 자릿수 제약 (K-POS-TRACE)
- 정렬 자리 \(k\)의 허용: \(k \le x \le 40+k\)
- 각 gather 세트는 생성 후 정렬·검증 (불법 자리 0)

### Step C — 점수 (역추적 입력 · v0는 단순)
세트 \(S\) 점수 =
1. **커버 이득**: 5세트에서 **한 장에도 같이 안 나온** 고빈도 쌍을 모으는지 (뇌내 pair 재결합)
2. **자리 다양**: 이론 자리 mean에 가까운 LMH/합 (PATTERN-1 구간 신호와 정합)
3. **중복 패널티**: 기존 5세트와의 Jaccard 과도 중복 감점  
4. (v1+) POS 전이 가중이 유의할 때만 가산 — **v0는 sticky≈null이므로 전이 가중 OFF**

### Step D — 5장 산출
- V에서 그리디/커버링 휴리스틱으로 6공×5장
- 목표: **쌍 커버 최대** + 자리 합법 + 기존5와 차별
- 동점 시: 합 구간 [100,170] · 홀짝 2:4~4:2 선호 (balance 명분)

### Step E — 태깅
```json
{"set_no": 6, "nums": [...], "kind": "gather", "reasoning": "몰아주기v0: ..."}
```

---

## 3) 학습 진화 (나중 튜닝)

| 단계 | 내용 |
|------|------|
| v0 | 규칙 엔진 (본 명세) |
| v1 | SCATTER waste 패턴으로 pair 재결합 강화 |
| v2 | learn_state에 gather 전용 키 (형 GO) |
| v3 | 전담 소형 모델 — **동결 토큰 미사용** 경로만 |

---

## 4) 성공 기준 (④ PILOT)

| 게이트 | 내용 |
|--------|------|
| 사후 상한 | gather 세트가 같은 V로 **oracle 6모음**에 얼마나 가까운지 (설명용) |
| 사전 실측 | gather best mean / ge3/ge4 vs base5 · **null best-of-5** 병기 |
| 다양성 | gather↔base Jaccard mean < 0.5 (복제 금지) |
| 금지 | ge6↑ 보장 주장 |

---

## 5) 비범위 (⑤ 전)

- UI 10세트 표시
- DB 스키마 sets_count 변경
- 라이브 발권 기본값을 gather로

→ **K-GATHER-WIRE** + 형 GO

---

## 6) 다음

**K-GATHER-PILOT** — `tools/_kgather_pilot.py` 가 v0 규칙으로 2~1234 오프라인 채점
