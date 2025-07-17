from .models import ChatMessage, ChatRoom
from rest_framework import serializers
from django.contrib.auth import get_user_model
from datetime import datetime
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
            "room_name",
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


class ChatMessageSrializer(serializers.ModelSerializer):
    sender_username = serializers.ReadOnlyField(source="sender.username")
    sender_id = serializers.ReadOnlyField(source="sender.id")
    room_id = serializers.ReadOnlyField(source="room.room_id")

    class Meta:
        model = ChatMessage
        fields = [
            "message_id",
            "room_id",
            "sender_id",
            "sender_username",
            "content",
            "timestamp",
            "edited_at",  
            "is_deleted",  
        ]
        read_only_fields = [
            "message_id",
            "room_id",
            "sender_id",
            "sender_username",
            "content",
            "timestamp",
            "edited_at",
            "is_deleted",
        ]


class ChatMessageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["content"]  
        read_only_fields = ["message_id", "room", "sender", "timestamp", "is_deleted"]

    def update(self, instance, validated_data):
        # Update the content
        instance.content = validated_data.get("content", instance.content)
        # Set the edited_at timestamp to now
        instance.edited_at = datetime.now()
        instance.save()
        return instance


class ChatMessageDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = []
   
    def update(self, instance, validated_data):
        # Mark the message as deleted
        instance.content = "This message has been deleted."
        instance.edited_at = datetime.now()
        instance.is_deleted = True
        instance.save()
        return instance