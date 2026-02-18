import asyncio

class EventBus:
    def __init__(self):
        self.subscribers: list[asyncio.Queue] = []

    async def publish(self, message: dict):
        for queue in self.subscribers:
            await queue.put(message)

    def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        if queue in self.subscribers:
            self.subscribers.remove(queue)


event_bus = EventBus()
