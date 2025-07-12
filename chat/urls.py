# chat/urls.py
from django.urls import path
from .views import ChatRoomListAPIView, ChatRoomCreateAPIView, websocket_docs
from . import views

urlpatterns = [
    path("rooms/", ChatRoomListAPIView.as_view(), name="room-list"),
    path("rooms/create/", ChatRoomCreateAPIView.as_view(), name="create-room"),
]

urlpatterns += [
    path('websocket-docs/', websocket_docs, name='websocket-docs'),
]
