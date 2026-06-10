from django.urls import path
from .consumers import ScheduleConsumer, TrajectoryConsumer, VoteConsumer

websocket_urlpatterns = [
    path('ws/trajectories/', TrajectoryConsumer.as_asgi()),
    path('ws/schedule', ScheduleConsumer.as_asgi()),
    path('ws/votes/', VoteConsumer.as_asgi()),
]
