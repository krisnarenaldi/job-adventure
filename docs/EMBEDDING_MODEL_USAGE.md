# Embedding Model Usage Documentation

## Overview

This document explains where, when, and how the `all-MiniLM-L6-v2` model is used in the Resume Job Matching System.

---

## Model Information

### What is `all-MiniLM-L6-v2`?

- **Model Name**: `all-MiniLM-L6-v2`
- **Type**: Sentence Transformer (pre-trained neural network)
- **Purpose**: Convert text into semantic embeddings (numerical vectors)
- **Output Dimension**: 384-dimensional vectors
- **Library**: `sentence-transformers` (HuggingFace)
- **Size**: ~90 MB
- **Performance**: Fast inference, optimized for semantic similarity tasks

### Why This Model?

1. **Lightweight**: Small model size suitable for free-tier deployments
2. **Fast**: Quick inference time for real-time applications
3. **Accurate**: Good balance between speed and quality
4. **Pre-trained**: No training required, ready to use
5. **Multilingual Support**: Works reasonably well with multiple languages

---

## Where the Model is Used

### 1. Core Service Location

**File**: `backend/app/services/embedding_service.py`

```python
class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self.embedding_dimension = 384  # all-MiniLM-L6-v2 outputs 384-dimensional vectors
```

The model is initialized as a singleton instance:
```python
embedding_service = EmbeddingService()
```

### 2. Initialization

**When**: Application startup (in `main.py`)

**File**: `backend/app/main.py`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from app.services.embedding_service import embedding_service
    await embedding_service.initialize()  # Model is loaded here
    
    yield
    
    # Shutdown
    await embedding_service.close()
```

**What happens**:
1. Downloads the model from HuggingFace (first time only, ~90 MB)
2. Loads the model into memory
3. Model stays in memory for the lifetime of the application

---

## When the Model is Used

### Use Case 1: Resume Processing

**File**: `backend/app/api/v1/endpoints/resumes.py`

**Trigger**: When a user uploads a resume

**Flow**:
```python
async def process_resume_content(...):
    # 1. Parse resume content from PDF/DOCX
    resume_content = await resume_parser.parse(file_path)
    
    # 2. Generate embedding from resume text
    embedding_service = EmbeddingService()
    await embedding_service.initialize()
    embedding = await embedding_service.generate_embedding(resume.content)
    
    # 3. Store embedding in database (PostgreSQL with pgvector)
    await resume_repo.update_embedding(resume.id, embedding)
```

**Purpose**: Convert resume text into a 384-dimensional vector for semantic search and matching.

---

### Use Case 2: Job Description Processing

**File**: `backend/app/api/v1/endpoints/jobs.py`

**Trigger**: When a recruiter creates or updates a job posting

**Flow**:
```python
async def create_job(...):
    # 1. Create job in database
    job = await job_repo.create(job_create)
    
    # 2. Combine job fields for embedding
    full_text = f"{job.title} {job.description} {job.requirements}"
    
    # 3. Generate embedding
    embedding_service = EmbeddingService()
    embedding = await embedding_service.generate_embedding(full_text)
    
    # 4. Store embedding
    await job_repo.update_embedding(job.id, embedding)
```

**Purpose**: Convert job description into a 384-dimensional vector for matching against resumes.

---

### Use Case 3: Job-Resume Matching

**File**: `backend/app/services/matching_engine.py`

**Trigger**: When calculating match scores between jobs and resumes

**Flow**:
```python
class MatchingEngine:
    async def calculate_comprehensive_match(self, job, resume):
        # 1. Get embeddings from database (already generated)
        job_embedding = job.embedding      # 384-dimensional vector
        resume_embedding = resume.embedding  # 384-dimensional vector
        
        # 2. Calculate cosine similarity
        similarity_result = await self._similarity_service.calculate_match_score(
            job_embedding=job_embedding,
            resume_embedding=resume_embedding
        )
        
        # Returns match score (0-100)
        return similarity_result.overall_score
```

**Purpose**: Compare semantic similarity between job and resume vectors to determine match quality.

---

### Use Case 4: Similarity Search

**File**: `backend/app/api/v1/endpoints/matching.py`

**Trigger**: When searching for similar jobs or resumes using text query

**Flow**:
```python
async def similarity_search(...):
    # 1. User provides search query text
    search_query = "Python developer with machine learning experience"
    
    # 2. Generate embedding for query
    embedding_service = EmbeddingService()
    query_embedding = await embedding_service.generate_embedding(search_query)
    
    # 3. Search database using pgvector similarity
    # Finds jobs/resumes with closest embeddings
    similar_jobs = await job_repo.similarity_search(
        query_embedding, 
        limit=10
    )
```

**Purpose**: Enable semantic search - find jobs/resumes that are conceptually similar to a text query.

---

### Use Case 5: Health Checks

**File**: `backend/app/api/v1/endpoints/health.py`

**Trigger**: Health check endpoint (`/api/v1/health/detailed`)

**Flow**:
```python
async def _check_embedding_service_health():
    # Test embedding generation
    test_text = "health check test"
    embedding = await embedding_service.generate_embedding(test_text)
    
    # Returns service status and statistics
```

**Purpose**: Verify the embedding service is working correctly.

---

## How the Model Works

### Step-by-Step Process

#### 1. Text Preprocessing
```python
def _preprocess_text(self, text: str) -> str:
    # Clean text
    text = text.strip()
    text = ' '.join(text.split())  # Remove extra whitespace
    
    # Truncate if too long (8000 char limit)
    if len(text) > 8000:
        text = text[:8000]
    
    return text
```

#### 2. Embedding Generation
```python
async def generate_embedding(self, text: str) -> List[float]:
    # 1. Preprocess
    processed_text = self._preprocess_text(text)
    
    # 2. Check cache (Redis)
    cached = await cache_service.get_cached_embedding(processed_text)
    if cached:
        return cached
    
    # 3. Generate embedding using model
    embedding = await self._model.encode(processed_text)
    
    # 4. Convert to list and cache
    embedding_list = embedding.tolist()  # numpy array -> list
    await cache_service.cache_embedding(processed_text, embedding_list)
    
    return embedding_list  # Returns [float1, float2, ..., float384]
```

#### 3. Storage in Database
```sql
-- PostgreSQL with pgvector extension
CREATE TABLE resumes (
    id UUID PRIMARY KEY,
    content TEXT,
    embedding vector(384)  -- Stores the 384-dimensional vector
);

-- Vector similarity search
SELECT * FROM resumes
ORDER BY embedding <-> query_embedding  -- Cosine distance
LIMIT 10;
```

---

## Performance Optimizations

### 1. Caching (Redis)

- **What**: Embeddings are cached after generation
- **Key Format**: `embedding:{text_hash}`
- **TTL**: 24 hours (default)
- **Benefit**: Avoid re-generating embeddings for the same text

### 2. Batch Processing

```python
async def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
    # Process multiple texts at once
    # More efficient than one-by-one
    batch_embeddings = await self._model.encode(texts)
    return batch_embeddings
```

**Use Case**: When processing multiple resumes or jobs at once.

### 3. Async Execution

```python
# Run in thread pool to avoid blocking
loop = asyncio.get_event_loop()
embedding = await loop.run_in_executor(None, self._model.encode, text)
```

**Benefit**: Non-blocking operation allows handling multiple requests concurrently.

### 4. Circuit Breaker Pattern

```python
@embedding_circuit_breaker
async def generate_embedding(self, text: str) -> List[float]:
    # If service fails repeatedly, circuit opens
    # Returns fallback (zero vector) instead of crashing
```

**Benefit**: Graceful degradation when model fails.

---

## Model Download and Storage

### First Startup

When the application starts for the first time:

1. **Download**: Model is downloaded from HuggingFace Hub (~90 MB)
2. **Cache Location**: `~/.cache/torch/sentence_transformers/`
3. **Time**: 30-60 seconds depending on connection speed

### Subsequent Startups

- **Download**: Not needed (already cached)
- **Load Time**: 2-5 seconds
- **Memory Usage**: ~200 MB RAM

---

## Dependencies

### Required Python Packages

```txt
# From requirements-render.txt
sentence-transformers==3.0.1
torch  # PyTorch (CPU version)
numpy==1.26.4
```

### System Requirements

- **RAM**: Minimum 512 MB (1 GB recommended)
- **Disk Space**: ~500 MB for model and dependencies
- **CPU**: Any modern CPU (GPU not required)

---

## Troubleshooting

### Issue 1: Model Download Fails

**Symptoms**: 
```
Failed to initialize embedding service: Connection timeout
```

**Solutions**:
1. Check internet connection
2. Verify HuggingFace is accessible
3. Pre-download model locally and mount volume

### Issue 2: Out of Memory

**Symptoms**:
```
RuntimeError: Unable to allocate memory
```

**Solutions**:
1. Increase server RAM
2. Use smaller batch sizes
3. Enable swap memory

### Issue 3: Slow Inference

**Symptoms**: Embedding generation takes >5 seconds

**Solutions**:
1. Enable Redis caching
2. Use batch processing for multiple embeddings
3. Consider upgrading to GPU instance (optional)

### Issue 4: Model Not Loading on Render

**Symptoms**:
```
No open ports detected
Failed to initialize services
```

**Solutions**:
1. Model initialization is now non-blocking (recent fix)
2. Check Render logs for specific error
3. Verify `sentence-transformers` is in requirements

---

## API Endpoints Using Embeddings

| Endpoint | Method | Uses Model | Purpose |
|----------|--------|------------|---------|
| `/api/v1/resumes/` | POST | Yes | Generate embedding for new resume |
| `/api/v1/jobs/` | POST | Yes | Generate embedding for new job |
| `/api/v1/matching/calculate` | POST | No* | Compare existing embeddings |
| `/api/v1/matching/similarity-search` | POST | Yes | Generate query embedding |
| `/api/v1/health/detailed` | GET | Yes | Test embedding service |

*Uses embeddings but doesn't generate new ones

---

## Configuration

### Environment Variables

```bash
# Optional: Override default model
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2

# Cache settings
REDIS_URL=redis://localhost:6379/0
```

### Code Configuration

```python
# Change model in embedding_service.py
embedding_service = EmbeddingService(model_name="all-mpnet-base-v2")
# Note: Different models have different dimensions!
```

---

## Alternative Models

If you want to use a different model:

| Model | Dimension | Size | Speed | Accuracy |
|-------|-----------|------|-------|----------|
| all-MiniLM-L6-v2 | 384 | 90 MB | Fast | Good |
| all-mpnet-base-v2 | 768 | 420 MB | Medium | Better |
| paraphrase-multilingual | 384 | 470 MB | Fast | Good (multilingual) |

**To switch**: Update `model_name` in `EmbeddingService.__init__()` and adjust `embedding_dimension` accordingly.

---

## Summary

### The Model is Used For:

1. ✅ **Resume Processing** - Convert resume text to vectors
2. ✅ **Job Processing** - Convert job descriptions to vectors
3. ✅ **Matching** - Calculate similarity between jobs and resumes
4. ✅ **Search** - Find similar jobs/resumes based on text queries
5. ✅ **Health Checks** - Verify service functionality

### Key Benefits:

- 🚀 **Fast**: Processes text in milliseconds
- 💾 **Efficient**: Small model size, low memory usage
- 🎯 **Accurate**: Good semantic understanding
- 🔄 **Cached**: Results cached in Redis for performance
- 🛡️ **Resilient**: Graceful fallback on failures

### Performance Metrics:

- **Single Embedding**: ~50-200ms (without cache)
- **Batch of 10**: ~200-500ms
- **Cache Hit**: ~1-5ms
- **Memory**: ~200 MB per worker
- **Throughput**: ~20-50 embeddings/second

---

## Further Reading

- [Sentence Transformers Documentation](https://www.sbert.net/)
- [all-MiniLM-L6-v2 Model Card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [PostgreSQL pgvector Extension](https://github.com/pgvector/pgvector)
- Backend Architecture: `docs/BACKEND_ARCHITECTURE.md`
- API Reference: `docs/BACKEND_QUICK_REFERENCE.md`

---

**Last Updated**: 2024
**Maintained By**: Resume Job Matching System Team