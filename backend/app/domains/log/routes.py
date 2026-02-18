import asyncio
import json
import logging
from datetime import date
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from core.deps import get_database
from core.database import AsyncSessionLocal # 매 폴링마다 세션 생성을 위해 임포트
from app.domains.log import service, schema

router = APIRouter(prefix="/v1/logs", tags=["logs"])
logger = logging.getLogger(__name__)

@router.get("", response_model=schema.LogListResponse)
async def get_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    level: str | None = None,
    category: str | None = None,
    search: str | None = None,
    start_date: date | None = Query(None, description="YYYY-MM-DD"), # date 타입으로 자동 검증
    end_date: date | None = Query(None, description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_database),
):
    items, total_count = await service.list_logs(
        db,
        page=page,
        limit=limit,
        level=level,
        category=category,
        search=search,
        start_date=start_date,
        end_date=end_date,
    )
    return {"items": items, "total_count": total_count}

@router.get("/stream")
async def stream_logs(request: Request):
    async def log_publisher():
        # Last-Event-ID 헤더 확인 (표준 대응)
        last_event_id = request.headers.get("last-event-id")
        last_id = int(last_event_id) if last_event_id and last_event_id.isdigit() else 0
        
        try:
            while True:
                # 클라이언트 연결 끊김 감지
                if await request.is_disconnected():
                    break
                
                # 매 폴링마다 새로운 세션을 열어 안전하게 조회 (세션 점유 및 stale 방지)
                async with AsyncSessionLocal() as db:
                    new_logs = await service.get_new_logs(db, last_id)
                    for log in new_logs:
                        last_id = log.id
                        yield {
                            "id": str(log.id), # 브라우저의 Last-Event-ID 갱신
                            "data": json.dumps({
                                "id": log.id,
                                "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                "category": log.category,
                                "eventname": log.event_name, # schema의 alias와 일치하게 mapping
                                "level": log.level,
                                "message": log.message
                            }, ensure_ascii=False)
                        }
                
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("SSE connection cancelled by client")
            raise
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            raise

    # 필수 및 권장 헤더 세트
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no", # nginx 버퍼링 방지
    }
    
    return EventSourceResponse(
        log_publisher(),
        headers=headers
    )
