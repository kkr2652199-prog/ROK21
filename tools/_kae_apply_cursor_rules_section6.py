# -*- coding: utf-8 -*-
from pathlib import Path

p = Path("My_Drive_Sync/SUMMARY/CURSOR_RULES.md")
text = p.read_text(encoding="utf-8")
marker_old = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n## 6. 4군 뇌 체계 (현행)\n"
marker_7 = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n## 7. 폴더 구조 (저장 위치)\n"
if marker_old not in text:
    raise SystemExit("old §6 marker not found")
start = text.index(marker_old)
end = text.index(marker_7)
new6 = Path("reports/drafts/20260727_KAC_CURSOR_RULES_§6초안.md").read_text(encoding="utf-8")
# extract from ## 6. to end of ## 6b section from draft — rebuild with separators
block = """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 6. 테스트로또 뇌 체계 (현행 · ROK21 주작업)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 총 **3예측 + 4보조** (coordinator 등록분)

 [예측]
 - stat (`predict_stat_fairy` / statistical)
 - markov (`predict_flow_shaman`)
 - review (`predict_review_king`)

 [보조]
 - miss_aux · pattern_aux · balance_aux · referee_aux

 명분 라벨 SSOT = `WARRANT.md` (코드 미러 `brains/warrant.py`)
 뇌 수/구성 변경 시: STATUS_LATEST 선언 + FINDINGS 갱신

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 6b. 4군(lotto4) 뇌 체계 (별도 · 레거시 문서)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 (구 §6 이관) 총 9뇌 = 7활성 + 2Hidden

 [Ace - 번호 생성]
 v13_seq : LSTM(45→128→64) + Attention + Sigmoid
 v13_struct : XGBoost 7모델 (구조변수 예측)

 [RiskScore - 후보 평가]
 v13_gap : Z-score 갭 분석
 v13_diversity: Jaccard + 십단위 커버리지
 v13_ev : 인기도 역수 기대값

 [Meta - 조합]
 v13_evolution: Ace 2뇌 동적 가중치 (seq, struct만)

 [Commander]
 v13_ensemble : 18C6 전수평가, FINAL = 0.30·cons + 0.30·struct
 + 0.10·gap + 0.20·div + 0.10·ev

 [Hidden - 미호출]
 v13_cdm, v13_cond_prob

 ※ testlotto 작업과 **혼용 금지**. 4군 작업 지시서에만 인용.
 뇌 수 변경 시: 반드시 \"4군 뇌 수 변경 선언\" + STATUS 갱신

"""
text2 = text[:start] + block + text[end:]
# header date
text2 = text2.replace(
    "# 최종 갱신: 2026-07-18 (push 검증·RESUME_HERE 반영)",
    "# 최종 갱신: 2026-07-27 (K-AE · §6 testlotto 현행 · 구9뇌 §6b)",
    1,
)
p.write_text(text2, encoding="utf-8")
print("ok", start, end)
