# 7021 서버 종료 후 재가동

시각: 2026-08-14T20:50+09:00 · **OK** · 코드/DB 무수정 · 1237아님

## 0) 한 줄

종료 요청 시 **7021은 이미 꺼져 있었다.** `python run_v13.py`로 재기동했고 홈 **HTTP 200**.

## 1) 종료

- `netstat`/Listen **7021 없음**
- `python.exe` 중 `run_v13.py` **없음** (LSP만)
- kill 대상 없음

## 2) 재가동

- 명령: `python run_v13.py` · `D:\ROK21`
- bind: `http://127.0.0.1:7021`
- 로그: `Application startup complete` · `Uvicorn running`
- 확인: `Invoke-WebRequest /` → **STATUS=200** LEN=34709

## 3) 다음

형 다음 1건(권고=markov 동일 소비). 1237 아님.
