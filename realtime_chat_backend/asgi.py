# realtime_chat_backend/asgi.py
import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

# Ensure this import path is correct based on your project structure
# It should point to the file containing your custom JWTAuthMiddlewareStack
from realtime_chat_backend.auth_middleware import JWTAuthMiddlewareStack

# Set the Django settings module environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realtime_chat_backend.settings')

django_asgi_app = get_asgi_application()

# Import your app's WebSocket routes AFTER django_asgi_app is initialized
# This prevents potential circular import issues if chat.routing imports Django models.
import chat.routing

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app, 
        "websocket":
            JWTAuthMiddlewareStack( 
                AuthMiddlewareStack( 
                    URLRouter(
                        chat.routing.websocket_urlpatterns 
                    )
                )
            )
        
    }
)
