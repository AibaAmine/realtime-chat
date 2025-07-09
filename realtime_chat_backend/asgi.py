import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realtime_chat_backend.settings')
django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

from realtime_chat_backend.auth_middleware import JWTAuthMiddlewareStack
import chat.routing

django_asgi_app = get_asgi_application()

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
