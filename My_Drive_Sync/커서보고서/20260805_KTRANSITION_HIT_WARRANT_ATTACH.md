# K-TRANSITION-HIT-WARRANT-ATTACH (2026-08-05)

- **판정:** `PASS` · wire=`False`
- hit_warrant_log rows=**1134** (transition upsert=1134)
- evolve notes updated=**3402** · weight_all_zero=**True**
- TRANSITION_V1_WIRE=**False** · HIT_WARRANT_ATTACH=**True**

## spot 1235
- `{'draw_no': 1235, 'summary_text': 'HIT-WARRANT carry=[15, 43] exp=4/6 [6:struct_consec; 7:trans_top15+struct_consec@14; 11:unexplained; 15:carry+trans_top15@7; 39:unexplained; 43:carry]', 'n_explained': 4, 'n_unexplained': 2}`

## 해석
- 명분 라벨을 **학습/설명 로그**에만 부착.
- 발권 confidence·quota·WIRE 변경 없음.
- 카탈로그 비율 SSOT는 prior HIT-WARRANT JSON.

- tool: `tools/_k_transition_hit_warrant_attach.py` · module: `app/testlotto/hit_warrant.py`
