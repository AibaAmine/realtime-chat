# Realtime Chat Backend

A Django-based realtime chat backend with WebSocket support.

## Features

- JWT Authentication
- Realtime messaging using WebSockets
- Message read status tracking
- Room-based chat system

## API Endpoints

### Authentication
- `POST /api/token/` - Get JWT token
- `POST /api/token/refresh/` - Refresh JWT token

## WebSocket Endpoints

### Chat WebSocket
- URL: `ws://your-domain/ws/chat/{room_name}/`

#### Message Types

1. Send Message:
```json
{
    "message": "Hello world!"
}
```

2. Mark Message as Read:
```json
{
    "type": "read_status",
    "message_id": "message-uuid-here"
}
```

#### Message Responses

1. Chat Message:
```json
{
    "message": "Hello world!",
    "username": "user123",
    "message_id": "uuid-here",
    "timestamp": "2024-03-14T12:00:00Z"
}
```

2. Read Status:
```json
{
    "type": "read_status",
    "message_id": "uuid-here",
    "username": "user123",
    "timestamp": "2024-03-14T12:00:00Z"
}
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
ACCESS_TOKEN_LIFETIME=5
REFRESH_TOKEN_LIFETIME=1
ROTATE_REFRESH_TOKENS=True
BLACKLIST_AFTER_ROTATION=True
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Start the server:
```bash
python manage.py runserver
``` 