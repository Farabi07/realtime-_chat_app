import json
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from jwt import decode as jwt_decode
from django.conf import settings
from .models import Message

# User = get_user_model()

# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.room_name = self.scope['url_route']['kwargs']['room_name']
#         self.room_group_name = f'chat_{self.room_name}'

#         # Authenticate user via JWT
#         token = self.scope['query_string'].decode('utf-8').split('=')[1]
#         try:
#             decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
#             self.user = await self.get_user(decoded_data['user_id'])
#         except (InvalidToken, TokenError, KeyError):
#             await self.close()
#             return

#         # Join room group
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )
#         await self.accept()

#     async def disconnect(self, close_code):
#         # Leave room group
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#     async def receive(self, text_data):
#         data = json.loads(text_data)
#         message = data.get('message')
#         timestamp = data.get('timestamp')

#         if not message:
#             # Handle missing message content
#             await self.send(text_data=json.dumps({'error': 'Message content is required.'}))
#             return

#         # Save message to the database
#         await self.save_message(self.user, message, self.room_name)

#         # Broadcast message to room group
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 'type': 'chat_message',
#                 'message': message,
#                 'username': self.user.username,
#                 'timestamp': timestamp,
#             }
#         )

#     async def chat_message(self, event):
#         # Send message to WebSocket
#         await self.send(text_data=json.dumps({
#             'message': event['message'],
#             'username': event['username'],
#             'timestamp': event['timestamp'],
#         }))

#     @database_sync_to_async
#     def get_user(self, user_id):
#         try:
#             return User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return AnonymousUser()

#     @database_sync_to_async
#     def save_message(self, user, content, room_name):
#         """Save the message to the database."""
#         Message.objects.create(sender=user, content=content, room_name=room_name)

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message
from datetime import datetime

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        if not self.scope.get("user") or not self.scope["user"].is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = self.scope["user"].username

        msg = await self.save_message(username, self.room_name, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': msg['message'],
                'username': msg['username'],
                'timestamp': msg['timestamp']
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @staticmethod
    # Save message
    @database_sync_to_async
    def save_message(user, room, content):
        message = Message.objects.create(
            sender=user,
            room=room,
            content=content
        )
        return {
            "username": message.sender.username,
            "message": message.content,
            "timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
