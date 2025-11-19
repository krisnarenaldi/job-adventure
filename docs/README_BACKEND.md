# Backend Documentation - Job Match System

## 📖 Overview

This is a **FastAPI-based backend** for an AI-powered job matching system that uses **semantic embeddings** and **skill matching** to rank candidates against job descriptions.

## 🎯 What It Does

1. **User Management**: Registration, login, JWT authentication
2. **Job Management**: Create, update, delete job postings
3. **Resume Processing**: Upload, parse, extract skills from PDF/DOCX
4. **AI Matching**: Generate embeddings, calculate similarity, match skills
5. **Candidate Ranking**: Rank candidates by match score
6. **Interview Scheduling**: Schedule and manage interviews
7. **Analytics**: Track recruitment metrics

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│         API Layer (FastAPI)         │  ← HTTP endpoints
├─────────────────────────────────────┤
│      Service Layer (Business)       │  ← AI, matching, parsing
├─────────────────────────────────────┤
│   Repository Layer (Data Access)    │  ← Database operations
├─────────────────────────────────────┤
│     Model Layer (SQLAlchemy)        │  ← Database schema
└─────────────────────────────────────┘
```

## 📚 Documentation Files

| File | Description |
|------|-------------|
| **BACKEND_ARCHITECTURE.md** | Complete architecture, flow diagrams, detailed explanations |
| **BACKEND_QUICK_REFERENCE.md** | Quick lookup for libraries, endpoints, commands |
| **README_BACKEND.md** | This file - overview and getting started |

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Up Environment
```bash
cp .env.example .env
# Edit .env with your database URL, Redis URL, etc.
```

### 3. Run Migrations
```bash
alembic upgrade head
```

### 4. Start Server
```bash
uvicorn app.main:app --reload
```

Server runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

## 🔑 Key Technologies

### Core Framework
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

### Database
- **PostgreSQL** - Main database
- **pgvector** - Vector similarity search
- **SQLAlchemy 2.0** - Async ORM
- **Alembic** - Migrations

### AI/ML
- **sentence-transformers** - Generate embeddings (384-dim)
- **PyTorch (CPU)** - ML framework
- **numpy** - Vector operations

### Caching & Auth
- **Redis** - Cache embeddings and results
- **python-jose** - JWT tokens
- **passlib** - Password hashing (bcrypt)

### Document Processing
- **PyPDF2** - PDF extraction
- **python-docx** - DOCX extraction
- **pdfminer.six** - Advanced PDF parsing

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/     # API routes
│   │   ├── auth.py          # Registration, login
│   │   ├── jobs.py          # Job CRUD
│   │   ├── resumes.py       # Resume upload
│   │   ├── matching.py      # Matching logic
│   │   └── interviews.py    # Interview scheduling
│   ├── core/                # Core functionality
│   │   ├── config.py        # Settings
│   │   ├── security.py      # JWT, passwords
│   │   └── deps.py          # Dependencies
│   ├── models/              # Database models
│   │   ├── user.py
│   │   ├── job.py
│   │   ├── resume.py
│   │   └── match_result.py
│   ├── repositories/        # Data access
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   │   ├── embedding_service.py
│   │   ├── matching_engine.py
│   │   ├── document_processor.py
│   │   └── skill_extraction_service.py
│   └── main.py             # FastAPI app
├── alembic/                # Database migrations
├── requirements.txt        # Dependencies
└── .env                    # Configuration
```

## 🔄 Complete Flow: User Registration → Job Matching

### 1. User Registers
```
POST /api/v1/auth/register
{email, password, full_name, role, company_name}
  ↓
Hash password with bcrypt
  ↓
Store in database
  ↓
Return user object
```

### 2. User Logs In
```
POST /api/v1/auth/login
{email, password}
  ↓
Verify password
  ↓
Generate JWT token
  ↓
Return {access_token, user}
```

### 3. Create Job
```
POST /api/v1/jobs (with JWT token)
{title, company, description, requirements, skills_required}
  ↓
Store job in database
  ↓
Generate embedding (384-dim vector)
  ↓
Store embedding in pgvector column
  ↓
Return job with embedding
```

### 4. Upload Resume
```
POST /api/v1/resumes/upload
{file: resume.pdf, job_id}
  ↓
Extract text from PDF/DOCX
  ↓
Parse sections (experience, skills, education)
  ↓
Extract skills (pattern matching)
  ↓
Generate embedding (384-dim vector)
  ↓
Store resume with embedding
  ↓
**AUTO-MATCH** to job
```

### 5. Matching Process (Automatic)
```
Get job embedding and resume embedding
  ↓
Calculate cosine similarity (pgvector)
  ↓
Match skills (required vs extracted)
  ↓
Calculate overall score:
  overall = (similarity * 0.6) + (skill_match * 0.4)
  ↓
Generate explanation (template-based)
  ↓
Store match_result with score and status=PENDING
  ↓
Return match result
```

### 6. View Candidates
```
GET /api/v1/jobs/{job_id}/candidates
  ↓
Query match_results JOIN resumes
  ↓
Sort by match_score DESC
  ↓
Return ranked list of candidates
```

### 7. Update Candidate Status
```
PATCH /api/v1/jobs/{job_id}/candidates/{resume_id}
{status: "shortlisted"}
  ↓
Update match_result.status
  ↓
Return updated result
```

### 8. Schedule Interview
```
POST /api/v1/interviews
{resume_id, job_id, interview_type, scheduled_at}
  ↓
Validate: candidate not rejected
  ↓
Store interview
  ↓
Return interview details
```

## 🧠 How AI Matching Works

### Step 1: Generate Embeddings
- Uses **SentenceTransformer** model: `all-MiniLM-L6-v2`
- Converts text to **384-dimensional vector**
- Captures semantic meaning

```python
job_text = f"{title} {description} {requirements}"
job_embedding = model.encode(job_text)  # [0.123, -0.456, ...]
```

### Step 2: Calculate Similarity
- Uses **cosine similarity** via pgvector
- Compares job embedding vs resume embedding
- Returns score 0-1 (0=different, 1=identical)

```sql
SELECT resume_id, 
       1 - (job.embedding <=> resume.embedding) as similarity
FROM resumes
ORDER BY similarity DESC
```

### Step 3: Match Skills
- Extracts skills from job requirements
- Extracts skills from resume
- Calculates: matched, missing, additional skills
- Returns skill match percentage

### Step 4: Calculate Overall Score
```python
overall_score = (similarity_score * 0.6) + (skill_match_percentage * 0.4)
```

### Step 5: Generate Explanation
- Uses **template-based** approach (no AI API calls)
- Fills in: score, matched skills, missing skills
- Fast and cost-effective

## 🗄️ Database Schema

### Key Tables

**users** - Authentication
- id, email, hashed_password, role, company_id

**job_descriptions** - Job postings
- id, title, description, requirements, skills_required
- **embedding** (vector(384)) ← Semantic vector

**resumes** - Candidate resumes
- id, candidate_name, email, content, extracted_skills
- **embedding** (vector(384)) ← Semantic vector

**match_results** - Job-resume matches
- job_id, resume_id, match_score, explanation
- key_strengths, missing_skills, **status**
- UNIQUE(job_id, resume_id) ← Prevent duplicates

**interviews** - Interview scheduling
- resume_id, job_id, interview_type, scheduled_at, status

## 🔐 Authentication

- **JWT tokens** for authentication
- **Bcrypt** for password hashing
- **Bearer token** in Authorization header
- Token expires after 30 minutes (configurable)

## ⚡ Performance Features

- ✅ **Async/await** - Non-blocking I/O
- ✅ **Redis caching** - Cache embeddings and results
- ✅ **Connection pooling** - Reuse DB connections
- ✅ **Vector indexing** - Fast similarity search with IVFFlat
- ✅ **Batch processing** - Generate multiple embeddings at once
- ✅ **Circuit breaker** - Prevent cascading failures

## 📊 API Documentation

Interactive API docs available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```

## 🔧 Configuration

Key environment variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI (optional)
ANTHROPIC_API_KEY=sk-...

# Environment
ENVIRONMENT=development
```

## 📈 Monitoring

- **Health check**: `GET /api/v1/health`
- **Logs**: Structured JSON logs in `backend/logs/`
- **Metrics**: Request duration, DB query time
- **Errors**: Centralized error handling

## 🚢 Deployment

See deployment guides:
- **RAILWAY_DEPLOYMENT.md** - Deploy to Railway
- **DEPLOYMENT_OPTIONS.md** - Compare platforms
- **QUICK_DEPLOY.md** - Quick start guide

## 📚 Learn More

- **BACKEND_ARCHITECTURE.md** - Deep dive into architecture
- **BACKEND_QUICK_REFERENCE.md** - Quick lookup reference
- **API Docs** - `http://localhost:8000/docs`

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Run tests
4. Submit pull request

## 📝 Notes

- **No Spacy**: Uses pattern matching instead (saves ~200MB)
- **CPU-only PyTorch**: Optimized for deployment (saves ~500MB)
- **Template explanations**: No AI API calls (fast and free)
- **Auto-matching**: Resumes matched automatically on upload
- **Duplicate prevention**: UNIQUE constraint prevents duplicate matches

---

**Ready to explore?** Start with `BACKEND_ARCHITECTURE.md` for detailed flow diagrams! 🚀

