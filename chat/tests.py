import json
from channels.testing import WebsocketCommunicator
from django.test import TestCase
from chat.consumers import ChatConsumer
from channels.routing import URLRouter
from django.urls import re_path

test_websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>\w+)/$", ChatConsumer.as_asgi()),
]


class ChatConsumerTest(TestCase):
    async def test_chat_message_flow(self):
        communicator = WebsocketCommunicator(
            URLRouter(test_websocket_urlpatterns), "/ws/chat/test_room/"
        )

        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)

        test_message_content = "Hello from automated test!"
        await communicator.send_json_to({"message": test_message_content})

        received_message = await communicator.receive_json_from()

        self.assertEqual(received_message, {"message": test_message_content})

        await communicator.disconnect()
