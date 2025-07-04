# realtime_chat_backend/auth_middleware.py
import jwt
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_key):
    """
    Attempts to authenticate a user based on a JWT token.
    This function must be async because it interacts with the database.
    """
    try:
        # AccessToken handles expiration and signature validation internally.
        access_token = AccessToken(token_key)
        user_id = access_token["user_id"]  # Get user_id from the token payload
        user = User.objects.get(id=user_id)
        return user
    except (jwt.ExpiredSignatureError, jwt.DecodeError, jwt.InvalidTokenError) as e:
        # Catch specific JWT errors for clearer debugging if needed
        print(f"JWT Token Error: Invalid or Expired Token: {e}")
        return AnonymousUser()
    except User.DoesNotExist:
        print(f"JWT Token Error: User with ID not found for token: {token_key}")
        return AnonymousUser()
    except Exception as e:
        print(f"Unexpected error during JWT authentication: {e}")
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate users using JWT tokens from either
    the Authorization header or a 'token' query parameter (for testing convenience).
    """

    def __init__(self, inner):
        super().__init__(inner)
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Only process WebSocket scopes for this authentication logic
        if scope["type"] == "websocket":
            token_key = None

            # --- 1. Try to get token from Authorization header (Preferred for production) ---
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(
                b"authorization"
            )  # Header names are lowercase and byte strings

            if auth_header:
                try:
                    # auth_header is like b'Bearer eyJhbGciOiJIUzI1Ni...'
                    # Decode to string, then split
                    token_prefix, token_value = auth_header.decode().split(" ", 1)
                    if token_prefix.lower() == "bearer":
                        token_key = token_value
                except ValueError:
                    print("Invalid Authorization header format for WebSocket.")
                    pass  # Malformed header, token_key remains None

            # --- 2. If not found in header, try to get from query parameter
            if not token_key:
                query_string = scope.get("query_string", b"").decode()
                parsed_query = parse_qs(query_string)
                if "token" in parsed_query:
                    # parse_qs returns a list for each parameter, get the first one
                    token_key = parsed_query["token"][0]
                    print("JWT token found in URL query parameter (for testing).")

            if token_key:
                # 3. Authenticate user using the found token
                scope["user"] = await get_user_from_token(token_key)
            else:
                # No valid token provided in header or query param, treat as anonymous
                scope["user"] = AnonymousUser()

        # 4. Continue to the next middleware or consumer
        return await super().__call__(scope, receive, send)


# A helper function to apply the middleware in your asgi.py
def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
