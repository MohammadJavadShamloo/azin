# routing.py

from django.urls import path
from storage.consumers import ChatConsumer

websocket_urlpatterns = [
    path('ws/messages/<str:room_name>/', ChatConsumer.as_asgi()),
]
