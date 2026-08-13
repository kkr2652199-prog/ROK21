# K-REPACK-COPY-TIER-AUDIT — 몰아주기 복사·등수 정밀

시각: 2026-08-13T10:57:45+09:00 · 창 1037~1236 · **복사=설계(signal_union)** · ge3미클레임

## 1) 형이 본 것: 몰아주기가 10세트를 그대로 가져온다

- 현재 조립: `signal_union` · 슬롯={'markov': 2, 'stat': 2, 'review': 2} · cap=4
- **버그 아님.** 몰아주기 5장 중 **최대 4장**은 pool 10장 중 점수/신호 상위 세트를 **통째 보존**한다 (`source=pool`).
- 나머지 1장(+중복 시 보충)은 번호 재조합 (`source=score_repack`).
- 실측: repack 3000장 중 pool번호 완전일치 **2400** (비율 **0.8** = 장당 평균 **4.0/5**, cap=4와 일치)
- 캐시 `source` 필드가 비어 있었음 → `payload_from_wf_parts`가 source를 버리던 측정갭. **본턴 패치**(이후 생성분부터 `source=pool|score_repack` 기록)

## 2) 3등 — 2줄이지만 **같은 번호 1장**

원장에 3등 세트가 2행인 이유: **1210회 markov pool set3 = repack set3** 번호가 동일.

- 번호 `[1, 7, 12, 17, 27, 38]` · 당첨 `[1, 7, 9, 17, 27, 38]` 보너스 31 · 5적중(12≠9)
- **고유 3등 조합 = 1건.** 몰아주기가 pool 3등을 통째 보존해서 행이 하나 더 생긴 것.
- **발권 5장에는 없음.** 1210 발권 markov는 `[1,12,13,20,35,45]`(1적중) = 몰아주기 1번 세트. quota가 3등 세트를 안 고름.

그래서 화면에서 「3등 2번 · 몰아주기 3등 1번」으로 보이지만, 산 표 기준으로는 **3등 0**.

## 3) 회차 best 등수 (그 회차에서 제일 좋은 장 1개)

- 발권5: {'r1': 0, 'r2': 0, 'r3': 0, 'r4': 6, 'r5': 21, 'none': 173}
- pool10 only: {'r1': 0, 'r2': 0, 'r3': 1, 'r4': 13, 'r5': 83, 'none': 103}
- repack5 only: {'r1': 0, 'r2': 0, 'r3': 1, 'r4': 10, 'r5': 43, 'none': 146}
- pool또는repack (45장 효과): {'r1': 0, 'r2': 0, 'r3': 1, 'r4': 14, 'r5': 88, 'none': 97}
- 같은 창 1137~1236 n100 vs v5: 이번 {'r1': 0, 'r2': 0, 'r3': 1, 'r4': 9, 'r5': 41, 'none': 49} · v5 r3=0 r4=4 r5=42 (풀경로 모니터)

발권5의 3·4·5등과 풀 45장 등수를 **같은 성적**으로 비교하면 안 된다.
v5와 이번 200회는 창 길이도 다르다(100 vs 200). 겹친 100회만 위 한 줄.

## 4) 뇌 엔진 (발권 전세트 mean · 이미 BT200)

근거 파일 `20260813_KPOST_L12B_RESET_BT200.json` solo mean_all: stat 0.828 / markov 0.808 / review 0.823.
이론 장당 0.80 근처. **서열 선언 안 함.**

샘플 복사:
```
[
  {
    "draw": 1037,
    "brain": "stat",
    "repack_set": 1,
    "source": "no_source_field",
    "source_set_no": null,
    "nums": [
      4,
      5,
      16,
      27,
      32,
      45
    ]
  },
  {
    "draw": 1037,
    "brain": "stat",
    "repack_set": 2,
    "source": "no_source_field",
    "source_set_no": null,
    "nums": [
      5,
      16,
      18,
      27,
      32,
      45
    ]
  },
  {
    "draw": 1037,
    "brain": "stat",
    "repack_set": 3,
    "source": "no_source_field",
    "source_set_no": null,
    "nums": [
      1,
      7,
      14,
      32,
      35,
      45
    ]
  },
  {
    "draw": 1037,
    "brain": "stat",
    "repack_set": 4,
    "source": "no_source_field",
    "source_set_no": null,
    "nums": [
      4,
      16,
      27,
      28,
      32,
      45
    ]
  },
  {
    "draw": 1037,
    "brain": "markov",
    "repack_set": 1,
    "source": "no_source_field",
    "source_set_no": null,
    "nums": [
      4,
      18,
      27,
      34,
      43,
      44
    ]
  },
  {
    "draw": 1037,
    "brain": "markov",
    "repack_set": 2,
    "source": "no_source_field",
    "source_set_no": null,
    "nums": [
      4,
      13,
      18,
      34,
      43,
      44
    ]
  },
  {
    "draw": 1037,
    "brain": "markov",
    "repack_set": 3,
    "source": "no_source_field",
    "source_set_no": null,
    "nums": [
      13,
      17,
      18,
      34,
      43,
      44
    ]
  },
  {
    "draw": 1037,
    "brain": "markov",
    "repack_set": 4,
    "source": "no_source_field",
    "source_set_no": null,
    "nums": [
      5,
      12,
      18,
      33,
      35,
      41
    ]
  }
]
```

## 5) 버그 리스트 → 본턴 패치

| ID | 판정 | 조치 |
|----|------|------|
| HARD (peek/장수/예외) | 0 | 없음 |
| 몰아주기=pool 복사 | **설계** | 패치 안 함 (cap 4/5) |
| 3등 2행 | **중복 집계** | 고유조합 1 · 발권 0 |
| SOFT 창밖 1036 캐시 | 버그 | `auto_feedback` → `allow_compute=False` |
| 캐시 source 누락 | 측정갭 | `payload_from_wf_parts`에 source 보존 |

클릭 L12b 화면 스모크·HOLD 재스윕은 패치 대상 아님 (형 다음 1건).

벤치: `docs/benchmarks/20260813_KREPACK_COPY_TIER_AUDIT.json`
도구: `tools/_k_repack_copy_tier_audit.py`


