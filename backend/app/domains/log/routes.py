import asyncio
import json
import logging
from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from core.deps import get_database
from core.event_bus import event_bus
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
    start_date: date | None = Query(None, description="YYYY-MM-DD"),
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

    async def event_generator():
        # 클라이언트별 구독 큐 생성
        queue = event_bus.subscribe()

        # 표준 SSE 재연결 헤더(참고용)
        # - 이 값으로 "누락 로그 자동 재전송"을 하려면 서버가 별도 버퍼/브로커가 있어야 함
        # - 우리는 히스토리는 GET /v1/logs 로 받는 구조이므로 여기서는 참고만
        _ = request.headers.get("last-event-id")

        try:
            while True:
                # 클라이언트가 끊기면 종료
                if await request.is_disconnected():
                    break

                # 새 이벤트를 기다림(완전 실시간)
                message = await queue.get()

                # keep-alive 용도로 가끔 ping을 보내고 싶으면 이 구조로 확장 가능
                # (현재는 publish가 들어올 때만 이벤트가 나감)

                # payload가 dict가 아니면 dict로 맞춰줌
                if not isinstance(message, dict):
                    message = {"message": str(message)}

                # SSE 포맷으로 전송
                # - id: 브라우저의 Last-Event-ID 갱신에 사용 가능(있으면 넣어줌)
                # - event: 프론트에서 addEventListener로 분기하고 싶으면 사용(선택)
                event_id = message.get("id")
                event_name = message.get("eventname") or message.get("event_name")  # 호환 처리

                yield {
                    "id": str(event_id) if event_id is not None else None,
                    "event": str(event_name) if event_name else None,
                    "data": json.dumps(message, ensure_ascii=False),
                }

        except asyncio.CancelledError:
            logger.info("SSE connection cancelled by client")
            raise
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            raise
        finally:
            # 구독 해제(메모리 누수 방지)
            event_bus.unsubscribe(queue)

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # nginx 사용 시 버퍼링 방지
    }

    return EventSourceResponse(event_generator(), headers=headers)
