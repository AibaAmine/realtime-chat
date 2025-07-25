# chat/urls.py
from django.urls import path
from .views import (
    ChatRoomListAPIView,
    ChatRoomCreateAPIView,
    PrivateMessageRoomAPIView,
    ChatRoomRetriveUpdateDeleteAPIView,
    ChatRoomAddMemberAPIView,
    ChatRoomRemoveMemberAPIView,
    ChatMessageDeleteAPIView,
    ChatMessageUpdateAPIView,
    websocket_docs,
)
from . import views

urlpatterns = [
    path("rooms/", ChatRoomListAPIView.as_view(), name="room-list"),
    path("rooms/create/", ChatRoomCreateAPIView.as_view(), name="create-room"),
    path(
        "rooms/<uuid:room_id>/",
        views.ChatRoomRetriveUpdateDeleteAPIView.as_view(),
        name="room-detail",
    ),
    path(
        "dm/<int:target_user_id>",
        PrivateMessageRoomAPIView.as_view(),
        name="chat_dm_room",
    ),
    path(
        "rooms/<uuid:room_id>/members/add/",
        ChatRoomAddMemberAPIView.as_view(),
        name="chat-room-add-member",
    ),
    path(
        "rooms/<uuid:room_id>/members/remove/<uuid:user_id_to_remove>/",
        ChatRoomRemoveMemberAPIView.as_view(),
        name="chat-room-remove-member",
    ),
    path(
        "messages/<uuid:message_id>/edit/",
        ChatMessageUpdateAPIView.as_view(),
        name="chat-message-edit",
    ),
    path(
        "messages/<uuid:message_id>/delete/",
        ChatMessageDeleteAPIView.as_view(),
        name="chat-message-delete",
    ),
]

urlpatterns += [
    path("websocket-docs/", websocket_docs, name="websocket-docs"),
]
