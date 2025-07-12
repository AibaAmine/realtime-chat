# WebSocket API Documentation

This document describes the WebSocket API for the Realtime Chat backend.

---

## Overview
- **Endpoint:** `ws://<your-domain>/ws/chat/{room_name}/`
- **Protocol:** WebSocket
- **Authentication:** JWT (see below)
- **Room-based:** Each connection is scoped to a chat room by `room_name`.

---

## Authentication

A valid JWT access token is required to connect. You can provide the token in one of two ways:

1. **Authorization Header (Recommended):**
   - Header: `Authorization: Bearer <your-jwt-token>`
2. **Query Parameter (For Testing):**
   - URL: `ws://<your-domain>/ws/chat/{room_name}/?token=<your-jwt-token>`

If authentication fails, the server will close the connection with code `4001`.

---

## Connection Example

```
GET ws://your-domain/ws/chat/general/
Authorization: Bearer <your-jwt-token>
```

---

## Message Types

### Client → Server

#### 1. Send Chat Message
```
{
  "message": "Hello world!"
}
```

---

### Server → Client

#### 1. New Chat Message
```
{
  "type": "chat_message",
  "message": "Hello world!",
  "sender_username": "user123",
  "sender_id": "user-id",
  "timestamp": "2024-03-14T12:00:00Z"
}
```

#### 2. User Joined
```
{
  "type": "user_join",
  "user_id": "user-id",
  "username": "user123"
}
```

#### 3. User Left
```
{
  "type": "user_leave",
  "user_id": "user-id",
  "username": "user123"
}
```

#### 4. Room Users List (sent on connect)
```
{
  "type": "room_users_list",
  "users": [
    { "id": "user-id", "username": "user123" },
    { "id": "user-id2", "username": "user456" }
  ]
}
```

#### 5. Historical Messages (sent on connect)
- Each message is sent as a `chat_message` type (see above).

#### 6. Error Message
```
{
  "error": "Error description here."
}
```

---

## Error Codes
- **4001:** Unauthorized (invalid or missing token)
- **4000:** Room not found or could not be created

---

## Example Flow

1. **Connect** to `ws://your-domain/ws/chat/general/` with a valid JWT.
2. **On connect:**
   - Receive a list of current users (`room_users_list`).
   - Receive historical messages (`chat_message` for each).
3. **Send a message:**
   - Send `{ "message": "Hi!" }`.
   - All users in the room receive a `chat_message` event.
4. **User joins/leaves:**
   - All users receive `user_join` or `user_leave` events.

---

## Notes
- All messages are JSON-encoded.
- The server may send error messages or close the connection if protocol is violated.
- Room names must be unique and are used as the identifier in the URL.

---

## See Also
- [HTTP API Documentation (Swagger)](/swagger/)
