# 7021 서버 재가동

시각: 2026-08-31T11:19+09:00 · **OK** · 코드 무수정 · 1239예측 없음

## 0) 한 줄

재가동 요청 시 **7021은 이미 꺼져 있었다.** `python run_v13.py`로 기동. 홈 로그 **GET / 200**. `/api/testlotto/draws?limit=1` **STATUS 200**.

## 1) 종료

- Listen **7021 없음** (Connection refused)
- kill 대상 없음

## 2) 재가동

- 명령: `python run_v13.py` · `D:\ROK21`
- bind: `http://127.0.0.1:7021`
- 로그: `Application startup complete` · `Uvicorn running`
- 확인: 서버로그 `GET /` **200** · draws API **200**
- 실측 `lotto_testlotto.db`: draws min**1** max**1239** · pred_1238**15** · pred_1239**0**
- 1239 당첨행 있음(`11 13 22 32 33 36`+8 · 날짜 2026-08-29). 스케줄러 `collect_latest` 기동 로그 있음. **예측 생성 없음.**

## 3) 다음

형 다음 1건. 1239 예측 아님. DB git 안 함.
