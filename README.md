# Resume Job Matching System

An AI-powered system that automatically analyzes job descriptions and candidate resumes to evaluate compatibility, provide match scores, identify skill gaps, and generate explanations.

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL (with pgvector extension)
- Redis

### Local Development Setup

1. Create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy the environment file and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your database and Redis connection details
   ```

4. Run the FastAPI application:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. The API will be available at `http://localhost:8000`
   - Health check: `http://localhost:8000/health`
   - API documentation: `http://localhost:8000/docs`

### Optional: Docker Setup

If you prefer using Docker for PostgreSQL and Redis:

1. Start the services:
   ```bash
   docker-compose up postgres redis -d
   ```

2. Run the backend locally as described above

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Configuration and settings
│   │   ├── db/           # Database configuration
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic services
│   │   └── main.py       # FastAPI application
│   ├── scripts/          # Database initialization scripts
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── .env.example
└── README.md
```

## Services

- **Backend API**: FastAPI application (Port 8000)
- **PostgreSQL**: Database with pgvector extension (default Port 5432)
- **Redis**: Cache and session storage (default Port 6379)

## Database Setup

### PostgreSQL with pgvector
1. Install PostgreSQL and the pgvector extension
2. Create a database named `resume_matching`
3. Enable the vector extension: `CREATE EXTENSION vector;`

### Redis
1. Install and start Redis server
2. Default configuration should work for development

## Environment Variables

See `.env.example` for all available configuration options.

## API Documentation

Once the application is running, visit `http://localhost:8000/docs` for interactive API documentation.