from django.urls import path
from .consumers import ScheduleConsumer, TrajectoryConsumer

websocket_urlpatterns = [
    path('ws/trajectories/', TrajectoryConsumer.as_asgi()),
    path('ws/schedule', ScheduleConsumer.as_asgi()),
]
