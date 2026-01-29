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
    retry_delay = 1.0  # 기본 1초 대기

    if OperatingLog is None:
        print(f"[DB_LOG_ERROR] OperatingLog 모델을 찾을 수 없습니다: {safe_message}")
        return

    for attempt in range(max_retries):
        try:
            # 비동기 세션 생성 후 트랜젹션 시작
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    new_log = OperatingLog(
                        level=safe_level,
                        category=safe_category,
                        event_name=safe_event_name,
                        message=safe_message
                    )
                    session.add(new_log)
                    return
        except Exception as e:
            # 일시적 오류일 경우 재시도
            if attempt < max_retries - 1:
                wait_time = retry_delay * (attempt + 1)
                logger.warning(f"[DB_LOG_RETRY] 저장 실패 (시도 {attempt+1}/{max_retries}): {e}. {wait_time}초 후 재시도.")
                await asyncio.sleep(wait_time)
            else:
                # 모든 재시도 실패 시 최종 에러 및 백업 로그 출력
                error_msg = f"[DB_LOG_FATAL] 모든 재시도 실패: {e}"
                print(error_msg)
                logger.error(error_msg)
                # 유실 방지를 위해 콘솔에 최종 백업 내용을 출력
                print(f"📌 [FINAL_BACKUP] {safe_level} | {safe_category} | {safe_event_name} | {safe_message}")
