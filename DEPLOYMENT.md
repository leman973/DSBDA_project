# DSBDA Authentication & Docker Setup Guide

## Overview

This guide covers the authentication system and Docker deployment for the DSBDA Data Analysis Assistant.

## Features Added

### 🔐 Authentication System
- **User Registration & Login** - Secure account creation with username, email, and password
- **JWT Token-based Auth** - Stateless authentication with configurable expiration (30 minutes default)
- **Password Hashing** - Bcrypt for secure password storage
- **User-specific Datasets** - Each user can only access their own uploaded datasets
- **Protected API Endpoints** - All data operations require authentication

### 🐳 Docker Deployment
- **PostgreSQL Database** - Production-ready database with persistent storage
- **Containerized Backend** - FastAPI application in Docker
- **Containerized Frontend** - React application served via Nginx
- **Docker Compose** - One-command deployment of all services

---

## Quick Start

### Option 1: Docker Deployment (Recommended)

#### Prerequisites
- Docker Desktop installed
- Gemini API key with billing/quota enabled

#### Steps

1. **Clone and Configure:**
```bash
cd DSBDA_project

# Copy environment template
cp .env.example .env

# Edit .env and change SECRET_KEY to a secure random string (min 32 chars)
# You can generate one using: openssl rand -hex 32
```

2. **Start all services:**
```bash
docker-compose up --build
```

3. **Access the application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432

4. **Create your first user:**
- Go to http://localhost:5173/register
- Create an account with username, email, and password
- Login with your credentials

### Option 2: Local Development (Without Docker)

#### Backend Setup

1. **Install PostgreSQL:**
```bash
# macOS
brew install postgresql@15

# Start PostgreSQL
brew services start postgresql@15

# Create database
createdb dsbda_db
```

2. **Setup Python environment:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings:
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dsbda_db
# SECRET_KEY=your-secret-key-min-32-characters
```

4. **Run backend:**
```bash
uvicorn main:app --reload --port 8000
```

#### Frontend Setup

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Run development server:**
```bash
npm run dev
```

3. **Access application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

---

## API Endpoints

### Authentication Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/auth/register` | POST | No | Register new user |
| `/api/auth/login` | POST | No | Login and get JWT token |
| `/api/auth/me` | GET | Yes | Get current user info |

### Dataset Endpoints (All require authentication)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/datasets/upload` | POST | Upload CSV/XLSX/PDF |
| `/api/datasets` | GET | List user's datasets |
| `/api/datasets/{id}` | GET | Get dataset info |
| `/api/datasets/{id}/data` | GET | Get dataset data |
| `/api/datasets/{id}/summary` | GET | Get dataset summary |
| `/api/datasets/{id}` | DELETE | Delete dataset |

### Chat Endpoint

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message and get analysis |

---

## Usage Examples

### 1. Register a new user

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepass123"
  }'
```

### 2. Login and get token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -F "username=johndoe" \
  -F "password=securepass123"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 30
}
```

### 3. Upload dataset (with token)

```bash
curl -X POST http://localhost:8000/api/datasets/upload \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@your_dataset.csv"
```

### 4. List your datasets

```bash
curl -X GET http://localhost:8000/api/datasets \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Architecture

### Services

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Frontend      │──────│   Backend       │──────│   PostgreSQL    │
│   (React)       │      │   (FastAPI)     │      │   (Database)    │
│   Port 5173     │      │   Port 8000     │      │   Port 5432     │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                │
                                ↓
                         ┌─────────────────┐
                         │   Gemini API    │
                         │   (Google)      │
                         │   HTTPS         │
                         └─────────────────┘
```

### Database Schema

**Users Table:**
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email
- `hashed_password` - Bcrypt hashed password
- `is_active` - Account status
- `created_at` - Registration date

**Datasets Table:**
- `id` - UUID primary key
- `name` - Dataset name
- `file_path` - Path to uploaded file
- `original_filename` - Original file name
- `rows` - Number of rows
- `columns` - Number of columns
- `columns_info` - JSON column metadata
- `owner_id` - Foreign key to Users
- `created_at` - Upload date
- `updated_at` - Last update

---

## Security Considerations

### Password Requirements
- Minimum 6 characters
- Must be alphanumeric username
- Stored as bcrypt hashes (never plain text)

### JWT Token Security
- Expires after 30 minutes (configurable)
- Signed with HMAC-SHA256
- Must be included in Authorization header

### Best Practices

1. **Change SECRET_KEY in production!**
   - Generate a strong random key (min 32 chars)
   - Use environment variables or secrets manager
   - Never commit to version control

2. **Use HTTPS in production**
   - Always encrypt traffic in production
   - Use reverse proxy (Nginx, Traefik)

3. **Database security**
   - Change default PostgreSQL password
   - Use strong passwords
   - Restrict database access to internal network

4. **CORS configuration**
   - Update CORS_ORIGINS for production domains
   - Don't use wildcard (*) in production

---

## Troubleshooting

### Backend won't start

**Error: Could not connect to database**
```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres
docker-compose logs backend
```

**Solution:** Make sure PostgreSQL container is healthy before backend starts

### Authentication errors

**Error: Could not validate credentials**
- Token may have expired (default 30 minutes)
- Logout and login again to get new token
- Check SECRET_KEY matches in .env

**Error: Incorrect username or password**
- Verify credentials are correct
- Check if user exists in database

### Gemini connection issues

**Error: Gemini API authentication failed**

- Verify `GEMINI_API_KEY` in `.env`
- Ensure API key has access to Gemini API
- Ensure billing/quota is enabled in Google Cloud

### Frontend build errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## Advanced Configuration

### Custom Token Expiration

Edit `.env`:
```env
ACCESS_TOKEN_EXPIRE_MINUTES=60  # 1 hour
```

### Using Different Gemini Model

Edit `.env`:
```env
GEMINI_MODEL=gemini-1.5-pro
# or
GEMINI_MODEL=gemini-2.5-flash
```

### Production Database

For production, use environment variables or secrets manager:

```yaml
# docker-compose.prod.yml
services:
  backend:
    environment:
      DATABASE_URL: postgresql://user:password@db-host:5432/dbname
      SECRET_KEY: ${SECRET_KEY}  # From environment
```

---

## Backup and Restore

### Backup Database

```bash
docker exec dsbda_postgres pg_dump -U postgres dsbda_db > backup.sql
```

### Restore Database

```bash
cat backup.sql | docker exec -i dsbda_postgres psql -U postgres dsbda_db
```

---

## Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/api/health

# Frontend
curl http://localhost:5173
```

---

## Cleanup

### Stop all services

```bash
docker-compose down
```

### Remove volumes (deletes all data!)

```bash
docker-compose down -v
```

### Rebuild from scratch

```bash
docker-compose down -v --rmi all
docker-compose up --build
```

---

## Next Steps

1. **Create your user account** at http://localhost:5173/register
2. **Upload a dataset** (CSV, Excel, or PDF)
3. **Ask questions** about your data in natural language
4. **Generate visualizations** by requesting charts

Enjoy secure, containerized data analysis! 🚀
