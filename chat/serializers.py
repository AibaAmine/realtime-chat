from .models import ChatMessage, ChatRoom
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatRoomSerializer(serializers.ModelSerializer):

    creator_username = serializers.ReadOnlyField(source="creator.username")

    # or we can using :
    # creator = serializers.StringRelatedField(read_only = True)  # show user username instead of his id
    
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "room_id",
            "created_at",
            "creator_username",
            "description",
            "is_private",
            "message_count",
        ]
        read_only_fields = [
            "room_id",
            "created_at",
            "creator_username",
            "is_private",
            "message_count",
        ]

    def get_message_count(self, obj):
        return obj.messages.count()


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ["room_name", "description", "is_private"]
        #         # Creator will be set by the view's perform_create method
