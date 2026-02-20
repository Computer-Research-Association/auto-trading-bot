import sys
import os
import logging
import asyncio
from datetime import datetime

# 프로젝트 루트(backend/) 경로 설정
# backend/ 폴더를 sys.path에 추가한다.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

if project_root not in sys.path:
    sys.path.append(project_root)

# 비동기 db 세션 및 모델 임포트
from core.database import AsyncSessionLocal
from core.event_bus import event_bus

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

def _enum_value(x):
    """Enum이면 .value, 아니면 그대로 문자열로"""
    return x.value if hasattr(x, "value") else str(x)

logger = logging.getLogger(__name__)

# 로컬 파일 백업 경로 (DB 장애 시 fallback)
_BACKUP_LOG_PATH = os.path.join(current_dir, "backup.log")


def _write_backup_log(level: str, category: str, event_name: str, message: str):
    """DB 저장 완전 실패 시 로컬 파일에 Fallback 기록 (동기 함수, 스레드풀 아닌 직접 호출)"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {level} | {category} | {event_name} | {message}\n"
        with open(_BACKUP_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as backup_err:
        # 파일 쓰기도 실패하면 콘솔만 남기고 더 이상 할 수 없음
        print(f"[BACKUP_LOG_FAIL] 파일 백업도 실패: {backup_err}")


async def save_log_to_db(level: str, category: str, event_name: str, message: str):
    """
    트레이딩 봇의 로그를 비동기 방식으로 db에 저장
    유효성 검사 및 네트워크 순단에 대비한 재시도 로직 포함
    모든 재시도 실패 시 로컬 backup.log 파일에 Fallback 기록
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
            # 비동기 세션 생성 후 트랜젝션 시작
            async with AsyncSessionLocal() as session:
                # log_event 호출하여 저장 위임
                # commit=True로 즉시 커밋
                created = await log_event(
                    db=session,
                    level=e_level,
                    category=e_category,
                    event=e_event,
                    message=safe_message,
                    commit=True,
                )

                # ✅ SSE 실시간 전송 (DB 저장 성공 직후 publish)
                # created가 None일 수도 있으니 안전하게 처리
                # (log_event가 반환하는 객체 구조에 따라 다를 수 있음. OperatingLog 객체라고 가정)
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 만들어진 객체에서 id/timestamp 추출 시도
                # log_event가 ORM 객체를 리턴한다면 id, timestamp 속성이 있을 것임
                # 만약 리턴값이 없다면(None), 임의로 채워넣음
                # 여기서는 반환값이 있다고 가정하고 getattr로 안전하게 접근
                
                payload = {
                    "id": getattr(created, "id", None),
                    "timestamp": (
                        created.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                        if created and getattr(created, "timestamp", None)
                        else now_str
                    ),
                    "category": _enum_value(e_category),
                    "eventname": _enum_value(e_event),
                    "level": _enum_value(e_level),
                    "message": safe_message,
                }

                # event_bus는 메모리 기반이므로 "같은 프로세스" 안의 SSE 연결에 즉시 전달됨
                await event_bus.publish(payload)
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
                # 모든 재시도 실패 시 최종 에러
                display_event = e_event.value if hasattr(e_event, "value") else e_event
                error_msg = f"[DB_LOG_FATAL] 모든 재시도 실패: {e}"
                # 1. 콘솔 출력 (기존 동작 유지)
                print(error_msg)
                print(f"📌 [FINAL_BACKUP] {level} | {category} | {display_event} | {safe_message}")
                # 2. 로컬 파일 Fallback (신규 추가)
                _write_backup_log(level, category, display_event, safe_message)
