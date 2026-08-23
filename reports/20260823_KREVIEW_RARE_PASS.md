# K-REVIEW-RARE-PASS (2026-08-23)

- **판정:** `APPLY_OK` · 전체조합 반영 · 엔진 패스 · 몰아주기 미접촉
- 시각: 2026-08-23T12:05:33+09:00
- 형: 814만 동일확률. 얇은 형태는 패스. 당첨회 분석 저장을 조합·엔진이 읽게. 한 단계. 1238/1239 달력은 이번 작업 아님.
- 근거: `docs/benchmarks/20260823_KREVIEW_RARE_PASS.json`
- 선행: `20260823_KREVIEW_RARE_SLICE` (814만 전수+당첨1–1237 형태표)

## 무엇을 저장했나

개별 조합 확률은 모두 1/8,145,060. 갈라내는 것은 **얇은 형태 조각**(확률의 확률).
예시 `1-2-3-4-5-6`은 클래스 중 하나일 뿐(run6). 사람+추첨기계가 극소 형태를 패스할 수 있게 목록을 저장.

표=`testlotto_rare_pass_combos` · 엔진 `should_pass()` · 전체조합 탭 극소 열·「극소만 보기」가 **같은 목록**을 읽는다.

| 항목 | 값 |
|------|-----:|
| unique 목록 | **21245** |
| 814만 대비 | 21245 / 8145060 ≈ 0.002609 |
| tag합(중복포함) | 21436 |
| 겹침 | 191 |
| 20분할 스탬프 | parts **20** · marked **21245** |
| 1236 review pool rare | **0** / 10 |
| pred_1237 | **0** |
| pred_1239 | **0** |
| draws MAX | **1238** |

## 1단계 클래스 → 조합번호

STEP1 = 공간 얇고 당첨1–1237 = 0회. run4(당첨6)·전홀짝(19/17)은 **안 자름**.

| tag | 공간(SLICE) | 목록 count | 당첨1–1237 |
|-----|------------:|-----------:|-----------:|
| run6 | 40 | 40 | 0 |
| run5plus | 1600 | 1600 | 0 |
| arith6 | 180 | 180 | 0 |
| gap8 | 210 | 210 | 0 |
| split_l3h3 | 14400 | 14400 | 0 |
| zone_1_15 | 5005 | 5005 | 0 |
| exact_123_434445 | 1 | 1 | 0 |

`1-2-3-4-5-6` = combo_no **1** · run6(+run5plus). `1-2-3-43-44-45` = combo_no **11480**.

## 엔진

- 금액뇌 `engine.generate` — `REVIEW_RARE_SLICE_WIRE` 켜면 `should_pass(pick)` 패스(다시 뽑음)
- 목록 비어도 `is_step1_rare` 폴백
- 몰아주기(`score5`) **미접촉**
- 1237/1239 신규예측 **없음**

## 전체조합 탭

- 열 **극소** · 배지=`pass_tags` (STEP1만. run4plus·span 제외)
- 체크 **극소만 보기** → `GET /allcombos?rare_only=true` (목록 21245 · 178페이지/120행)
- 요약줄 `극소형태 21,245건(엔진 패스)`
- CSV `rare_pass,rare_tags`
- 브라우저 확인: No.1=`1 2 3 4 5 6` 배지 `run6,run5plus,arith6,zone_1_15` · 1238당첨 `2 13 18 32 38 42`=No.1829370 극소 `—` · 당첨표시 1238회
- part DB 스탬프는 로컬만 · **git 커밋 금지**

## 추가 아이디어 (실측 후 이번 목록에 안 넣음)

- 이중3연속(dual 3-run): 공간 **780** · 당첨 **1**회(`30,31,32,35,36,37`) → STEP1 조건(0회) 불충족
- run4 / 전홀짝 / gap7 / zone_16_30 / zone_31_45: 당첨 있음 → 패스 목록 제외

## 롤백

- `REVIEW_RARE_SLICE_WIRE=False` (예측 패스 끔)
- 전체조합 열은 코드 되돌림. part `rare_pass` 컬럼은 로컬 잔존(무시 가능)

## 파일

- `app/testlotto/brains/review_brain/rare_pass_store.py`
- `app/testlotto/brains/review_brain/engine.py`
- `app/testlotto/models.py` (`testlotto_rare_pass_combos`)
- `app/lotto4/all_combos_service.py` · `app/lotto4/v13_routes.py`
- `app/static/index.html` · `js/lotto4.js` · `css/lotto4.css`
- `tools/_k_review_rare_pass.py`
- `docs/benchmarks/20260823_KREVIEW_RARE_PASS.json`
- `reports/20260823_KREVIEW_RARE_PASS.md`

우열·적중↑ 클레임 금지. 다음 형태조각=형 1건.
