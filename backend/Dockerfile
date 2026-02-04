# 1. 파이썬 3.11 슬림 버전 이미지 사용 (가볍고 빠름)
FROM --platform=linux/amd64 python:3.12-bookworm

# 2. 컨테이너 내부의 작업 디렉토리 설정
WORKDIR /app

# 3. 라이브러리 설치를 위해 목록 파일 먼저 복사
COPY requirements.txt .

# 4. 의존성 라이브러리 설치
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드 복사 (개발 시에는 볼륨 설정으로 로컬 코드와 동기화됨)
COPY . .

# 6. FastAPI 서버 실행 (Hot Reload 모드 활성화)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]