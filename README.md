# Face Recognition System

A realtime face recognition system with a REST API built using **FastAPI** and **MariaDB**. Detects and identifies registered faces from image input, and exposes the results for consumption by external monitoring applications.

Includes a standalone webcam demo for local model testing — independent from the API.

---

## Features

- **REST API** — two endpoints: register a user and scan a face in realtime
- **MariaDB storage** — face embeddings stored as binary data; raw images never saved
- **Layered Architecture** — clean separation between API, service, repository, and model layers
- **Standalone demo** — webcam-based face register and scan for local testing without a database
- **Async** — fully async FastAPI + SQLAlchemy for non-blocking I/O

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.14 |
| API Framework | FastAPI |
| Database | MariaDB (async via `aiomysql` + SQLAlchemy 2.x) |
| Face Recognition | `face-recognition` + `dlib` |
| Image Processing | OpenCV, Pillow |

---

## Project Structure

```
face_recognition/
├── app/                        # REST API (Layered Architecture)
│   ├── main.py                 # FastAPI app factory & lifespan
│   ├── api/v1/routes/
│   │   ├── register.py         # POST /api/v1/register
│   │   └── scan.py             # POST /api/v1/scan
│   ├── services/               # Business logic
│   ├── repositories/           # Database queries
│   ├── models/                 # SQLAlchemy ORM
│   ├── schemas/                # Pydantic request/response models
│   ├── core/                   # Config & database engine
│   └── utils/                  # Image decoding helpers
│
├── demo/                       # Standalone webcam demo (no API/DB required)
│   ├── main.py                 # CLI menu
│   ├── register.py             # Register face via webcam → face_dataset.dat
│   └── scan.py                 # Scan & recognize via webcam
│
├── tests/                      # Service-layer tests (no HTTP server needed)
│   ├── test_register.py
│   ├── test_scan.py
│   └── assets/                 # Place face1.jpg and face2.jpg here
│
├── index.py                    # Uvicorn entry point
├── requirements.txt
├── .env.example
└── pytest.ini
```

---

## Getting Started

### 1. Clone & install dependencies

```bash
git clone https://github.com/your-username/face-recognition.git
cd face-recognition

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your database credentials:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=face_recognition
RECOGNITION_TOLERANCE=0.6
```

### 3. Create the database

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS face_recognition CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

Tables are created automatically on first API startup.

### 4. Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Endpoints

### `POST /api/v1/register`

Register a new user with their face image.

**Request** — `multipart/form-data`:

| Field | Type | Description |
|---|---|---|
| `name` | string | Full name |
| `employee_id` | string | Unique identifier |
| `image` | file | JPEG/PNG with exactly one face |

**Response `201`**:
```json
{
  "success": true,
  "message": "User registered successfully",
  "user_id": 1,
  "name": "Arya Putra",
  "employee_id": "EMP001"
}
```

---

### `POST /api/v1/scan`

Scan a face image and return the matching registered user (if any).

**Request** — `multipart/form-data`:

| Field | Type | Description |
|---|---|---|
| `image` | file | JPEG/PNG from camera or scanner |

**Response `200` — recognized**:
```json
{
  "recognized": true,
  "user_id": 1,
  "name": "Arya Putra",
  "employee_id": "EMP001",
  "confidence": 0.8721,
  "scanned_at": "2026-05-15T10:30:00"
}
```

**Response `200` — not recognized**:
```json
{
  "recognized": false,
  "user_id": null,
  "name": null,
  "employee_id": null,
  "confidence": null,
  "scanned_at": "2026-05-15T10:30:00"
}
```

---

## Standalone Demo (Webcam)

Test the face recognition model locally using your webcam — no API or database needed.

```bash
python demo/main.py
```

Menu options:
1. **Register Face** — captures your face via webcam and saves it to `demo/face_dataset.dat`
2. **Scan Face** — runs the live scanner and labels recognized faces in realtime
3. **Exit**

> Dataset file is stored locally in `demo/face_dataset.dat` and is excluded from version control.

---

## Running Tests

Tests run directly against the service layer without starting an HTTP server.

**Setup:** place JPEG face images in `tests/assets/`:
- `face1.jpg` — required for all tests
- `face2.jpg` — optional, for negative recognition test

```bash
# All tests
pytest tests/ -v

# Register tests only
pytest tests/test_register.py -v

# Scan tests only
pytest tests/test_scan.py -v
```

Tests that require face images are automatically skipped if files are not present.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DB_HOST` | `localhost` | MariaDB host |
| `DB_PORT` | `3306` | MariaDB port |
| `DB_USER` | `root` | Database user |
| `DB_PASSWORD` | — | Database password |
| `DB_NAME` | `face_recognition` | Database name |
| `RECOGNITION_TOLERANCE` | `0.6` | Face distance threshold (lower = stricter, range 0.0–1.0) |

---

## Contributing

Contributions are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push to the branch: `git push origin feat/your-feature`
5. Open a Pull Request

Please keep pull requests focused on a single concern and include a clear description.

---

## License

This project is licensed under the [MIT License](LICENSE).
