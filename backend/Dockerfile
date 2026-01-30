# 1. 파이썬 3.12 버전 사용 (pandas-ta 및 기타 의존성 지원을 위해)
FROM python:3.12-bookworm

# 2. 컨테이너 내부의 작업 디렉토리 설정
WORKDIR /app

# 3. 라이브러리 설치를 위해 목록 파일 먼저 복사
COPY requirements.txt .

# 4. 의존성 라이브러리 설치
# bookworm 이미지는 build-essential 등을 포함하고 있어 더 안정적입니다.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드 복사
COPY . .

# 6. FastAPI 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]