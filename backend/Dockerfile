# 1. 파이썬 3.12 버전 이미지 사용
FROM python:3.12-slim

# 2. 컨테이너 내부 작업 디렉토리 설정
WORKDIR /api-server

# 3. 가상환경 생성 및 환경변수 설정 (이게 핵심입니다!)
ENV VIRTUAL_ENV=/app/.venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 4. 라이브러리 설치를 위해 목록 파일 복사
COPY requirements.txt .

# 5. 의존성 라이브러리 설치 (이제 자동으로 venv 안에 설치됨)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. 소스 코드 복사
COPY . .

# 7. FastAPI 서버 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]