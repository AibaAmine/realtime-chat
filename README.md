# Realtime Chat Backend

A Django-based realtime chat backend with WebSocket support.

## Features

- JWT Authentication
- Realtime messaging using WebSockets
- Message read status tracking
- Room-based chat system (public, private, and direct messages)
- User registration, login, and profile management
- Swagger UI for API exploration

## REST API Endpoints

### Authentication
- `POST /users/auth/register/` — Register a new user
- `POST /users/auth/login/` — Obtain JWT access and refresh tokens
- `POST /users/token/refresh/` — Refresh JWT token

### User
- `GET /users/auth/profile/` — Get current user's profile (JWT required)
- `PUT /users/auth/profile/` — Update current user's profile (JWT required)

### Chat Rooms
- `GET /chat/rooms/` — List all chat rooms
- `POST /chat/rooms/create/` — Create a new chat room (JWT required)
- `GET /chat/rooms/<pk>/` — Retrieve a chat room by ID (JWT required)
- `PUT /chat/rooms/<pk>/` — Update a chat room (JWT required, must be creator)
- `DELETE /chat/rooms/<pk>/` — Delete a chat room (JWT required, must be creator)
- `GET /chat/dm/<target_user_id>` — Get or create a direct message room with another user (JWT required)

### API Documentation
- `GET /swagger/` — Swagger UI for exploring and testing the API

## WebSocket API

See the full documentation in [`static/WEBSOCKET_API.md`](static/WEBSOCKET_API.md) or via [WebSocket API Documentation](https://github.com/AibaAmine/realtime-chat/blob/main/static/WEBSOCKET_API.md).

**Summary:**
- **Endpoint:** `ws://<your-domain>/ws/chat/{room_name}/`
- **Authentication:** JWT (via header or query param)
- **Room-based:** Each connection is scoped to a chat room by `room_name`.
- **Events:**
  - Send/receive chat messages
  - User join/leave notifications
  - Room user list on connect
  - Historical messages on connect
  - Error messages and codes (e.g., 4001 for unauthorized)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (example for PostgreSQL):
```
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
ACCESS_TOKEN_LIFETIME_MINUTES=5
REFRESH_TOKEN_LIFETIME_DAYS=1
ROTATE_REFRESH_TOKENS=True
BLACKLIST_AFTER_ROTATION=True
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
REDIS_URL=redis://127.0.0.1:6379/1
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Start the server:
```bash
python manage.py runserver
```

## Dependencies

Main dependencies (see `requirements.txt` for full list):
- Django
- djangorestframework
- channels
- channels-redis
- djangorestframework-simplejwt
- drf-yasg (Swagger UI)
- django-filter
- daphne
- gunicorn
- whitenoise
- dj-database-url
- django-cors-headers
- python-dotenv
- pillow

## Notes
- For production, configure environment variables securely and use a production-ready database and Redis instance.
- The default user model is extended (`CustomUser`) to support profile pictures.
- See Swagger UI (`/swagger/`) for detailed API schema and try out endpoints interactively.
- For WebSocket message formats and flows, see [`static/WEBSOCKET_API.md`](static/WEBSOCKET_API.md). 