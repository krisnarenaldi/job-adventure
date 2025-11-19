# Backend Architecture Documentation

## 📁 Folder Structure

```
backend/
├── app/
│   ├── api/                    # API endpoints
│   │   └── v1/
│   │       ├── api.py         # Router aggregation
│   │       └── endpoints/     # Individual endpoint modules
│   ├── core/                  # Core functionality
│   │   ├── config.py         # Configuration settings
│   │   ├── security.py       # Authentication & JWT
│   │   ├── deps.py           # Dependencies (auth, DB)
│   │   ├── exceptions.py     # Custom exceptions
│   │   ├── error_handler.py  # Error handling
│   │   ├── logging_config.py # Logging setup
│   │   └── redis.py          # Redis connection
│   ├── db/                    # Database
│   │   ├── database.py       # SQLAlchemy base
│   │   └── session.py        # DB session management
│   ├── middleware/            # Middleware
│   │   ├── logging_middleware.py
│   │   ├── cache_middleware.py
│   │   └── session_middleware.py
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── company.py
│   │   ├── job.py
│   │   ├── resume.py
│   │   ├── match_result.py
│   │   ├── interview.py
│   │   ├── candidate_note.py
│   │   └── shared_link.py
│   ├── repositories/          # Data access layer
│   │   ├── base.py           # Base repository
│   │   └── [model]_repository.py
│   ├── schemas/               # Pydantic schemas (DTOs)
│   │   ├── auth.py
│   │   ├── job.py
│   │   ├── resume.py
│   │   ├── matching.py
│   │   └── ...
│   ├── services/              # Business logic
│   │   ├── embedding_service.py
│   │   ├── matching_engine.py
│   │   ├── document_processor.py
│   │   ├── resume_parser.py
│   │   ├── skill_extraction_service.py
│   │   ├── similarity_service.py
│   │   ├── explanation_service.py
│   │   ├── cache_service.py
│   │   ├── analytics_service.py
│   │   └── monitoring_service.py
│   └── main.py                # FastAPI application
├── alembic/                   # Database migrations
├── scripts/                   # Utility scripts
├── uploads/                   # Uploaded files
├── requirements.txt           # Python dependencies
└── run.py                     # Application entry point
```

## 🏗️ Architecture Pattern

The application follows a **layered architecture**:

```
┌─────────────────────────────────────┐
│         API Layer (FastAPI)         │  ← HTTP endpoints
├─────────────────────────────────────┤
│      Service Layer (Business)       │  ← Business logic
├─────────────────────────────────────┤
│   Repository Layer (Data Access)    │  ← Database operations
├─────────────────────────────────────┤
│     Model Layer (SQLAlchemy)        │  ← Database schema
└─────────────────────────────────────┘
```

## 📚 Libraries and Their Purposes

### Web Framework

- **FastAPI (0.104.1)** - Modern async web framework

  - Fast performance with async/await
  - Automatic API documentation (Swagger/OpenAPI)
  - Built-in validation with Pydantic
  - Type hints support

- **Uvicorn (0.24.0)** - ASGI server
  - Runs FastAPI application
  - Supports async operations
  - High performance

### Database

- **SQLAlchemy (2.0.23)** - ORM (Object-Relational Mapping)

  - Async support with AsyncSession
  - Database abstraction layer
  - Query builder

- **asyncpg (0.29.0)** - PostgreSQL async driver

  - Fast PostgreSQL driver for Python
  - Async/await support

- **Alembic (1.12.1)** - Database migrations

  - Version control for database schema
  - Automatic migration generation

- **psycopg2-binary (2.9.9)** - PostgreSQL adapter

  - Synchronous PostgreSQL driver
  - Used by Alembic

- **pgvector (0.2.4)** - Vector similarity extension
  - Stores embeddings in PostgreSQL
  - Fast vector similarity search
  - Cosine similarity operations

### Caching

- **Redis (5.0.1)** - In-memory cache

  - Cache embeddings and match results
  - Session storage
  - Rate limiting

- **aioredis (2.0.1)** - Async Redis client
  - Async Redis operations
  - Connection pooling

### Authentication & Security

- **python-jose[cryptography] (3.3.0)** - JWT tokens

  - Create and verify JWT tokens
  - Token-based authentication

- **passlib[bcrypt] (1.7.4)** - Password hashing
  - Secure password hashing with bcrypt
  - Password verification

### Configuration

- **pydantic[email] (>=2.9.0)** - Data validation

  - Request/response validation
  - Settings management
  - Type checking

- **pydantic-settings (2.1.0)** - Settings from env

  - Load configuration from environment variables
  - Type-safe settings

- **python-dotenv (1.0.0)** - Environment variables
  - Load .env files
  - Development configuration

### AI & Machine Learning

- **torch (2.2.0+cpu)** - PyTorch (CPU-only)

  - Deep learning framework
  - Required by sentence-transformers
  - CPU-only version to save space

- **sentence-transformers (3.0.1)** - Embeddings

  - Generate semantic embeddings
  - Pre-trained models (all-MiniLM-L6-v2)
  - 384-dimensional vectors

- **anthropic (>=0.40.0)** - Claude AI (optional)

  - Generate match explanations
  - AI-powered insights
  - Can be removed to save space

- **numpy (1.26.4)** - Numerical operations
  - Array operations
  - Vector calculations
  - Required by ML libraries

### Document Processing

- **PyPDF2 (3.0.1)** - PDF extraction

  - Extract text from PDF files
  - Resume parsing

- **python-docx (1.1.0)** - DOCX extraction

  - Extract text from Word documents
  - Resume parsing

- **pdfminer.six (20221105)** - Advanced PDF parsing

  - Fallback for complex PDFs
  - Better text extraction

- **openpyxl (3.1.2)** - Excel files
  - Read/write Excel files
  - Data export

### Utilities

- **httpx (0.25.2)** - HTTP client

  - Async HTTP requests
  - API calls to external services

- **python-dateutil (2.8.2)** - Date utilities

  - Date parsing and manipulation
  - Timezone handling

- **psutil (5.9.6)** - System monitoring

  - CPU and memory usage
  - Performance monitoring

- **python-multipart (0.0.6)** - File uploads

  - Handle multipart form data
  - File upload support

- **greenlet** - Async support
  - Required by SQLAlchemy async

## 🔄 Application Flow: User Registration

Let me trace the complete flow from user registration to job matching:

### 1. User Registration Flow

```
┌─────────────┐
│   Client    │
│  (Frontend) │
└──────┬──────┘
       │ POST /api/v1/auth/register
       │ {email, password, full_name, role, company_name}
       ▼
┌─────────────────────────────────────┐
│  API Layer                          │
│  app/api/v1/endpoints/auth.py       │
│  - register() function              │
└──────┬──────────────────────────────┘
       │ 1. Validate request (Pydantic)
       │ 2. Check if email exists
       ▼
┌─────────────────────────────────────┐
│  Repository Layer                   │
│  app/repositories/user.py           │
│  - UserRepository.get_by_email()    │
└──────┬──────────────────────────────┘
       │ 3. Query database
       ▼
┌─────────────────────────────────────┐
│  Database (PostgreSQL)              │
│  SELECT * FROM users                │
│  WHERE email = ?                    │
└──────┬──────────────────────────────┘
       │ 4. If exists → 400 Error
       │ 5. If not exists → Continue
       ▼
┌─────────────────────────────────────┐
│  Company Repository                 │
│  - Check/create company             │
└──────┬──────────────────────────────┘
       │ 6. Get or create company
       ▼
┌─────────────────────────────────────┐
│  Security Service                   │
│  app/core/security.py               │
│  - get_password_hash()              │
└──────┬──────────────────────────────┘
       │ 7. Hash password with bcrypt
       ▼
┌─────────────────────────────────────┐
│  User Repository                    │
│  - create_user()                    │
└──────┬──────────────────────────────┘
       │ 8. Insert into database
       ▼
┌─────────────────────────────────────┐
│  Database                           │
│  INSERT INTO users                  │
│  (id, email, hashed_password, ...)  │
└──────┬──────────────────────────────┘
       │ 9. Return user object
       ▼
┌─────────────────────────────────────┐
│  API Response                       │
│  UserResponse (Pydantic schema)     │
│  {id, email, full_name, role, ...}  │
└──────┬──────────────────────────────┘
       │ 10. JSON response
       ▼
┌─────────────┐
│   Client    │
│  (Frontend) │
└─────────────┘
```

### 2. User Login Flow

```
Client → POST /api/v1/auth/login
         {email, password}
           ↓
API Layer (auth.py)
  → UserRepository.authenticate()
           ↓
Security Service
  → verify_password(plain, hashed)
  → passlib.verify() with bcrypt
           ↓
If valid:
  → create_access_token()
  → JWT token with user_id
  → python-jose encodes token
           ↓
Response: {access_token, token_type, user}
```

### 3. Complete Job Matching Flow

```
┌──────────────────────────────────────────────────────────┐
│ STEP 1: Job Creation                                     │
└──────────────────────────────────────────────────────────┘
Client → POST /api/v1/jobs
         {title, company, description, requirements, ...}
           ↓
API Layer (jobs.py)
  → Authenticate user (JWT token)
  → JobRepository.create()
           ↓
Database
  → INSERT INTO job_descriptions
  → Returns job object (without embedding yet)
           ↓
Background Task
  → MatchingEngine.generate_job_embedding()
           ↓
EmbeddingService
  → Combine: title + description + requirements
  → SentenceTransformer.encode()
  → Generate 384-dim vector
           ↓
Database
  → UPDATE job_descriptions SET embedding = vector
  → Store in pgvector column

┌──────────────────────────────────────────────────────────┐
│ STEP 2: Resume Upload                                    │
└──────────────────────────────────────────────────────────┘
Client → POST /api/v1/resumes/upload
         {file: resume.pdf, job_id: uuid}
           ↓
API Layer (resumes.py)
  → FileService.save_file()
  → Store in uploads/ directory
           ↓
DocumentProcessor
  → Extract text from PDF/DOCX
  → PyPDF2 or pdfminer.six
  → Returns raw text
           ↓
ResumeParser
  → Extract sections (experience, skills, education)
  → Pattern-based extraction (no Spacy needed)
  → Extract candidate name, email, phone
           ↓
SkillExtractionService
  → Extract technical skills
  → Extract soft skills
  → Extract certifications
  → Pattern matching + keyword database
           ↓
EmbeddingService
  → Generate embedding for resume content
  → SentenceTransformer.encode()
  → 384-dim vector
           ↓
Database
  → INSERT INTO resumes
  → Store: content, sections, skills, embedding
           ↓
Automatic Matching Trigger
  → MatchingEngine.match_resume_to_job()

┌──────────────────────────────────────────────────────────┐
│ STEP 3: Matching Process                                 │
└──────────────────────────────────────────────────────────┘
MatchingEngine.match_resume_to_job()
           ↓
1. Similarity Calculation
   → SimilarityService.calculate_similarity()
   → Cosine similarity between vectors
   → pgvector: job.embedding <=> resume.embedding
   → Returns similarity score (0-1)
           ↓
2. Skill Matching
   → SkillExtractionService.match_skills()
   → Compare job.skills_required vs resume.extracted_skills
   → Calculate: matched, missing, additional skills
   → Returns skill match percentage
           ↓
3. Score Calculation
   → overall_score = (similarity * 0.6) + (skill_match * 0.4)
   → Weighted combination
           ↓
4. Generate Explanation (Template-based)
   → ExplanationService.generate_template_explanation()
   → Uses predefined templates
   → No AI API calls (per user request)
   → Fills in: matched skills, missing skills, score
           ↓
5. Store Match Result
   → MatchResultRepository.create()
   → INSERT INTO match_results
   → Store: scores, explanation, skills, status=PENDING
           ↓
Response to Client
  → Match result with score and explanation

┌──────────────────────────────────────────────────────────┐
│ STEP 4: View Candidates                                  │
└──────────────────────────────────────────────────────────┘
Client → GET /api/v1/jobs/{job_id}/candidates
           ↓
API Layer (jobs.py)
  → MatchResultRepository.get_by_job()
  → JOIN match_results + resumes
  → ORDER BY match_score DESC
           ↓
Response
  → List of candidates with:
    - Resume details
    - Match score
    - Explanation
    - Status (pending/shortlisted/rejected)
    - Skills analysis

┌──────────────────────────────────────────────────────────┐
│ STEP 5: Update Candidate Status                          │
└──────────────────────────────────────────────────────────┘
Client → PATCH /api/v1/jobs/{job_id}/candidates/{resume_id}
         {status: "shortlisted"}
           ↓
API Layer (jobs.py)
  → MatchResultRepository.update_status()
  → UPDATE match_results SET status = 'shortlisted'
           ↓
Response
  → Updated match result

┌──────────────────────────────────────────────────────────┐
│ STEP 6: Schedule Interview                               │
└──────────────────────────────────────────────────────────┘
Client → POST /api/v1/interviews
         {resume_id, job_id, interview_type, scheduled_at, ...}
           ↓
API Layer (interviews.py)
  → Validate: candidate not rejected
  → InterviewRepository.create()
           ↓
Database
  → INSERT INTO interviews
  → Store: type, date, location/link, status=SCHEDULED
           ↓
Response
  → Interview details
```

## 🔑 Key Components Explained

### 1. **Models** (app/models/)

SQLAlchemy ORM models representing database tables:

- **User**: Authentication and user management
- **Company**: Organization data
- **JobDescription**: Job postings with embeddings
- **Resume**: Candidate resumes with embeddings
- **MatchResult**: Job-resume matches with scores
- **Interview**: Interview scheduling
- **CandidateNote**: Recruiter notes
- **SharedLink**: Shareable candidate links

### 2. **Repositories** (app/repositories/)

Data access layer - handles all database operations:

- Inherits from `BaseRepository` (CRUD operations)
- Async methods using `AsyncSession`
- Query building with SQLAlchemy
- Example: `UserRepository.get_by_email()`

### 3. **Services** (app/services/)

Business logic layer:

**EmbeddingService**

- Loads SentenceTransformer model (all-MiniLM-L6-v2)
- Generates 384-dimensional embeddings
- Caches embeddings in Redis
- Batch processing support

**MatchingEngine**

- Orchestrates the matching process
- Combines similarity + skill matching
- Calculates overall scores
- Generates explanations

**DocumentProcessor**

- Extracts text from PDF/DOCX
- Handles multiple formats
- Fallback mechanisms

**ResumeParser**

- Parses resume sections
- Extracts structured data
- Pattern-based extraction

**SkillExtractionService**

- Extracts skills from text
- Pattern matching (no Spacy needed)
- Skill categorization
- Skill matching

**SimilarityService**

- Calculates cosine similarity
- Uses pgvector for fast queries
- Batch similarity calculations

**ExplanationService**

- Template-based explanations
- No AI API calls (optimized)
- Customizable templates

**CacheService**

- Redis caching
- Embedding cache
- Match result cache

**AnalyticsService**

- Recruitment metrics
- Performance tracking

**MonitoringService**

- System health monitoring
- Performance metrics

### 4. **Schemas** (app/schemas/)

Pydantic models for request/response validation:

- Input validation
- Output serialization
- Type checking
- Documentation

### 5. **Core** (app/core/)

**config.py**

- Settings from environment variables
- Database URLs
- API keys
- Feature flags

**security.py**

- JWT token creation/verification
- Password hashing (bcrypt)
- Token validation

**deps.py**

- Dependency injection
- `get_current_user()` - Auth middleware
- `get_db()` - Database session

**error_handler.py**

- Centralized error handling
- Retry logic
- Circuit breaker pattern
- Graceful degradation

**exceptions.py**

- Custom exception classes
- Structured error responses

### 6. **Middleware** (app/middleware/)

**LoggingMiddleware**

- Request/response logging
- Performance tracking

**CacheMiddleware**

- HTTP caching
- Cache headers

**SessionMiddleware**

- Session management
- Cookie handling

## 🗄️ Database Schema

### Key Tables

**users**

- id (UUID, PK)
- email (unique)
- hashed_password
- full_name
- role (recruiter/hiring_manager/admin)
- company_id (FK)
- is_active
- created_at, updated_at

**companies**

- id (UUID, PK)
- name (unique)
- created_at

**job_descriptions**

- id (UUID, PK)
- title, company, description, requirements
- location, salary_range, employment_type
- skills_required (array)
- **embedding (vector(384))** ← pgvector
- created_by (FK → users)
- is_active
- created_at, updated_at

**resumes**

- id (UUID, PK)
- candidate_name, email, phone
- content (full text)
- original_filename, file_path
- sections (JSON)
- extracted_skills (array)
- **embedding (vector(384))** ← pgvector
- uploaded_by (FK → users)
- is_processed
- uploaded_at, processed_at

**match_results**

- id (UUID, PK)
- job_id (FK → job_descriptions)
- resume_id (FK → resumes)
- match_score (0-100)
- confidence_score
- explanation (text)
- key_strengths (array)
- missing_skills (array)
- skill_matches (JSON)
- experience_score, skills_score, education_score
- **status** (pending/shortlisted/rejected/maybe)
- status_updated_at, status_updated_by
- created_at, updated_at
- UNIQUE(job_id, resume_id) ← Prevent duplicates

**interviews**

- id (UUID, PK)
- resume_id (FK → resumes)
- job_id (FK → job_descriptions)
- interview_type (phone/video/in-person)
- scheduled_at
- duration_minutes
- location, meeting_link
- notes
- **status** (scheduled/completed/cancelled/rescheduled)
- created_by (FK → users)
- created_at, updated_at

## 🔐 Authentication Flow

1. **Registration**: Password hashed with bcrypt → Stored in DB
2. **Login**: Verify password → Generate JWT token
3. **Protected Routes**: Extract token → Verify → Get user
4. **Token Structure**: `{exp: timestamp, sub: user_id}`

## 🚀 Performance Optimizations

1. **Async/Await**: All I/O operations are async
2. **Connection Pooling**: Database and Redis connections
3. **Caching**: Redis cache for embeddings and results
4. **Batch Processing**: Bulk embedding generation
5. **Vector Indexing**: pgvector IVFFlat index for fast similarity
6. **Query Optimization**: Proper indexes on frequently queried columns
7. **Lazy Loading**: Models load on first use
8. **Circuit Breaker**: Prevents cascading failures

## 📊 Monitoring & Logging

- **Structured Logging**: JSON logs with context
- **Performance Tracking**: Request duration, DB queries
- **Error Tracking**: Centralized error handling
- **Health Checks**: `/api/v1/health` endpoint
- **Metrics**: CPU, memory, request counts

## 🔄 Data Flow Summary

```
User Register → Hash Password → Store in DB
     ↓
User Login → Verify Password → Generate JWT
     ↓
Create Job → Store Job → Generate Embedding → Store Vector
     ↓
Upload Resume → Extract Text → Parse Sections → Extract Skills
     ↓
Generate Embedding → Store Vector → Auto-Match
     ↓
Calculate Similarity (pgvector) + Skill Match → Overall Score
     ↓
Generate Explanation → Store Match Result
     ↓
View Candidates → Sorted by Score
     ↓
Update Status → Shortlist/Reject
     ↓
Schedule Interview → Store Interview
```

This architecture provides a scalable, maintainable, and performant system for AI-powered resume matching! 🎉
