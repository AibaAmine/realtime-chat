# chat/views.py
from rest_framework import views
from rest_framework import generics
from .serializers import ChatRoomSerializer, ChatRoomCreateSerializer
from .models import ChatRoom
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import FileResponse
import os
from django.conf import settings


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

# add apis for updating ,deleting rooms


def websocket_docs(request):
    file_path = os.path.join(settings.BASE_DIR, 'WEBSOCKET_API.md')
    return FileResponse(open(file_path, 'rb'), content_type='text/markdown')