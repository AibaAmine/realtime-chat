# chat/consumers.py
import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from datetime import datetime
from .models import ChatMessage, ChatRoom
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if isinstance(self.scope["user"], AnonymousUser):
            await self.close(code=4001)  # 4001 : unauthorized
            return

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        
        #get the room instance or create it if its not founded
        self.room_obj = await self.get_or_create_room(self.room_name)
        
        if not self.room_obj:
            await self.close(code=4000) # could not get /create room
            return

        # Join room group

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        

        await self.accept()
        print(
            f"WebSocket CONNECT /ws/chat/{self.room_name}/ [User: {self.scope['user'].username}]"
        )
        
        #send the message history to the connected room 
        await self.send_message_history()


    async def disconnect(self, close_code):
        # Leave room group
        if not isinstance(self.scope["user"], AnonymousUser):  # if ahthorized
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    # Receive message from WebSocket
    async def receive(self, text_data):
        if isinstance(self.scope["user"], AnonymousUser):
            await self.send(text_data=json.dump({"Unauthorized to send messages. "}))
            await self.close(code=4001)
            return

        try:

            text_data_json = json.loads(text_data)
            message_content = text_data_json.get("message")

            if not message_content:
                await self.send(
                    text_data=json.dumps({"error": "message content is missing "})
                )
                return

            # save msg to db
            await self.save_chat_message(
                room=self.room_obj, sender=self.scope["user"], content=message_content
            )

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.message",
                    "message": message_content,
                    "sender_id": str(self.scope["user"].id),
                    "sender_username": self.scope["user"].username,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        except json.JSONDecodeError:
            print(f"Recieved non Json data or malformed JSON")
            await self.send(
                text_data=json.dump({"Error": "invalid json format reseived"})
            )
        except Exception as e:
            print(f"Error processing message :  {e}")
            await self.send(
                text_data=json.dump({"Error": "Server error processing message:"})
            )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        sender_username = event.get("sender_username", "Unknown")
        sender_id = (
            str(event.get("sender_id", ""))
            if event.get("sender_id") is not None
            else None
        )
        timestamp = event.get("timestamp", "")

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "message": message,
                    "sender_username": sender_username,
                    "sender_id": sender_id,
                    "timestamp": timestamp,
                }
            )
        )
        
    # -- HELPER METHODS FOR DB OPERATIONS --
    
    @database_sync_to_async
    def get_or_create_room(self,room_name):
        try:
            room, created = ChatRoom.objects.get_or_create(
                room_name=room_name,
                defaults={"creator": self.scope["user"]}
            )
            if created:
                print(f"Created new chat room: {room_name} by {self.scope["user"].username}")
            
            return room
        except Exception as e:
            print(f"Error getting /creating chat room {room_name}")
            
    
    @database_sync_to_async
    def save_chat_message(self,room,sender,content):
        try:
            ChatMessage.objects.create(room = room ,sender= sender,content=content)
        except Exception as e:
            print(f"Error saving chat message : {e}")
    
    
    # method to get messages history for a room 
    @database_sync_to_async
    def get_message_history(self,room,limit=50):
        return list(room.messages.order_by('timestamp').values(
            'sender__username',
            'sender__id',
            'content',
            'timestamp'
        ))
        
    
    #method to send messages history to a room
    async def send_message_history(self):
        history = await self.get_message_history(self.room_obj)
        for message_data in history:
            await self.send(text_data=json.dumps({
                "type": "chat_message",
                "message":message_data["content"],
                "sender_username":message_data["sender__username"],
                "sender_id":str(message_data["sender__id"]),
                "timpestamp": message_data["timestamp"].isoformat()
            }))
            
            print(f"send{len(history)} historical messages to  : {self.scope["user"].username } in {self.room_obj.room_name}")
        
    
