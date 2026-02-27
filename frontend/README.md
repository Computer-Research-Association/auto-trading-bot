# Auto Trading Bot - UI (Gold Bar)
> Auto Trading Bot에서 UI를 담당하고 있는 프론트엔드입니다.

---

## 🛠 Tech Stack
- React 19
- Typescript
- Vite
- Recharts (차트 라이브러리)
- Axios (백엔드 API 통신)

---

## 💻 개발 환경
이 프로젝트의 프론트엔드는 다음 환경에서 개발 및 실행됩니다.
- node.js: v22 권장
- Package Manager: npm (Node Package Manager)
- Language: Typescript ('tsx')
- Build Tool: Vite (빠른 HMR 및 빌드 지원)
- UI & Styling: React 19, 표준 css, Reacharts (차트 라이브러리)

---

## 🚀 실행 스크립트
frontend/ 디렉토리에서 반드시 npm install로 패키지를 먼저 설치해아함

    npm install

프로젝트를 처음 클론받은 후 구동에 필요한 모든 의존성 패키지를 설치합니다. (최우선으로 실행!)

    npm run dev

가장 자주 사용하는 명령어입니다. 개발용 로컬 서버를 실행합니다.

    npm run build

서비스를 실제 서버에 배포하기 전, 코드르 최적화하고 하나로 압축하는 명령어입니다.

실행 시
```
dist/
```
폴더가 생성되며, 이 폴더 안의 파일들을 서버에 올리게 됩니다.

    npm run lint

코드에 오타가 있거나, 정해진 규칙(ESLint)에 어긋나는 코드가 없는지 전체적으로 검사해주는 명령어입니다.

---

## 📂 폴더 구조

```text
frontend/
├── src/
│   ├── components/       # 재사용 가능한 UI 컴포넌트
│   │   ├── Assets.tsx
│   │   ├── Loading.tsx
│   │   ├── History.tsx
│   │   ├── Log.tsx       # 실시간 로그 필터/모니터링
│   │   ├── ProfitLoss.tsx# 수익률 차트
│   │   └── StrategyPanelV2.tsx
│   ├── lib/              # 백엔드 연동 API 함수 모음
│   │   ├── api.ts
│   │   ├── assets.api.ts
│   │   ├── history.api.ts
│   │   ├── log.api.ts
│   │   ├── orderbook.api.ts
│   │   └── performance.api.ts
│   ├── pages/            # 페이지 단위 레벨 컴포넌트
│   │   └── Dashboard.tsx
│   ├── App.tsx           # 메인 레이아웃
│   ├── main.tsx          # React 앱 진입점
│   └── index.css         # 글로벌 스타일 설정
├── .env                  # 환경 변수 기본값 (Git 포함)
├── .env.local            # 로컬 환경 변수 (Git 제외, 직접 생성 필요)
├── package.json          # 프로젝트 의존성 및 스크립트 정보
└── vite.config.js        # Vite 빌드 설정
