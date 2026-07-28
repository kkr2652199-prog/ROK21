# K-DETAIL-CUTOFF — detail/draw CUTOFF 회귀 수정

**일자:** 20260728  
**HEAD:** `8c32f72` (패치 로컬 · 미커밋)

---

## 증상

- `GET /api/testlotto/detail/draw/1234` → **500**
- 메인 테스트로또 **1234 선택** → `로드 실패: Unexpected token 'I'...`
- 상세페이지 당첨·오답노트 **빈 화면**

## 원인

`get_draw_detail()` 이 `aux_referee.describe()` → `get_referee_weights()` → `get_all_learn_states()` 를 **set_learn_as_of 없이** 호출.  
CUTOFF 기본 ON(K-T)에서 `ValueError` 발생.

## 수정 (최소 diff)

`app/testlotto/detail_service.py` · `get_draw_detail()`:

- 당첨 데이터 확인 후 `set_learn_as_of(draw_no)`
- `finally` 에서 이전 as_of 복원 (walkforward 와 동일 패턴)

동결 토큰·boost·random.choices **미수정**.

## 검증

| 게이트 | 결과 |
|--------|------|
| `_kdetail_cutoff_verify.py` | **verify_pass** |
| detail/1234 | 200 · actual `[1,15,19,31,35,43]` · brains=3 · aux=4 |
| detail/1235 | 200 · error=미추첨 (정상) |
| 브라우저 1234 | 당첨번호·3뇌 탭·명분패널 **로드 OK** |

벤치: `docs/benchmarks/20260728_KDETAIL_cutoff_fix.json`

## 다음

`K-AWAIT` — 1235 발표 후 `--execute`
