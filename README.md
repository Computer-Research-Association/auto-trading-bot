# 📈 Auto Trading Bot (가상화폐 자동매매 봇)

> **업비트(Upbit) API를 활용한 가상화폐 자동매매 및 포트폴리오 관리 시스템입니다.**

이 프로젝트는 기술적 지표(RSI, 이동평균선, 볼린저 밴드 등)를 바탕으로 24시간 자동으로 가상화폐를 매매하는 봇 시스템입니다.  
FastAPI 백엔드에서 안정적인 매매 로직과 백그라운드 스케줄러가 동작하며, React 기반 대시보드를 통해 실시간 수익률과 매매 체결 로그를 손쉽게 모니터링할 수 있습니다.

---

## ✨ 주요 기능

- **자동 매매 알고리즘:** `pandas-ta`를 활용한 기술적 지표 계산 및 조건부 매수/매도 로직 (RSI, 볼린저 밴드, 스캘핑 장착)
- **실시간 모니터링:** SSE(Server-Sent Events)를 활용한 실시간 봇 상태 및 시스템 로그(체결 내역, 에러) 스트리밍
- **포트폴리오 수익률 관리:** 일간/시간별 투자 수익률(PnL) 스냅샷 자동 저장 및 시각화 차트 제공 (`Recharts`)
- **백그라운드 자동화:** `APScheduler`를 이용한 상시 자산 스냅샷, 업비트 매매 내역 동기화, 오래된 로그 자동 정리

---

## 🛠️ 기술 스택 (Tech Stack)

### Frontend 
- **Framework & UI:** React 19, Vite, TypeScript
- **Visualization Component:** Recharts (수익률 그래프)
- **Network:** Axios (단일 및 공통 API 관리)

### Backend
- **Framework:** FastAPI, Uvicorn
- **Language:** Python 3
- **Core Engine:** PyUpbit (업비트 주문 연동), Pandas / Numpy (데이터 파싱)
- **Real-time & Schedule:** SSE 지원 (`sse-starlette`), APScheduler

### Database & Infra
- **Database:** PostgreSQL 17 (ORM: SQLAlchemy 2.0, SQLModel, 비동기 드라이버 asyncpg)
- **Migration:** Alembic
- **Deploy:** Docker & Docker Compose

---

## 🚀 시작 가이드 (Getting Started)

프로젝트를 로컬에서 구동하려면 다음 설정과 프로그램이 필요합니다.
- [Node.js](https://nodejs.org/) (v18 또는 v22+ 권장)
- [Python 3.10+](https://www.python.org/)
- [Docker & Docker Compose](https://www.docker.com/) (필수)

### 1. 프로젝트 다운로드 (Clone)
```bash
git clone https://github.com/사용자계정/auto-trading-bot.git
cd auto-trading-bot
```

### 2. 백엔드/DB 환경 변수 설정
`backend` 디렉토리에 `.env` 파일을 생성하고, 본인의 업비트 API 키와 DB 정보를 입력합니다.
**`backend/.env`**
```env
UPBIT_ACCESS_KEY=당신의_업비트_ACCESS_KEY
UPBIT_SECRET_KEY=당신의_업비트_SECRET_KEY
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=gold_db
```

### 3. 서버(DB/Backend) 실행
이 프로젝트는 Docker Compose를 활용하여 데이터베이스와 백엔드를 한 번에 올릴 수 있습니다.
최상위 경로(`auto-trading-bot/`)에서 아래 명령어를 실행하세요.
```bash
docker-compose up -d --build
```
> 구동 확인 ➜ `http://localhost:8000/docs` (FastAPI Swagger UI 확인 가능)

### 4. 프론트엔드 스크립트 실행
백엔드가 켜졌다면, 프론트엔드를 실행하여 화면을 띄웁니다.
```bash
cd frontend
npm install
npm run dev
```
> 구동 확인 ➜ `http://localhost:5173` (React 대시보드 진입)

---

## 📂 주요 폴더 구조 (Project Structure)

```text
auto-trading-bot/
├── backend/                   # 봇 구동 및 핵심 API 서버
│   ├── app/                   # 도메인 별 비즈니스 로직 (bot, coin, log, performance 등)
│   ├── core/                  # DB 연결 설정, CORS/로거 모듈
│   ├── trading/               # 매매 판단 기반 클래스 및 백테스팅(알고리즘) 함수
│   ├── alembic/               # 데이터베이스 마이그레이션 도구 세팅
│   ├── .env                   # 백엔드 환경변수 세팅
│   └── requirements.txt       # 파이썬 의존 라이브러리 목록
├── frontend/                  # 관리자 대시보드 UI
│   ├── src/
│   │   ├── components/        # 차트, 로그, 헤더 등 컴포넌트 목록
│   │   ├── lib/               # API 통신 함수 모음 (`api.ts` 등)
│   │   ├── pages/             # 대시보드 메인 레이아웃 
│   │   └── App.tsx / main.tsx # 앱 진입점
│   ├── .env.local             # 로컬 테스트용 환경변수 모음
│   └── vite.config.js         # 번들러 환경 세팅
├── postgres_data/             # Docker 볼륨 (DB 데이터를 로컬에 영구 보존용 맵핑)
└── docker-compose.yml         # 백엔드 및 DB 컨테이너 세팅 파일
```
