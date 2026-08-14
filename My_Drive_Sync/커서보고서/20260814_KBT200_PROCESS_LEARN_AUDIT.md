# K-BT200-PROCESS-LEARN-AUDIT — 지금 200회 프로세스·학습

시각: 2026-08-14T21:01:57+09:00 · **PASS** · READ-ONLY · ge3미클레임 · 1237아님

## 0) 한 줄

지금 DB 200회(1037~1236) 원장을 읽었다. **프로세스 엔진 가동 정상**(10+5, 역할 5+3+2, 번호 유효, 컨닝 0). 6~8/9~10 복습은 **stat만 소비**. 1~5 숙제표는 이번 경로에 **없음**(발권 피드백 0).

## 1) 플래그·센서스 (파일·DB)

- ROLE_SLOTS_WIRE=**True** · ROLE_TIER_LEARN_WIRE=**True** · 소비뇌=['stat'] · COVER_MIN_HITS=**3**
- draws MAX **1236** · pred **0** · pred1237 **0**
- cache **600** · ledger **3000** · scatter **400**
- role_hw **1200** · skill_hw **0** · learn_state **0** · review **0**
- UI backtest_runs **0** · draw_results **0**

## 2) 프로세스 엔진 (원장 1037~1236)

| 항목 | 값 |
|------|-----|
| 회차 | **200**/200 |
| 뇌 | ['stat'] |
| 행 | 3000 |
| pool10 결손 | 0 |
| repack5 결손 | 0 |
| 역할 불일치 | 0 |
| 번호 무효 | 0 |
| 역할 카운트 | `{'skill_native': 1000, 'cover_r3': 600, 'shape_r2': 400, 'focus_r1': 1000}` |
| kind | `{'stat|pool': 2000, 'stat|repack': 1000}` |
| 캐시 뇌 | `{'stat': 200, 'markov': 200, 'review': 200}` |
| 타뇌 빈캐시 | 400 (stat단독 BT 설계) |

### stat 6~8 생성 경로 (캐시 source)

```
{
  "stat|pool|cover_r3|None": 600
}
```

### 1236 샘플 (역할·source)

```
{
  "stat": {
    "pool_n": 10,
    "repack_n": 5,
    "pool_roles": [
      {
        "set_no": 1,
        "role": "skill_native",
        "source": null
      },
      {
        "set_no": 2,
        "role": "skill_native",
        "source": null
      },
      {
        "set_no": 3,
        "role": "skill_native",
        "source": null
      },
      {
        "set_no": 4,
        "role": "skill_native",
        "source": null
      },
      {
        "set_no": 5,
        "role": "skill_native",
        "source": null
      },
      {
        "set_no": 6,
        "role": "cover_r3",
        "source": null
      },
      {
        "set_no": 7,
        "role": "cover_r3",
        "source": null
      },
      {
        "set_no": 8,
        "role": "cover_r3",
        "source": null
      },
      {
        "set_no": 9,
        "role": "shape_r2",
        "source": null
      },
      {
        "set_no": 10,
        "role": "shape_r2",
        "source": null
      }
    ],
    "repack_roles": [
      {
        "set_no": 1,
        "role": "focus_r1",
        "source": "pool"
      },
      {
        "set_no": 2,
        "role": "focus_r1",
        "source": "pool"
      },
      {
        "set_no": 3,
        "role": "focus_r1",
        "source": "pool"
      },
      {
        "set_no": 4,
        "role": "focus_r1",
        "source": "pool"
      },
      {
        "set_no": 5,
        "role": "focus_r1",
        "source": "score_repack"
      }
    ]
  },
  "markov": {
    "pool_n": 0,
    "repack_n": 0,
    "pool_roles": [],
    "repack_roles": []
  },
  "review": {
    "pool_n": 0,
    "repack_n": 0,
    "pool_roles": [],
    "repack_roles": []
  }
}
```

## 3) 학습

- 역할숙제 행 **1200** (기대 200×3×2=**1200**) · as_of n=**200** min=1037 max=1236
- 소비 뇌=['stat'] · peek as_of≥1237 = **0**
- skill_homework=**0** · learn_state=**0** · brain_review=**0**
- skill_homework=0 → 이번 경로 발권 피드백 없음. 1~5 miss_pattern 숙제 미누적(설계).
- 쓰기=3뇌×2역할. 소비=stat만. markov/review 6~10은 Jaccard/변형 구경로.

### 숙제 n_pos (칸 수)

| 키 | n | mean | min | max | 초반10 | 후반10 |
|----|---|------|-----|-----|--------|--------|
| markov|cover_r3 | 200 | 0 | 0 | 0 | 0 | 0 |
| markov|shape_r2 | 200 | 30.19 | 26 | 35 | 32.8 | 30.1 |
| review|cover_r3 | 200 | 0 | 0 | 0 | 0 | 0 |
| review|shape_r2 | 200 | 30.19 | 26 | 35 | 32.8 | 30.1 |
| stat|cover_r3 | 200 | 21.115 | 3 | 29 | 4 | 22.5 |
| stat|shape_r2 | 200 | 30.19 | 26 | 35 | 32.8 | 30.1 |

## 4) 적중 모니터 (클레임 금지 · 이론 0.80)

| 키 | n | mean_all | mean_best | ge3_best(모니터) |
|----|---|----------|-----------|------------------|
| stat|pool|cover_r3 | 600 | 0.8083 | 1.465 | 14 |
| stat|pool|shape_r2 | 400 | 0.835 | 1.04 | 12 |
| stat|pool|skill_native | 1000 | 0.798 | 1.705 | 25 |
| stat|repack|focus_r1 | 1000 | 0.807 | 1.61 | 24 |

## 5) 서버 HTTP

`{"home_status": 200, "pool_index_n": 0, "draw_index_n": 0, "runs_ok": true, "pred_status": 200, "d1236_status": 200}`

## 6) HARD / SOFT

- HARD (0): []
- SOFT: ['stat-only BT: markov/review cache empty [] n=400 (미실행·버그아님)']

## 7) 판정

- engine_ok=**True** · verdict=**PASS**
- 다음=형 1건(권고 markov 동일 소비). 1237아님.

## 8) 정밀 해석 (초심자용)

1. **프로세스(칸 나누기)** 는 정상이다. 매 회차 1~5번=실력, 6~8번=3등쪽 덮기, 9~10번=2등쪽 모양, 몰아주기 5장. 번호 6개·1~45·중복없음. 역할 이름과 칸 번호가 200회 전부 맞다.
2. **6~8 복습은 과거학습(stat)만 실제로 쓴다.** 숙제표 칸 수가 초반 평균 4 → 후반 22.5 로 늘었다. 표가 쌓이며 다음 회차에만 읽는다(컨닝 0).
3. **markov·review의 6~8 숙제표는 전부 0칸.** 이번 200회는 stat만 돌려서 그 두 뇌의 원장이 없다. 9~10 숙제는 과거 보너스 빈도라 세 뇌가 같은 숫자(~30칸)다. **버그 아님.**
4. **1~5번 실력 학습은 이번 경로에 없다.** 발권(실제 산 5장) 피드백이 0이라 skill_homework·learn_state가 비어 있다. 1~5 엔진 코드는 그대로이고, ‘숙제 누적’만 안 된 것이다.
5. **홈 화면 강제백테 표는 비어 있을 수 있다.** `backtest_runs`/`draw_results`=0. 이번 200회는 원장·풀캐시에 저장됐다. pool-index API는 강제백테 표와만 조인해서 **n_draws=0** 이 된다.
6. **캐시 JSON에 source가 없다.** 저장 함수가 역할만 남기고 경로 라벨을 버린다. 6~8이 숙제를 썼는지는 이전 ON/OFF 비교(178/200 변경)로 이미 확인됨. 엔진 정지 아님.
7. 홈에서 markov/review 1037~1236을 열면 **빈 10세트**가 보인다. stat단독 백테가 빈 칸을 캐시에 넣은 것. 3뇌를 다시 돌리기 전엔 정상.

