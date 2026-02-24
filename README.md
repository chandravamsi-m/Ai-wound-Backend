# AI-Based Wound Analysis Tool - Backend

Django REST Framework backend for the AI-Based Wound Analysis Tool.

## Tech Stack

- **Framework**: Django 5.2.9
- **API**: Django REST Framework
- **Database**: PostgreSQL
- **CORS**: django-cors-headers

## Setup Instructions

### Prerequisites
- Python 3.10+
- PostgreSQL installed and running

### Installation

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Create a `.env` file in the Backend directory:
   ```
   DB_NAME=wound_analysis_db
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   SECRET_KEY=your-secret-key
   DEBUG=True
   ```

4. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Seed initial data** (optional):
   ```bash
   python scripts/seed_users.py
   ```

6. **Start development server**:
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://127.0.0.1:8000/api/`

## API Endpoints

### Authentication
- `POST /api/login/` - Validate credentials and return user role/session data. Includes password hashing verification.

### Users (Staff Management)
- `GET /api/users/` - List all staff members with dynamic initial calculation.
- `POST /api/users/` - Create a new staff member (Admin only).
- `GET /api/users/<id>/` - Retrieve detailed information for a specific staff member.
- `PATCH /api/users/<id>/` - Partially update staff information (e.g., status, role).
- `DELETE /api/users/<id>/` - Permanently remove a staff member from the system.

## Data Seeding & Maintenance

The backend includes utility scripts for environment management:

1. **Initial Seed**: Populate the database with default admin and staff accounts.
   ```bash
   python scripts/seed_users.py
   ```

2. **Database Cleanup**: Wipe all user records to reset the environment.
   ```bash
   python scripts/clean_db.py
   ```

3. **ID Reset**: Re-sequence user IDs for a clean database state.
   ```bash
   python scripts/reset_user_ids.py
   ```

## Project Structure

```
Backend/
├── users/              # User management app
├── wound_analysis_backend/  # Project settings
├── scripts/            # Utility scripts
├── manage.py           # Django management script
├── requirements.txt    # Python dependencies
└── .env               # Environment variables (not in git)
```
