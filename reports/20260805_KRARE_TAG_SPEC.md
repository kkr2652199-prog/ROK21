# K-RARE-TAG-SPEC — 3뇌 rare_tags 스키마 · 삽입점 (WIRE OFF)

📅 2026-08-05 · **SPEC** · `RARE_ANNOTATE_WIRE=False`

---

## 1) JSON 스키마 `rare_tag_v1`

후보 set(entry)에 부착:

```json
{
  "set_no": 1,
  "nums": [1, 2, 3, 4, 5, 6],
  "brain_tag": "stat",
  "kind": "repack",
  "assemble": "hy_p45_r123",
  "rare_tags": ["consec_6", "arithmetic_6", "zone_all_low_1_15"],
  "rarity_score": 5.3088,
  "is_ultra_rare_tag": true
}
```

| 필드 | 형 | 의미 |
|------|-----|------|
| `rare_tags` | string[] | `detect_patterns` 키 |
| `rarity_score` | float | \(-log_{10}(p_{min})\) · 태그 없으면 0 |
| `is_ultra_rare_tag` | bool | ultra 키 집합 매칭 |

annotate 전용 반환(`annotate_set`):

| 필드 | 의미 |
|------|------|
| `p_template_min` | 매칭 템플릿 중 최소 군확률 |
| `schema` | `rare_tag_v1` |
| `wire` / `policy` | 현재 스위치 스냅샷 |

---

## 2) 정책 enum (`RARE_POLICY_MODE`)

| 값 | 동작 | 기본 |
|----|------|------|
| `off` | 변경 없음 | **기본** |
| `tag_only` | 태그만 부착 | |
| `exclude_ultra` | ultra 태그 세트 제거 | 형 GO |
| `prefer_ultra` | rarity_score 정렬 | 형 GO |

`RARE_ANNOTATE_WIRE=False`이면 발권 경로에서 **호출하지 않음**.

---

## 3) 삽입점

파일: `app/testlotto/signal_pool.py` · `build_pool_and_repack`  
위치: `by_brain_repack` 구성 직후 · `return` 직전 (주석 블록 존재).

모듈: `app/testlotto/rare_annotate.py`

```
annotate_set / annotate_sets / policy_filter
```

---

## 4) 금지

- 형 GO 없이 WIRE=True  
- best_hits를 학습 입력으로 사용  
- λ/cover 플래그와 동시 ON  
- 「태그 = 당첨확률↑」문서·UI 문구  

---

## 5) 스모크 (진단 only)

```text
python -c "from app.testlotto.rare_annotate import annotate_set; print(annotate_set([1,2,3,4,5,6]))"
```

기대: `wire=False` · `consec_6` 등 태그 · score>0

판정: **SPEC · stub ready · wire OFF**
