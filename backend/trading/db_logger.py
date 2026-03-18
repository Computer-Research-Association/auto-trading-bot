import sys
import os
import time
import logging
import asyncio
from datetime import datetime

# 프로젝트 루트(backend/) 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

if project_root not in sys.path:
    sys.path.append(project_root)

# 비동기 DB 세션 임포트
from core.database import AsyncSessionLocal
from core.event_bus import event_bus

try:
    # 로그를 DB에 저장하는 함수(도메인 로거)
    # logger.py에 정의된 create_log 사용
    from app.domains.log.logger import create_log
except ImportError:
    create_log = None


# Import 실패 여부와 상관없이 항상 사용 가능한 Enum 정의
class LogCategory:
    SYSTEM = "SYSTEM"
    DATA = "DATA"
    STRATEGY = "STRATEGY"
    TRADE = "TRADE"

    @classmethod
    def __class_getitem__(cls, k):
        return getattr(cls, k)


class LogLevel:
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

    @classmethod
    def __class_getitem__(cls, k):
        return getattr(cls, k)


class LogEvent:
    ERROR = "ERROR"
    FETCH_FAIL = "FETCH_FAIL"
    VALID_FAIL = "VALID_FAIL"
    DECISION = "DECISION"
    SYNC = "SYNC"
    BUY = "BUY"
    SELL = "SELL"
    STOPLOSS = "STOPLOSS"
    HEARTBEAT = "HEARTBEAT"
    COMMAND = "COMMAND"
    ENGINE_START = "ENGINE_START"

    @classmethod
    def __class_getitem__(cls, k):
        return getattr(cls, k)


def _enum_value(x):
    """Enum이면 .value, 아니면 그대로 문자열로"""
    return x.value if hasattr(x, "value") else str(x)


logger = logging.getLogger(__name__)

# 로컬 파일 백업 경로 (DB 장애 시 fallback)
_BACKUP_LOG_PATH = os.path.join(current_dir, "backup.log")

# 중복 방지를 위한 인메모리 캐시 (최대 3초 내 동일 로그 무시)
_log_cache = {}
_CACHE_TIMEOUT = 3.0

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
    트레이딩 봇의 로그를 비동기 방식으로 DB에 저장
    - 유효성 검사 및 네트워크/DB 일시 장애 대비 재시도 로직 포함
    - 단기 시간 내 (3초) 동일 메시지 중복 기록 방지 (Idempotency)
    - 저장 성공 시 SSE(EventBus)로 즉시 publish 해서 프론트가 실시간 수신 가능하게 함
    - 모든 재시도 실패 시 로컬 backup.log 파일에 Fallback 기록
    """
    global _log_cache

    if create_log is None:
        # 도메인 로거 import가 안 된 경우: DB 저장 불가
        logger.error("[DB_LOG] create_log import 실패로 DB 저장 불가")
        return

    # 입력받은 문자열을 Enum 타입(혹은 fallback 상수)으로 변환
    try:
        # Enum 형태(권장)
        e_level = LogLevel[level.upper()] if hasattr(LogLevel, "__getitem__") else LogLevel.INFO
        e_category = LogCategory[category.upper()] if hasattr(LogCategory, "__getitem__") else LogCategory.SYSTEM
        e_event = LogEvent[event_name.upper()] if hasattr(LogEvent, "__getitem__") else event_name.upper()
    except Exception:
        # 매칭되는 enum이 없을 경우 기본값으로 매핑
        e_level = getattr(LogLevel, "INFO", "INFO")
        e_category = getattr(LogCategory, "SYSTEM", "SYSTEM")
        e_event = event_name.upper()

    # 메시지 길이 제한
    safe_message = (message or "")[:1000]  # 최대 1000자

    # 중복 방지 로직 (Idempotency)
    now = time.time()
    log_hash = hash((level, category, event_name, safe_message))
    
    # 캐시 만료 정리
    expired_keys = [k for k, v in _log_cache.items() if now - v > _CACHE_TIMEOUT]
    for k in expired_keys:
        del _log_cache[k]
        
    if log_hash in _log_cache:
        return  # 3초 내에 동일한 로그 요청이 있었으므로 무시
        
    _log_cache[log_hash] = now

    # 일시적 DB 연결 오류 대비
    max_retries = 3
    retry_delay = 1.0

    for attempt in range(max_retries):
        try:
            async with AsyncSessionLocal() as session:
                # ✅ DB 저장
                # logger.py 정의에 맞춰 event_name으로 수정 (create_log 시그니처)
                created = await create_log(
                    db=session,
                    level=e_level,
                    category=e_category,
                    event_name=e_event,  # 인자명: event -> event_name
                    message=safe_message,
                    commit=True,
                )

                # ✅ SSE 실시간 전송 (DB 저장 성공 직후 publish)
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

                return  # ✅ 성공

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
                display_event = _enum_value(e_event)
                error_msg = f"[DB_LOG_FATAL] 모든 재시도 실패: {e}"
                logger.error(error_msg)

                # 유실 방지를 위해 콘솔에 최종 백업 내용을 출력
                print(error_msg)
                print(f"📌 [FINAL_BACKUP] {level} | {category} | {display_event} | {safe_message}")
                
                # ✅ 로컬 파일 Fallback (복구됨)
                _write_backup_log(level, category, display_event, safe_message)
                return
