# Backend Quick Reference

## 📚 Library Cheat Sheet

| Library | Version | Purpose | Used For |
|---------|---------|---------|----------|
| **FastAPI** | 0.104.1 | Web framework | API endpoints, routing, validation |
| **Uvicorn** | 0.24.0 | ASGI server | Run FastAPI app |
| **SQLAlchemy** | 2.0.23 | ORM | Database models, queries |
| **asyncpg** | 0.29.0 | PostgreSQL driver | Async DB operations |
| **Alembic** | 1.12.1 | Migrations | Database schema versioning |
| **pgvector** | 0.2.4 | Vector extension | Store/search embeddings |
| **Redis** | 5.0.1 | Cache | Cache embeddings, results |
| **python-jose** | 3.3.0 | JWT | Authentication tokens |
| **passlib** | 1.7.4 | Password hashing | Bcrypt password security |
| **Pydantic** | >=2.9.0 | Validation | Request/response schemas |
| **torch** | 2.2.0+cpu | Deep learning | Required by transformers |
| **sentence-transformers** | 3.0.1 | Embeddings | Generate 384-dim vectors |
| **anthropic** | >=0.40.0 | AI (optional) | Claude API (can remove) |
| **numpy** | 1.26.4 | Math | Vector operations |
| **PyPDF2** | 3.0.1 | PDF parsing | Extract resume text |
| **python-docx** | 1.1.0 | DOCX parsing | Extract resume text |
| **pdfminer.six** | 20221105 | PDF fallback | Complex PDF extraction |

## 🗂️ Folder Structure Quick Map

```
backend/app/
├── api/v1/endpoints/     → HTTP endpoints (auth, jobs, resumes, etc.)
├── core/                 → Config, security, dependencies
├── db/                   → Database connection
├── middleware/           → Request/response processing
├── models/               → SQLAlchemy ORM (database tables)
├── repositories/         → Data access layer (CRUD)
├── schemas/              → Pydantic models (validation)
├── services/             → Business logic (AI, matching, parsing)
└── main.py              → FastAPI app initialization
```

## 🔑 Key Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, middleware, startup/shutdown |
| `core/config.py` | Environment variables, settings |
| `core/security.py` | JWT, password hashing |
| `core/deps.py` | Auth middleware, DB session |
| `api/v1/api.py` | Route aggregation |
| `models/user.py` | User database model |
| `models/job.py` | Job database model |
| `models/resume.py` | Resume database model |
| `models/match_result.py` | Match database model |
| `services/embedding_service.py` | Generate embeddings |
| `services/matching_engine.py` | Orchestrate matching |
| `services/document_processor.py` | Extract text from files |
| `services/resume_parser.py` | Parse resume sections |
| `services/skill_extraction_service.py` | Extract skills |

## 🚀 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login, get JWT token
- `GET /api/v1/auth/me` - Get current user

### Jobs
- `POST /api/v1/jobs` - Create job
- `GET /api/v1/jobs` - List jobs
- `GET /api/v1/jobs/{id}` - Get job details
- `PUT /api/v1/jobs/{id}` - Update job
- `DELETE /api/v1/jobs/{id}` - Delete job
- `GET /api/v1/jobs/{id}/candidates` - Get matched candidates

### Resumes
- `POST /api/v1/resumes/upload` - Upload resume (auto-matches)
- `GET /api/v1/resumes` - List resumes
- `GET /api/v1/resumes/{id}` - Get resume details
- `DELETE /api/v1/resumes/{id}` - Delete resume

### Matching
- `POST /api/v1/matching/match` - Manual match trigger
- `GET /api/v1/matching/results/{job_id}` - Get match results
- `PATCH /api/v1/jobs/{job_id}/candidates/{resume_id}` - Update status

### Interviews
- `POST /api/v1/interviews` - Schedule interview
- `GET /api/v1/interviews` - List interviews
- `GET /api/v1/interviews/{id}` - Get interview details
- `PUT /api/v1/interviews/{id}` - Update interview
- `DELETE /api/v1/interviews/{id}` - Cancel interview

### Analytics
- `GET /api/v1/analytics/dashboard` - Get metrics
- `GET /api/v1/analytics/job/{id}` - Job-specific analytics

### Health
- `GET /api/v1/health` - Health check

## 🔄 Data Flow Summary

### User Registration
```
Frontend → API → Check email → Hash password → Insert DB → Return user
```

### User Login
```
Frontend → API → Get user → Verify password → Create JWT → Return token
```

### Job Creation
```
Frontend → API → Insert job → Generate embedding → Update job → Return
```

### Resume Upload & Matching
```
Frontend → API → Save file → Extract text → Parse sections → 
Extract skills → Generate embedding → Insert resume → 
Auto-match → Calculate similarity → Match skills → 
Generate explanation → Insert match_result → Return
```

### View Candidates
```
Frontend → API → Query match_results JOIN resumes → 
Sort by score → Return list
```

### Schedule Interview
```
Frontend → API → Validate candidate → Insert interview → Return
```

## 🗄️ Database Tables

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `users` | id, email, hashed_password, role | Authentication |
| `companies` | id, name | Organization data |
| `job_descriptions` | id, title, description, **embedding** | Job postings |
| `resumes` | id, candidate_name, content, **embedding** | Candidate resumes |
| `match_results` | job_id, resume_id, match_score, status | Matches |
| `interviews` | resume_id, job_id, scheduled_at, status | Interviews |
| `candidate_notes` | resume_id, job_id, note | Recruiter notes |
| `shared_links` | job_id, token | Shareable links |

## 🧠 AI/ML Components

### Embedding Generation
- **Model**: all-MiniLM-L6-v2 (SentenceTransformer)
- **Dimension**: 384
- **Input**: Text (job description or resume)
- **Output**: Vector [0.123, -0.456, ...]
- **Storage**: PostgreSQL pgvector column

### Similarity Calculation
- **Method**: Cosine similarity
- **Formula**: `job.embedding <=> resume.embedding`
- **Range**: 0 (different) to 1 (identical)
- **Database**: pgvector operator `<=>`

### Skill Matching
- **Method**: Pattern matching + keyword database
- **No Spacy**: Uses regex patterns (lightweight)
- **Output**: matched, missing, additional skills
- **Score**: percentage of required skills matched

### Overall Score
```python
overall_score = (similarity_score * 0.6) + (skill_match * 0.4)
```

### Explanation Generation
- **Method**: Template-based (no AI API calls)
- **Templates**: Predefined text with placeholders
- **Variables**: score, matched_skills, missing_skills
- **Fast**: No external API latency

## 🔐 Authentication

### Password Flow
1. **Registration**: `passlib.hash(password)` → Store hash
2. **Login**: `passlib.verify(input, hash)` → If valid, create JWT
3. **JWT Structure**: `{exp: timestamp, sub: user_id}`
4. **Token Verification**: `python-jose.decode(token)` → Get user_id

### Protected Routes
```python
@router.get("/protected")
async def protected(current_user: User = Depends(get_current_user)):
    # current_user is automatically injected
    return {"user": current_user}
```

## ⚡ Performance Features

- **Async/Await**: All I/O operations non-blocking
- **Connection Pooling**: Reuse DB connections
- **Redis Caching**: Cache embeddings, match results
- **Batch Processing**: Generate multiple embeddings at once
- **Vector Indexing**: IVFFlat index for fast similarity search
- **Query Optimization**: Proper indexes on foreign keys
- **Circuit Breaker**: Prevent cascading failures
- **Graceful Degradation**: Fallback mechanisms

## 🛠️ Common Commands

```bash
# Run development server
cd backend
uvicorn app.main:app --reload

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Run tests
pytest

# Check code style
flake8 app/

# Format code
black app/

# Type checking
mypy app/
```

## 📊 Monitoring

- **Logs**: Structured JSON logs in `backend/logs/`
- **Metrics**: Request duration, DB query time
- **Health**: `/api/v1/health` endpoint
- **Errors**: Centralized error handling with stack traces

## 🔧 Configuration

Environment variables (`.env`):
```bash
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=sk-... (optional)
ENVIRONMENT=development
```

## 📝 Notes

- **No Spacy**: Removed to save space, uses pattern matching
- **CPU-only PyTorch**: Smaller size for deployment
- **Template Explanations**: No AI API calls for explanations
- **Auto-matching**: Resumes automatically matched on upload
- **Duplicate Prevention**: UNIQUE constraint on (job_id, resume_id)

