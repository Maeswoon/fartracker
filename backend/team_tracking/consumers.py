import asyncio
from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import JsonWebsocketConsumer
from channels_yroom.conf import get_room_settings
from channels_yroom.consumer import YroomConsumer

class TrajectoryConsumer(JsonWebsocketConsumer):
    def connect(self):
        from .models import Trajectory
        from .serializers import TrajectorySerializer
        async_to_sync(self.channel_layer.group_add)('trajectories', self.channel_name)
        self.accept()
        trajectories = Trajectory.objects.select_related('team').all()
        serializer = TrajectorySerializer(trajectories, many=True)
        self.send_json({'type': 'initial', 'trajectories': serializer.data})

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)('trajectories', self.channel_name)

    def trajectory_update(self, event):
        self.send_json({'type': 'update', 'trajectory': event['data']})

class ScheduleConsumer(YroomConsumer):
    async def forward_payload(self, message):
        """Override to log broadcasts from the yroom worker."""
        await super().forward_payload(message)

    room_name = 'schedule'
    _sync_task: asyncio.Task | None = None

    async def connect(self):
        self.room_name = self.get_room_name()
        self.conn_id = self.get_connection_id()
        self.room_settings = get_room_settings(self.room_name)

        from django.conf import settings
        from rest_framework_simplejwt.tokens import AccessToken

        headers = dict(self.scope.get('headers', []))
        origin = headers.get(b'origin', b'').decode()

        # Reject cross-origin WebSocket connections to prevent CSRF/CSRH.
        # When Origin is absent (native apps, curl, server-side clients)
        # there is no cross-origin risk, so we allow it.
        if origin:
            allowed = {
                'https://tracker.faroutlaunch.org',
                'https://www.tracker.faroutlaunch.org',
            }
            if settings.DEBUG:
                allowed.add('http://localhost:5173')
                allowed.add('http://127.0.0.1:5173')
            if origin not in allowed:
                await self.close(code=4003)
                return

        cookie_header = headers.get(b'cookie', b'').decode()
        cookies = {}
        for item in cookie_header.split('; '):
            if '=' in item:
                key, _, value = item.partition('=')
                cookies[key] = value

        cookie_name = settings.SIMPLE_JWT.get('AUTH_COOKIE', 'access_token')
        raw_token = cookies.get(cookie_name, '')

        is_admin = False
        if raw_token:
            try:
                token = AccessToken(raw_token)
                is_admin = token.get('is_admin', False)
            except Exception as e:
                pass
        if not is_admin:
            await self.close(code=4001)
            return

        await self.join_room()

    async def handle_room_message(self, bytes_data):
        await super().handle_room_message(bytes_data)
        if self._sync_task and not self._sync_task.done():
            self._sync_task.cancel()
        self._sync_task = asyncio.create_task(self._sync_lanes_to_db())

    _pending_lanes: dict | None = None
    _pending_teams: dict | None = None
    _pending_schedule: dict | None = None

    async def _sync_lanes_to_db(self):
        await asyncio.sleep(2)
        room_settings = get_room_settings(self.room_name)
        self._pending_lanes = None
        self._pending_teams = None
        self._pending_schedule = None
        for map_name in ('lanes', 'teams', 'schedule'):
            await self.channel_layer.send(
                room_settings['CHANNEL_NAME'],
                {
                    'type': 'rpc',
                    'room': self.room_name,
                    'channel_name': self.channel_name,
                    'method': 'export_map',
                    'params': [map_name],
                },
            )

    async def rpc_response(self, event):
        import json
        data = event.get('result')
        if not data:
            return
        # The yroom RPC result may come back as a JSON string
        if isinstance(data, str):
            data = json.loads(data)
        # Determine which map this response is for by checking keys
        # lanes map has lane_id -> [team_ids], teams map has team_id -> {fields},
        # schedule map has string keys -> string values
        if any(isinstance(v, list) for v in data.values()):
            self._pending_lanes = data
        elif any(isinstance(v, dict) for v in data.values()):
            self._pending_teams = data
        else:
            self._pending_schedule = data
        # Save when all are available
        if self._pending_lanes is not None and self._pending_teams is not None and self._pending_schedule is not None:
            await sync_to_async(_save_lanes)(self._pending_lanes, self._pending_teams, self._pending_schedule)

def _save_lanes(lanes_data, team_data=None, schedule_data=None):
    import json

    from .models import SalvoSchedule
    from .views import DEFAULT_LANE_DEFINITIONS
    from django.utils import dateparse

    if isinstance(lanes_data, str):
        lanes_data = json.loads(lanes_data)
    if isinstance(team_data, str):
        team_data = json.loads(team_data)
    if isinstance(schedule_data, str):
        schedule_data = json.loads(schedule_data)

    schedule, _ = SalvoSchedule.objects.get_or_create(pk=1)

    # Only keep lane keys that match a known lane definition so that
    # internal Yjs sub-document keys (e.g. "salvo-1-12") don't leak
    # into the persisted data and hide teams from the UI.
    if isinstance(lanes_data, dict):
        known_ids = {ld['id'] for ld in (schedule.lane_definitions or DEFAULT_LANE_DEFINITIONS)}
        lanes_data = {k: v for k, v in lanes_data.items() if k in known_ids}

    schedule.lane_teams = lanes_data
    if team_data is not None:
        schedule.team_data = team_data
    if isinstance(schedule_data, dict):
        timer_val = schedule_data.get('salvo_timer_started')
        if timer_val and isinstance(timer_val, str):
            schedule.salvo_timer_started = dateparse.parse_datetime(timer_val)
        else:
            # empty string or missing means cleared
            schedule.salvo_timer_started = None
    schedule.save()
