from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer


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
