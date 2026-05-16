# WebSocket Real-Time Face Scan — Design Spec

**Date:** 2026-05-16
**Status:** Approved

## Overview

Add a WebSocket endpoint `/api/v1/ws/scan` to the existing Face Recognition API.
Browser clients stream JPEG frames continuously; the server runs InsightFace recognition on
the latest frame and returns JSON results in real-time. Only the scan feature uses WebSocket —
the `/register` endpoint stays as HTTP POST.

## Requirements

- Browser sends raw JPEG bytes over WebSocket at ~100ms intervals
- Server always processes the **latest** frame, not a queue of old frames
- Server returns `ScanResponse` JSON per recognition cycle
- DB session lives for the lifetime of the connection (not per-frame)
- Face recognition runs in a thread pool to avoid blocking the asyncio event loop

## Architecture

Two coroutines run concurrently via `asyncio.gather` for each connection:

```
Browser (getUserMedia)
    │  JPEG bytes ~100ms
    ▼
WebSocket /api/v1/ws/scan
    │
    ├─ _receive_loop  ──►  latest_frame (bytes | None)  +  asyncio.Event
    │                      (new frame overwrites unprocessed old frame)
    │
    └─ _process_loop  ──►  waits on Event
                           │
                           ├─ grab latest_frame, clear slot
                           ├─ run_in_executor → extract_best_embedding (CPU-bound)
                           ├─ AsyncSession DB query → find_best_match
                           └─ websocket.send_json(ScanResponse)
```

## Components

### New file: `app/api/v1/routes/ws_scan.py`
- `ws_scan(websocket, db)` — WebSocket handler
- `_receive_loop()` — inner coroutine, receives frames, writes to shared slot
- `_process_loop()` — inner coroutine, processes latest frame, sends result

### Modified file: `app/api/v1/router.py`
- Include `ws_scan` router

### Unchanged
- `face_service.py` — `extract_best_embedding`, `find_best_match` reused as-is
- `user_service.py` — not used by WS handler (WS calls face_service + repository directly)
- `repositories/` — `get_all_encodings`, `get_user_by_id` reused as-is
- `schemas/recognition.py` — `ScanResponse` reused as-is
- `main.py` — no changes

## WebSocket Endpoint Contract

**URL:** `ws://host/api/v1/ws/scan`

**Client → Server:** Binary frames (JPEG bytes), no framing protocol needed.

**Server → Client (per cycle):** JSON

```json
// Face recognized
{
  "recognized": true,
  "user_id": 1,
  "name": "Arya",
  "employee_id": "EMP001",
  "confidence": 0.87,
  "scanned_at": "2026-05-16T10:00:00"
}

// No face / no match
{
  "recognized": false,
  "scanned_at": "2026-05-16T10:00:00"
}

// Error (connection stays open)
{
  "error": "Invalid image data"
}
```

## Error Handling

| Scenario | Behavior |
|---|---|
| Browser disconnects | `WebSocketDisconnect` caught in `_receive_loop`, sets `disconnected` flag, `_process_loop` exits cleanly |
| Corrupt/invalid frame bytes | `ValueError` from `decode_image_rgb` → send `{"error": "..."}` → continue |
| No face detected | Send `{"recognized": false, ...}` → continue |
| Recognition slower than frame rate | Frame slot overwritten with latest — old frame silently dropped (by design) |
| Multiple concurrent clients | Each connection has isolated state — no shared mutable state |

## Concurrency Notes

- `extract_best_embedding` is CPU-bound (calls `face_recognition` C extension)
- Must be wrapped with `asyncio.get_event_loop().run_in_executor(None, ...)` to avoid blocking the event loop
- Default `ThreadPoolExecutor` is sufficient — one thread per active recognition
- `AsyncSession` per connection (not per frame) — safe because `_process_loop` is sequential within a connection

## Out of Scope

- Annotated frames with bounding box overlay
- Motion detection / frame diff throttling
- Authentication / token validation on WS handshake
- Re-connection handling on the client side
