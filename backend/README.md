# 📈 Auto Trading Bot Backend

이 디렉토리는 **가상화폐 자동매매 봇(Auto Trading Bot)**의 백엔드 서버 코드를 포함하고 있습니다. FastAPI를 기반으로 데이터베이스, 업비트 API 연동, 백그라운드 스케줄러, 실시간 SSE 스트리밍 등의 역할을 담당합니다.

## ✨ 주요 기능

- **FastAPI 기반 REST API:** 프론트엔드 대시보드와 서버 간 연동되는 고성능 비동기 API 엔드포인트 제공
- **자동 매매 핵심 엔진 (Core Engine):** 
  - `pyupbit`와 `pandas-ta`를 활용하여 24시간 실시간 시세 조회
  - 기술적 지표(RSI, 볼린저 밴드 등)를 계산 후 조건부 자동 매매 체결
- **백그라운드 스케줄러 (`APScheduler`):**
  - **포트폴리오 스냅샷:** 주기적(일 단위 혹은 시간 단위)으로 현재 자산 현황과 수익률(PnL)을 데이터베이스에 저장
  - **로그 정리:** 오래된 로그(예: 7~30일 이상)를 자동으로 정리하여 데이터베이스 용량 최적화 및 안정성 확보
  - **매매 내역 동기화:** 업비트 거래 내역 주기적 확인 및 DB 동기화
- **실시간 데이터 스트리밍 (SSE 지원):** 서버 환경에서 대시보드로 봇의 작동 상태 및 시스템 로그(체결 내역, 에러 알림 등)를 실시간 스트리밍하기 위해 `sse-starlette` 사용
- **데이터베이스 연동:** 비동기 PostgreSQL 드라이버(`asyncpg`), `SQLAlchemy` 2.0 및 `Alembic`을 활용한 견고한 데이터 모델링 및 마이그레이션 관리

## 🛠️ 기술 스택 (Tech Stack)

- **Framework:** FastAPI, Uvicorn
- **Language:** Python 3
- **Database:** PostgreSQL (asyncpg), SQLAlchemy 2.0, SQLModel, Alembic
- **Exchange API:** pyupbit
- **Data Analysis:** pandas, numpy, pandas-ta
- **Task Scheduler:** APScheduler
- **Real-time Streaming:** sse-starlette, websockets

## 🚀 환경 변수 설정

백엔드를 실행하기 전 `backend/.env` 파일을 작성해야 합니다. 제공되는 `.env.example` 파일을 참고하여 각 항목을 작성하세요.

```env
# Upbit API Keys
UPBIT_ACCESS_KEY=your_upbit_access_key
UPBIT_SECRET_KEY=your_upbit_secret_key

# Database (PostgreSQL)
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=gold_db
# Docker Compose 구동 시 db, 로컬 구동 시 localhost로 설정
DB_HOST=db
DB_PORT=5432
```

## 📦 시작 가이드 (로컬 직접 실행)

> 💡 **Docker로 실행하기 (권장):** 최상위 디렉토리(`auto-trading-bot`)에서 루트 `README.md`의 안내에 따라 `docker-compose up -d --build`를 통해 DB와 백엔드를 함께 구동하는 것을 권장합니다.
>
> 부득이 로컬에서 직접 백엔드를 띄울 경우 아래 절차를 따릅니다.

### 1. 파이썬 가상환경 생성 및 의존성 설치

```bash
cd backend
python -m venv .venv

# Windows 환경:
# .venv\Scripts\activate
# Mac / Linux 환경:
source .venv/bin/activate  

pip install -r requirements.txt
```

### 2. DB 마이그레이션 적용 (Alembic)

생성된 데이터베이스에 테이블 스키마를 동기화합니다. (위 환경 변수에 연결 가능한 DB 정보가 세팅되어야 함)
```bash
alembic upgrade head
```

### 3. FastAPI 서버 실행

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

> 서버가 성공적으로 실행되면, 브라우저에서 `http://localhost:8000/docs` 로 접속해 FastAPI Swagger UI (API 문서)를 확인할 수 있습니다.

## 📂 백엔드 주요 폴더 구조

```text
backend/
├── app/                  # FastAPI 메인 애플리케이션 및 도메인 로직
│   ├── api/              # API 라우터 및 엔드포인트 정의
│   ├── domains/          # 기능별 비즈니스 로직 및 모델 (bot, coin, log, portfolio 등 분리)
│   ├── utils/            # 공통 유틸리티 모음
│   └── main.py           # FastAPI 앱 생성 및 Lifespan(스케줄러 등록, 봇 인스턴스 초기화) 정의
├── core/                 # 핵심 애플리케이션 설정 (데이터베이스 커넥션, CORS 관리, 글로벌 Logger 등)
├── trading/              # 자동 매매 시스템의 두뇌 (TradingBot 클래스 구현 및 매수/매도 판단 알고리즘 파트 등)
├── alembic/              # 테이블 스키마 이력 및 마이그레이션 스크립트 도구 세팅
├── Dockerfile            # 백엔드 서버 도커 이미지 빌드 파일
├── requirements.txt      # 파이썬 외부 패키지 의존성 목록
└── alembic.ini           # Alembic 동작을 제어하는 설정 파일
```
