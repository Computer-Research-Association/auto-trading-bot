import sys
import os
import logging
import asyncio

# 프로젝트 루트(backend/) 경로 설정
# backend/ 폴더를 sys.path에 추가한다.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

if project_root not in sys.path:
    sys.path.append(project_root)

# 비동기 db 세션 및 모델 임포트
from core.database import AsyncSessionLocal

try:
    from app.domains.log.logger import log_event, LogCategory, LogLevel, LogEvent

except ImportError:

    class LogCategory:
        SYSTEM = "SYSTEM"
        DATA = "DATA"
        STRATEGY = "STRATEGY"
        TRADE = "TRADE"

    class LogLevel:
        INFO = "INFO"
        WARNING = "WARNING"
        ERROR = "ERROR"

    class LogEvent:
        ERROR = "ERROR"
        FETCH_FAIL = "FETCH_FAIL"
        DECISION = "DECISION"

    log_event = None

logger = logging.getLogger(__name__)


async def save_log_to_db(level: str, category: str, event_name: str, message: str):
    """
    트레이딩 봇의 로그를 비동기 방식으로 db에 저장
    유효성 검사 및 네트워크 순단에 대비한 재시도 로직 포함
    """

    # 입력받은 문자열을 Enum 타입으로 변환
    try:
        e_level = LogLevel[level.upper()]
        e_category = LogCategory[category.upper()]
        e_event = LogEvent[event_name.upper()]
    except (KeyError, AttributeError):
        # 매칭되는 enum이 없을 경우 기본값으로 매핑
        e_level = LogLevel.INFO
        e_category = LogCategory.SYSTEM
        e_event = event_name.upper()

    # 메세지 길이 제한
    safe_message = message[:1000]  # 최대 1000자

    # 일시적 db연결 오류 대비
    max_retries = 3
    retry_delay = 1.0

    for attempt in range(max_retries):
        try:
            # 비동기 세션 생성 후 트랜젹션 시작
            async with AsyncSessionLocal() as session:
                # log_event 호출하여 저장 위임
                # commit=True로 즉시 커밋
                await log_event(
                    db=session,
                    level=e_level,
                    category=e_category,
                    event=e_event,
                    message=safe_message,
                    commit=True,
                )
                return

        except Exception as e:
            # 일시적 오류일 경우 재시도
            if attempt < max_retries - 1:
                wait_time = retry_delay * (attempt + 1)
                logger.warning(
                    f"[DB_LOG_RETRY] 저장 실패 (시도 {attempt+1}/{max_retries}): {e}. {wait_time}초 후 재시도."
                )
                await asyncio.sleep(wait_time)
            else:
                # 모든 재시도 실패 시 최종 에러 및 백업 로그 출력
                error_msg = f"[DB_LOG_FATAL] 모든 재시도 실패: {e}"
                print(error_msg)
                # 유실 방지를 위해 콘솔에 최종 백업 내용을 출력
                display_event = e_event.value if hasattr(e_event, "value") else e_event
                print(
                    f"📌 [FINAL_BACKUP] {level} | {category} | {display_event} | {safe_message}"
                )
