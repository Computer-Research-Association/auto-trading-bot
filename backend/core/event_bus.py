import asyncio


class EventBus:
    def __init__(self):
        self.subscribers: list[asyncio.Queue] = []

    async def publish(self, message: dict):
        for queue in self.subscribers:
            await queue.put(message)

    def subscribe(self, queue: asyncio.Queue | None = None) -> asyncio.Queue:
        """
        - queue를 넘기면: 기존 큐를 등록 (133 방식 호환)
        - queue를 안 넘기면: 새 큐 생성 후 반환 (115 SSE 방식)
        """
        if queue is None:
            queue = asyncio.Queue()

        self.subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        if queue in self.subscribers:
            self.subscribers.remove(queue)


event_bus = EventBus()