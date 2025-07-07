# chat/views.py
from rest_framework import views
from rest_framework import generics
from .serializers import ChatRoomSerializer, ChatRoomCreateSerializer
from .models import ChatRoom
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


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
