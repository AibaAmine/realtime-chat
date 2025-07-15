# chat/views.py
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework import generics
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .serializers import ChatRoomSerializer, ChatRoomCreateSerializer
from .models import ChatRoom, ChatMessage
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import PermissionDenied
from django.http import FileResponse
import os
from django.conf import settings


User = get_user_model()


class ChatRoomListAPIView(generics.ListAPIView):

    queryset = ChatRoom.objects.all().order_by("room_name")
    serializer_class = ChatRoomSerializer
    permission_classes = [AllowAny]
    authentication_classes = []


class ChatRoomCreateAPIView(generics.CreateAPIView):

    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomCreateSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class ChatRoomRetriveUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def perform_update(self, serializer):
        serializer.save(creator=self.request.user)

    def perform_destroy(self, instance):
        # Ensure the user is the creator before deleting
        if instance.creator == self.request.user:
            instance.delete()
        else:
            raise PermissionError("You do not have permission to delete this room.")


class ChatRoomAddMemberAPIView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, room_id):
        room = get_object_or_404(ChatRoom, room_id=room_id)

        if room.creator != request.user:
            raise PermissionDenied(
                "You do not have permission to add members to this room."
            )

        if not room.is_private:
            return Response(
                {"detail": "Members can only be added to private chat rooms."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_user_id = request.data.get("user_id")
        if not target_user_id:
            return Response(
                {"detail": "User ID to add is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_user = get_object_or_404(User, id=target_user_id)

        if room.members.filter(id=target_user.id).exists():
            return Response(
                {"detail": f"{target_user.username} is already a member of this room."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        room.members.add(target_user)

        serializer = ChatRoomSerializer(room)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChatRoomRemoveMemberAPIView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def delete(self, request, room_id, user_id_to_remove):
        room = get_object_or_404(ChatRoom, room_id=room_id)

        if room.creator != request.user:
            raise PermissionDenied(
                "You do not have permission to remove members from this room."
            )

        if not room.is_private:
            return Response(
                {"detail": "Members can only be removed from private chat rooms."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_user = get_object_or_404(User, id=user_id_to_remove)

        if target_user == request.user:
            return Response(
                {
                    "detail": "You cannot remove yourself from a room you created. Delete the room instead."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not room.members.filter(id=target_user.id).exists():
            return Response(
                {"detail": f"{target_user.username} is not a member of this room."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        room.members.remove(target_user)

        serializer = ChatRoomSerializer(room)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PrivateMessageRoomAPIView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, target_user_id):

        current_user = request.user
        target_user = get_object_or_404(User, id=target_user_id)

        if current_user.id == target_user.id:
            return Response(
                "Cannot create or direct message with yourself.",
                status.HTTP_400_BAD_REQUEST,
            )

        # Generate rooom name for direct messages
        # we use sorted to ensures that the room name is the same
        user_ids = sorted([str(current_user.id), str(target_user.id)])

        dm_room_name = f"dm_{user_ids[0]}_{user_ids[1]}"

        # try to find and existing private room with these two members
        try:
            dm_room = ChatRoom.objects.get(room_name=dm_room_name, is_private=True)

            dm_room.members.set([current_user, target_user])

        except ChatRoom.DoesNotExist:
            dm_room = ChatRoom.objects.create(
                room_name=dm_room_name,
                description=f"Direct message between {current_user.username} and {target_user.username}",
                is_private=True,
                creator=current_user,
            )

            dm_room.members.set([current_user, target_user])
            print(f"Created new DM room :{dm_room_name}")

        serializer = ChatRoomSerializer(dm_room)

        return Response(serializer.data, status=status.HTTP_200_OK)


def websocket_docs(request):
    file_path = os.path.join(settings.BASE_DIR, "WEBSOCKET_API.md")
    return FileResponse(open(file_path, "rb"), content_type="text/markdown")
