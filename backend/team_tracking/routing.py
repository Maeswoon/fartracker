from django.urls import path
from .consumers import TrajectoryConsumer

websocket_urlpatterns = [
    path('ws/trajectories/', TrajectoryConsumer.as_asgi()),
]
