from django.urls import path
from .views import chatbot_response, chat

app_name = 'aichat'

urlpatterns = [
    path('', chat, name='index'),  # Main chat interface
    path('api/chat/', chatbot_response, name='chatbot_response'),  # API endpoint for chat
]
