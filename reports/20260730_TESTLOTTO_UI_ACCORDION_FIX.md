# TESTLOTTO 예측결과 UI 중복·내부문구 정리 (20260730)

## 원인 (1줄)
`전체 보기`(all) 기본 모드에서 `.lotto-brain-tabs`와 아코디언이 동시 렌더 + warrant/policy 스트립이 예측 영역에 노출.

## 수정
- **Option A**: all 모드 → 탭 바 제거, 3뇌 아코디언만
- 아코디언 헤더: 아이콘·이름·장수·역대전적만 (warrant 배지 제거)
- `lotto-brain-policy` 스트립 예측 영역에서 제거 (하단 warrant details 패널로만)
- pool/repack 서브탭: 데이터 있을 때만 표시

## 브라우저 QA (7021 · 1136회)
| 항목 | 결과 |
|------|------|
| `.lotto-brain-tabs` | 0 |
| 아코디언 | 3 |
| policy/명분 jargon | 없음 |
| 「🎯 3뇌 예측」단일 버튼 | 1 |
| pool+repack 서브탭 | 6 (뇌당 2) |

## 파일
- `app/static/js/testlotto.js`
- `app/static/css/testlotto.css`
- `app/static/index.html` (cache bust `20260730g`)
