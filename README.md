# LearnFlow

> Real-time video learning analytics platform

![MVP](https://img.shields.io/badge/status-MVP-brightgreen) ![Django](https://img.shields.io/badge/backend-Django-092E20) ![React](https://img.shields.io/badge/frontend-React-61DAFB) ![PostgreSQL](https://img.shields.io/badge/db-PostgreSQL-336791) ![Cloudinary](https://img.shields.io/badge/storage-Cloudinary-3448C5)

---

## Architecture

```
React → Django REST API → PostgreSQL → Cloudinary

Future:
learning_events → Feature Engineering → DVC → MLflow → Prediction Service
```

---

## Features

| Module | Description |
|---|---|
| **Auth & Roles** | JWT, refresh token, student / instructor / admin |
| **Course management** | CRUD courses, categories, enrollment, progress |
| **Video learning** | Cloudinary upload, chunked, notes, seek, completion tracking |
| **Behavior tracking** | play, pause, seek, skip, rate_change, note events |
| **Dashboards** | Student progress, instructor analytics, admin overview |
| **ML foundation** | Raw `learning_events` table ready for DVC + MLflow pipeline |

---

## Tech Stack

**Backend**
- Python, Django, Django REST Framework, SimpleJWT
- PostgreSQL
- django-cloudinary-storage, Cloudinary (chunked video upload)
- drf-spectacular (OpenAPI/Swagger)

**Frontend**
- React, Vite, React Router, Axios, lucide-react

**Planned ML stack**
- DVC — dataset versioning
- MLflow — experiment tracking & model registry
- Redis Stream / Kafka — realtime event pipeline
- scikit-learn / XGBoost — prediction models

---

## Project Structure

```
.
├── backend/
│   ├── core/        # Settings, root URLs
│   ├── users/       # Auth, JWT, instructor profile
│   ├── courses/     # Categories, courses, enrollment, progress
│   ├── videos/      # Course videos, Cloudinary, notes, progress
│   ├── analytics/   # Learning behavior events & analytics APIs
│   └── api/         # Admin dashboard APIs
└── frontend/
    └── src/
        ├── api/         # Axios client and API modules
        ├── components/  # Shared UI components
        ├── context/     # Auth context
        └── pages/       # auth / public / student / instructor / admin
```

---

## API Reference

### Auth
```
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/logout/
POST /api/auth/refresh/
GET  /api/auth/me/
POST /api/auth/instructor-profile/
```

### Courses
```
GET    /api/courses/
GET    /api/courses/{course_id}/
POST   /api/courses/create/
GET    /api/courses/{course_id}/manage/
PUT    /api/courses/{course_id}/manage/
DELETE /api/courses/{course_id}/manage/
POST   /api/courses/{course_id}/enroll/
GET    /api/courses/my-course/
GET    /api/courses/instructor-course/
```

### Videos
```
GET    /api/videos/courses/{course_id}/
POST   /api/videos/courses/{course_id}/
PUT    /api/videos/{video_id}/
DELETE /api/videos/{video_id}/
GET    /api/videos/{video_id}/stream/
GET    /api/videos/{video_id}/progress/
POST   /api/videos/{video_id}/progress/
GET    /api/videos/{video_id}/notes/
POST   /api/videos/{video_id}/notes/
PUT    /api/videos/notes/{note_id}/
DELETE /api/videos/notes/{note_id}/
```

### Analytics
```
POST /api/analytics/events/
GET  /api/analytics/instructor/behavior/
GET  /api/analytics/courses/{course_id}/behavior/
GET  /api/analytics/admin/behavior/
```

### Admin
```
GET /api/admin/dashboard/
```

---

## Local Setup

### Backend

```bash
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # macOS/Linux

pip install -r requirements.txt
python backend/manage.py migrate
python backend/manage.py runserver
# → http://localhost:8000
# → http://localhost:8000/api/docs/  (Swagger)
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Environment `backend/.env`

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=*

DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

EMAIL_HOST_USER=your_email
EMAIL_HOST_PASSWORD=your_email_app_password

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
CLOUDINARY_VIDEO_CHUNK_SIZE=20000000
```

---

## Behavior Events Tracked

```
play · pause · ended · seek
skip_forward_10 · skip_backward_10
rate_change · note_created · note_updated · note_deleted
progress_sync
```

Each event stores: `student`, `course`, `video`, `event_type`, `position_seconds`, `from_seconds`, `to_seconds`, `playback_rate`, `metadata`, `created_at`

---

## ML Roadmap

| Step | Task | Status |
|---|---|---|
| 1 | Export `learning_events` from PostgreSQL | ✅ Data ready |
| 2 | Build feature tables per student/course/video | 🔲 Planned |
| 3 | Version datasets with DVC | 🔲 Planned |
| 4 | Train baseline models, track with MLflow | 🔲 Planned |
| 5 | Store predictions: engagement score, dropout risk | 🔲 Planned |
| 6 | Surface insights in instructor/admin dashboards | 🔲 Planned |
| 7 | Add Redis Stream/Kafka for realtime events | 🔲 Planned |

---

## Notes

- `.env` and `media/` are git-ignored.
- New videos upload to Cloudinary; old local videos are not auto-migrated.
- Cloudinary free plan has file size limits — compress large videos or upgrade plan for production.
