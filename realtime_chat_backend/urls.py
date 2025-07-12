# mysite/urls.py
from django.contrib import admin
from django.urls import include, path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="My Chat API",
        default_version="v1",
        description="""
HTTP endpoints for authentication, user data, etc.

**[WebSocket API Documentation](https://github.com/AibaAmine/realtime-chat/blob/main/static/WEBSOCKET_API.md)**
""",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("chat/", include("chat.urls")),
    path("admin/", admin.site.urls),
    path("users/", include("users.urls")),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
]
