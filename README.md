# 🎓 Face Recognition Attendance System

A modern, AI-powered attendance management system that uses **real-time face recognition** to automate student attendance tracking. Built with Flask, OpenCV, and the `face_recognition` library (powered by dlib), it provides a complete web-based solution for educational institutions.

---

## ✨ Features

### 🔐 Authentication & Security
- Secure admin login with password hashing (Werkzeug)
- Mandatory password change on first login
- Session protection with `HttpOnly` and `SameSite` cookies
- Auto-generated secure secret keys with environment variable support

### 📸 Face Recognition
- Real-time face detection and recognition via webcam
- Multi-face identification in a single frame
- Configurable match tolerance for accuracy tuning
- In-memory encoding cache with thread-safe operations
- Lazy camera initialization for faster startup

### 📝 Student Registration
- Register students with face encoding captured via webcam
- Store student details: ID, name, father's name, department, year, semester, mobile number
- Automatic face encoding extraction and secure storage (numpy binary format)

### 📊 Attendance Management
- One-click automated attendance via face recognition
- Duplicate attendance prevention (per student per day)
- Holiday-aware system — skips attendance on holidays
- Date-change auto-reset with DB-synced cache

### 📈 Dashboard & Analytics
- Real-time attendance statistics and visualizations
- Branch-wise and semester-wise attendance breakdown
- Overall institutional attendance summary
- Interactive charts and graphs

### 📋 Reports
- Detailed attendance reports with filtering options
- Export and download capabilities
- Student-wise and date-wise report generation

### 🤖 Smart Chatbot Assistant
- Built-in attendance chatbot for quick queries
- Natural language commands:
  - `attendance 21001` — Check attendance percentage
  - `history 21001` — View recent attendance records
  - `shortage list` — Students below 75% attendance
  - `today` — Today's attendance summary
  - `department stats` — Department-wise breakdown
  - `total students` — Registered student count

### 🎓 Alumni Management
- Graduate/promote students to alumni records
- Maintain historical alumni data with passing year tracking
- Promotion logging with audit trail

### ⚙️ Settings & Configuration
- Holiday management (add holidays in advance)
- System configuration from the web interface
- Admin account management

---

## 🏗️ Architecture

```
Face-Recognition-Attendance-System/
│
├── app.py                    # Application factory & entry point
├── config.py                 # Centralized configuration
├── wsgi.py                   # WSGI entry point (production deployment)
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
│
├── database/                 # Database layer
│   ├── connection.py         # SQLite connection manager
│   ├── schema.py             # Table creation & migrations
│   └── queries.py            # All SQL query functions
│
├── modules/                  # Core AI/CV modules
│   ├── camera.py             # Webcam capture (cross-platform)
│   ├── face_encoder.py       # Face encoding extraction
│   ├── recognizer.py         # Face recognition engine (cached)
│   └── attendance_marker.py  # Smart attendance marking logic
│
├── routes/                   # Flask Blueprints (API routes)
│   ├── auth_routes.py        # Login / logout
│   ├── dashboard_routes.py   # Dashboard & analytics
│   ├── registration_routes.py# Student registration
│   ├── attendance_routes.py  # Attendance operations
│   ├── students_routes.py    # Student management
│   ├── reports_routes.py     # Report generation
│   ├── settings_routes.py    # System settings
│   ├── chatbot_routes.py     # Chatbot API
│   └── alumni_routes.py      # Alumni management
│
├── templates/                # Jinja2 HTML templates
│   ├── base.html             # Base layout template
│   ├── login.html            # Login page
│   ├── dashboard.html        # Main dashboard
│   ├── registration.html     # Student registration form
│   ├── attendance.html       # Attendance capture page
│   ├── students.html         # Student list & management
│   ├── reports.html          # Reports page
│   ├── settings.html         # Settings panel
│   └── alumni.html           # Alumni records
│
├── static/                   # Static assets
│   ├── css/
│   │   └── style.css         # Application stylesheet
│   ├── js/
│   │   ├── auth.js           # Login logic
│   │   ├── dashboard.js      # Dashboard interactions
│   │   ├── registration.js   # Registration form handling
│   │   ├── attendance.js     # Attendance capture logic
│   │   ├── students.js       # Student management UI
│   │   ├── reports.js        # Report filters & export
│   │   └── settings.js       # Settings panel logic
│   └── assets/               # Images & media
│
├── utils/                    # Utility modules
│   ├── chatbot.py            # Attendance chatbot engine
│   ├── decorators.py         # Auth decorators
│   ├── helpers.py            # Helper functions
│   └── logger.py             # Logging configuration
│
├── instance/                 # SQLite database (auto-created)
├── dataset/                  # Face encoding dataset
├── logs/                     # Application logs
└── debug/                    # Debug images
```

---

## 🛠️ Tech Stack

| Layer          | Technology                                    |
|----------------|-----------------------------------------------|
| **Backend**    | Python 3.8+, Flask 3.0                        |
| **Database**   | SQLite (via `sqlite3`)                        |
| **Face AI**    | `face_recognition`, `dlib`, OpenCV            |
| **Frontend**   | HTML5, CSS3, JavaScript (Jinja2 templates)    |
| **Data**       | NumPy, Pandas                                 |
| **Security**   | Werkzeug (password hashing), dotenv           |
| **Deployment** | WSGI-compatible (Gunicorn, Waitress, etc.)    |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **CMake** (required for building `dlib`)
- **Visual Studio Build Tools** (Windows only — for `dlib` compilation)
- A **webcam** connected to your system

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/face-recognition-attendance-system.git
cd face-recognition-attendance-system
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> **⚠️ Note (Windows):** Installing `dlib` may require CMake and Visual Studio Build Tools. If you encounter build errors:
> ```bash
> pip install cmake
> pip install dlib
> ```

### 4. Configure Environment Variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
SECRET_KEY=your-long-random-secret-key-here
ADMIN_INITIAL_PASSWORD=your-strong-admin-password
```

| Variable                  | Description                                            | Required |
|---------------------------|--------------------------------------------------------|----------|
| `SECRET_KEY`              | Flask secret key for session encryption                | Yes      |
| `ADMIN_INITIAL_PASSWORD`  | Initial admin password (must change on first login)    | Yes      |
| `FACE_TOLERANCE`          | Face match tolerance (default: `0.45`, lower = stricter) | No     |
| `CAMERA_ID`               | Webcam device ID (default: `0`)                        | No       |

> If `SECRET_KEY` is not set, the app generates a random one (sessions reset on restart).
> If `ADMIN_INITIAL_PASSWORD` is not set, a one-time bootstrap password is generated and logged.

### 5. Run the Application

```bash
python app.py
```

The server starts at **http://localhost:5000**

### 6. First Login

1. Navigate to `http://localhost:5000`
2. Login with:
   - **Username:** `admin`
   - **Password:** *(the password you set in `.env`, or check the console log for the auto-generated one)*
3. You will be prompted to change your password on first login

---

## 📖 Usage Guide

### Register a Student
1. Go to **Registration** from the sidebar
2. Fill in student details (ID, name, department, semester, etc.)
3. Capture the student's face via webcam
4. Submit — the face encoding is saved automatically

### Take Attendance
1. Go to **Attendance** from the sidebar
2. The webcam activates and scans faces in real-time
3. Recognized students are automatically marked present
4. Duplicate entries for the same day are prevented

### View Reports
1. Go to **Reports** to filter attendance by date, department, or student
2. Export data as needed

### Use the Chatbot
1. Click the chatbot icon on any page
2. Type natural language queries like:
   - `attendance 21001`
   - `shortage list`
   - `today`

---

## 🗄️ Database Schema

| Table            | Purpose                                      |
|------------------|----------------------------------------------|
| `students`       | Student profiles with face encodings         |
| `attendance`     | Daily attendance records (unique per student per day) |
| `admin`          | Admin credentials and settings               |
| `holidays`       | Holiday calendar (prevents attendance marking)|
| `alumni`         | Graduated student records                    |
| `promotion_log`  | Audit trail for promotions/graduations       |

---

## 🔧 Configuration

Key settings in `config.py`:

| Setting                    | Default    | Description                        |
|----------------------------|------------|------------------------------------|
| `FACE_MATCH_TOLERANCE`     | `0.45`     | Lower = stricter matching          |
| `CAMERA_ID`                | `0`        | Webcam device index                |
| `MAX_CONTENT_LENGTH`       | `16 MB`    | Max upload file size               |
| `SESSION_COOKIE_HTTPONLY`   | `True`     | XSS protection                     |
| `SESSION_COOKIE_SAMESITE`  | `Lax`      | CSRF protection                    |

---

## 🚢 Production Deployment

For production, use a WSGI server instead of the built-in Flask dev server:

### Using Waitress (Windows)

```bash
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
```

### Using Gunicorn (Linux / macOS)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

> **Important:** Always set `SECRET_KEY` and `ADMIN_INITIAL_PASSWORD` via environment variables in production.

---

## 🔒 Security Features

- ✅ Passwords hashed with Werkzeug's `generate_password_hash`
- ✅ Mandatory password change on first admin login
- ✅ Session cookies marked `HttpOnly` and `SameSite=Lax`
- ✅ Face encodings stored as numpy binary (no pickle deserialization)
- ✅ Input validation on all routes
- ✅ Auto-generated fallback secret key (non-predictable)
- ✅ Upload size limits enforced (16 MB max)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).

---

## 👤 Author

**Rajneesh Singh**

---

> Built with ❤️ using Flask, OpenCV & Face Recognition
