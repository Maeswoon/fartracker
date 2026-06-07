import asyncio
import os

from channels.layers import get_channel_layer
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from team_tracking.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fartracker_backend.settings')

django_asgi_app = get_asgi_application()

_worker_started = False


async def _start_worker():
    """Launch yroom worker on the ASGI event loop so it shares the
    same InMemoryChannelLayer as the consumers."""
    global _worker_started
    if _worker_started:
        return
    _worker_started = True

    # Lazy imports — Django must be set up first
    from channels_yroom.conf import get_default_room_settings
    from channels_yroom.worker import YroomWorker

    channel_layer = get_channel_layer()
    channel = get_default_room_settings()['CHANNEL_NAME']

    worker = YroomWorker(channel=channel, channel_layer=channel_layer)
    worker.input_queue = asyncio.Queue()

    async def receive_loop():
        while True:
            message = await channel_layer.receive(channel)
            if not message.get('type'):
                continue
            await worker.input_queue.put(message)

    asyncio.create_task(receive_loop())
    asyncio.create_task(worker.run_consumer())


class YroomASGIWrapper:
    """Starts the yroom worker on the first ASGI request."""

    def __init__(self, app):
        self.app = app
        self._started = False

    async def __call__(self, scope, receive, send):
        if not self._started:
            self._started = True
            await _start_worker()
        return await self.app(scope, receive, send)


application = YroomASGIWrapper(
    ProtocolTypeRouter({
        'http': django_asgi_app,
        'websocket': URLRouter(websocket_urlpatterns),
    })
)
