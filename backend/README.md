# PetCloud Backend Setup

## Project Structure
```
backend/
├── __init__.py          # Package initialization
├── src/
│   ├── __init__.py
│   ├── config/         # Configuration files
│   │   ├── __init__.py
│   │   └── database.py
│   ├── models/         # Database models
│   │   ├── __init__.py
│   │   ├── User.py
│   │   └── Pet.py
│   └── services/       # Business logic
│       ├── __init__.py
│       └── AuthService.py
└── requirements.txt    # Python dependencies
```

## Running the Project

1. First, make sure you're in the project root directory:
   ```bash
   cd PetCloud-project
   ```

2. Add the backend directory to PYTHONPATH:
   ```bash
   # On Windows (PowerShell):
   $env:PYTHONPATH = "$PWD\backend;$env:PYTHONPATH"
   
   # On Linux/Mac:
   export PYTHONPATH="${PWD}/backend:${PYTHONPATH}"
   ```

## Database Setup Instructions

1. Install PostgreSQL on your system if not already installed
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the `src` directory:
   - Copy `.env.example` to `.env`
   - Fill in your PostgreSQL credentials

4. Initialize the database:
   ```bash
   # Initialize Alembic
   alembic init migrations

   # Create initial migration
   alembic revision --autogenerate -m "Initial migration"

   # Run migrations
   alembic upgrade head
   ```

## Environment Variables

Make sure to set these variables in your `.env` file:

```
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=petcloud
```

## Database Schema

The project uses two main tables:

### Users Table
- id (Primary Key)
- name
- email (Unique)
- password (hashed)
- created_at
- updated_at

### Pets Table
- id (Primary Key)
- name
- type
- breed
- birth_date
- owner_id (Foreign Key to Users)
- health_records (JSON)
- feeding_schedule (JSON)
- created_at
- updated_at

## Development Setup

1. Create a new PostgreSQL database:
   ```sql
   CREATE DATABASE petcloud;
   ```

2. Create a user (if needed):
   ```sql
   CREATE USER your_username WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE petcloud TO your_username;
   ```

3. Run migrations to create tables:
   ```bash
   alembic upgrade head
   ```