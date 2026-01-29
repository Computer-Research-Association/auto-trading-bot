import sys
import os
import logging
import asyncio

# 프로젝트 루트(backend/) 경로 설정
# backend/ 폴더를 sys.path에 추가한다.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

if project_root not in sys.path:
    sys.path.append(project_root)

# 비동기 db 세션 및 모델 임포트
from core.database import AsyncSessionLocal
try:
    from app.domains.log.models import OperatingLog

except ImportError:
    OperatingLog = None


logger = logging.getLogger(__name__)

async def save_log_to_db(level: str, category: str, event_name: str, message: str):
    """
    트레이빙 봇의 로그를 비동기 방식으로 db에 저장
    유효성 검사 및 네트워크 순단에 대비한 재시도 로직 포함
    """

    # 컬럼별 최대 길이 제한
    safe_level = level[:20]  # INFO, WARNING, ERROR가 해당
    safe_category = category[:50]  # STRATEGY:RSI_BB가 해당
    safe_event_name = event_name[:100]  # ENGINE_START, HEARTBEAT가 해당
    safe_message = message[:1000]  # 상세 메세지는 넉넉하게

    # 재시도 설정
    max_retries = 3  # 최대 3회 시도
    retry_delay = 1.0  #  기본 1초 대기

    if OperatingLog is None:
        print(f"[DB_LOG_ERROR] OperatingLog 모델을 찾을 수 없습니다: {safe_message}")
