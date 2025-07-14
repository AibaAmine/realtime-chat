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
