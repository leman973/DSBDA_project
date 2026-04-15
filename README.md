# DSBDA Data Analysis Assistant

A natural language data analysis tool that allows users to upload datasets and query them using plain English. The application uses Gemini API to understand user queries and perform data analysis.

## 🔐 New Features

- **User Authentication** - Secure login/register with JWT tokens
- **Access Control** - User-specific datasets with ownership
- **PostgreSQL Database** - Production-ready data persistence
- **Docker Support** - One-command deployment with docker-compose

## Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌────────────────────┐
│   Frontend      │──────│   Backend       │──────│   Gemini API       │
│   (React/Vite)  │      │   (FastAPI)     │      │   (Google)         │
│   Port 5173     │      │   Port 8000     │      │   HTTPS            │
└─────────────────┘      └─────────────────┘      └────────────────────┘
```

## Project Structure

```
DSBDA_project/
├── frontend/           # React + Vite frontend
│   ├── src/
│   │   └── pages/
│   │       └── DataAnalysisAssistant.jsx   # Main app component
│   ├── package.json
│   └── vite.config.js
│
├── backend/            # Python FastAPI backend
│   ├── main.py        # API endpoints & logic
│   ├── requirements.txt
│   └── README.md     # Backend-specific docs
│
└── README.md          # This file
```

## Features

- **User Authentication**: Secure registration and login with JWT tokens
- **Access Control**: User-specific datasets - only you can see your data
- **File Upload**: Support for CSV, XLSX, and PDF files
- **Natural Language Queries**: Ask questions in plain English
- **Data Analysis**: Statistical summaries and insights
- **Chart Support**: Vega-Lite chart specifications (bar, line, scatter, pie charts)
- **Real-time Chat**: Interactive conversation with the LLM
- **Docker Deployment**: Production-ready containerization

## Prerequisites

### For Docker Deployment (Recommended):
1. **Docker Desktop** - Docker and docker-compose
2. **Gemini API key** - For LLM inference

### For Local Development:
1. **Node.js** (v18+) - For running the frontend
2. **Python 3.10+** - For running the backend
3. **PostgreSQL 15+** - Database server
4. **Gemini API key** - For running the Gemini LLM

## Installation & Setup

### Quick Start (Docker - Recommended)

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for detailed Docker setup instructions.

```bash
# Clone and configure
cp .env.example .env
# Edit .env and change SECRET_KEY

# Start all services
docker-compose up --build

# Access at http://localhost:5173
```

### Local Development Setup

### 1. Configure Gemini API

```bash
Create a `.env` file and set:
```bash
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
```
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Usage

1. Open your browser to `http://localhost:5173`
2. Upload a CSV or XLSX file using the sidebar or drag-and-drop
3. Select the uploaded dataset
4. Ask questions in plain English, for example:
   - "What are the column names?"
   - "Show me a summary of the data"
   - "What is the average of column X?"
   - "Create a bar chart of column Y"

## API Endpoints

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user |
| `/api/auth/login` | POST | Login and get JWT token |
| `/api/auth/me` | GET | Get current user info |

### Datasets (All require authentication)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/datasets/upload` | POST | Upload a CSV/XLSX/PDF file |
| `/api/datasets` | GET | List all datasets (user's own) |
| `/api/datasets/{id}` | GET | Get dataset information |
| `/api/datasets/{id}/data` | GET | Get paginated data |
| `/api/datasets/{id}/summary` | GET | Get statistical summary |
| `/api/chat` | POST | Send chat message to LLM |
| `/api/health` | GET | Health check |

## Environment Variables

### Backend (.env)

```bash
# Gemini API configuration
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dsbda_db

# JWT Authentication (REQUIRED - Change in production!)
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server config
HOST=0.0.0.0
PORT=8000
```

See `.env.example` for full list of configuration options.

## Troubleshooting

### Gemini API key missing
```
GEMINI_API_KEY is not configured on the backend
```
**Solution**: Add `GEMINI_API_KEY` in `.env` and restart backend

### CORS errors
```
Access to fetch at 'http://localhost:8000/api/...' has been blocked by CORS policy
```
**Solution**: Ensure backend is running and CORS is configured to allow your frontend origin

### Gemini authentication failed
```
Gemini API authentication failed. Check GEMINI_API_KEY.
```
**Solution**: Verify the key and ensure billing/quota are enabled on your Google project

## Tech Stack

- **Frontend**: React 19, Vite 7, Tailwind CSS 4, React Router DOM
- **Backend**: Python, FastAPI, Pandas, SQLAlchemy
- **Database**: PostgreSQL 15
- **Authentication**: JWT (JSON Web Tokens), Bcrypt password hashing
- **LLM**: Gemini API (`gemini-2.5-flash` by default)
- **Deployment**: Docker, Docker Compose

## License

MIT
