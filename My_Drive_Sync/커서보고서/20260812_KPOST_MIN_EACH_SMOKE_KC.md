# K-POST-MIN-EACH-SMOKE + K-C

시각: 2026-08-12T07:27:38+09:00 · 단계⑨⑩ · seed=42

## ⑨ 판정 **SMOKE_OK**
- min_each=1 · quota=`{'stat': 1, 'markov': 3, 'review': 1}`
- prefer=0.299535 · prize=-0.106851 · hit=0.321667(모니터)

## ⑩ K-C 판정 **STALE_CLOSE**
- avgs=`{'stat': 0.6667, 'markov': 0.8667, 'review': 0.8}`
- live=`{'stat': 0.23531, 'markov': 0.41177, 'review': 0.35292}`
- 최저avg=`stat` · 최고가중=`markov`
- reverse_ranking=False → 구 K-C는 legacy 1+avg*0.15·균등 시기. K-M/J/refill 후 재실측.
