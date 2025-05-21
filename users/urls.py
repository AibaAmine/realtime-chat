from django.urls import path
from .views import UserRegisterAPiView, UserLoginAPiView, UserProfileAPiView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("auth/register/", UserRegisterAPiView.as_view(), name="register"),
    path("auth/login/", UserLoginAPiView.as_view(), name="login"),
    path("auth/profile/", UserProfileAPiView.as_view(), name="profile"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
