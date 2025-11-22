# Embedding Model Flow Diagram

## Visual Overview of all-MiniLM-L6-v2 Usage

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION STARTUP                                  │
│                                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐             │
│  │  main.py     │─────→│  Initialize  │─────→│  Download    │             │
│  │  starts      │      │  Embedding   │      │  Model from  │             │
│  │  FastAPI     │      │  Service     │      │  HuggingFace │             │
│  └──────────────┘      └──────────────┘      └──────────────┘             │
│                               │                      │                      │
│                               │                      ↓                      │
│                               │            (~90 MB, first time only)       │
│                               │                      │                      │
│                               ↓                      ↓                      │
│                        ┌────────────────────────────────┐                  │
│                        │  all-MiniLM-L6-v2 Model        │                  │
│                        │  Loaded into Memory (~200 MB)  │                  │
│                        └────────────────────────────────┘                  │
│                                      │                                      │
│                                      ↓                                      │
│                        [ Ready to Process Requests ]                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Flow 1: Resume Upload & Embedding Generation

```
┌────────────┐
│  User      │
│  Uploads   │
│  Resume    │
│  (PDF)     │
└─────┬──────┘
      │
      ↓
┌─────────────────────────────────────────────────────────────────┐
│  POST /api/v1/resumes/                                          │
│  ────────────────────────────────────────────────────────────   │
│                                                                  │
│  1. Parse PDF/DOCX                                              │
│     ┌──────────────────┐                                        │
│     │ DocumentProcessor │                                       │
│     └────────┬───────────┘                                      │
│              ↓                                                   │
│     "John Doe, Software Engineer with 5 years..."              │
│                                                                  │
│  2. Extract Skills & Info                                       │
│     ┌──────────────────┐                                        │
│     │  ResumeParser    │                                        │
│     └────────┬───────────┘                                      │
│              ↓                                                   │
│     {name: "John", skills: ["Python", "ML"], ...}              │
│                                                                  │
│  3. Generate Embedding                                          │
│     ┌──────────────────────────────────────┐                   │
│     │  EmbeddingService                    │                   │
│     │  ────────────────                     │                   │
│     │  - Preprocess text                    │                   │
│     │  - Check Redis cache                  │                   │
│     │  - all-MiniLM-L6-v2.encode()         │                   │
│     │  - Returns 384-dim vector             │                   │
│     └────────┬─────────────────────────────┘                   │
│              ↓                                                   │
│     [0.123, -0.456, 0.789, ..., 0.321]  (384 floats)          │
│                                                                  │
│  4. Store in Database                                           │
│     ┌────────────────────┐                                      │
│     │  PostgreSQL        │                                      │
│     │  with pgvector     │                                      │
│     └────────┬───────────┘                                      │
│              ↓                                                   │
│     INSERT INTO resumes (id, content, embedding)               │
│     VALUES (..., ..., vector[384])                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
      │
      ↓
┌────────────┐
│  Resume    │
│  Stored    │
│  ✓         │
└────────────┘
```

---

## Flow 2: Job Posting & Embedding Generation

```
┌────────────┐
│ Recruiter  │
│ Posts Job  │
│ Opening    │
└─────┬──────┘
      │
      ↓
┌─────────────────────────────────────────────────────────────────┐
│  POST /api/v1/jobs/                                             │
│  ────────────────────────────────────────────────────────────   │
│                                                                  │
│  1. Receive Job Data                                            │
│     {                                                            │
│       title: "Senior Python Developer",                         │
│       description: "Build ML systems...",                       │
│       requirements: "5+ years Python, ML experience..."         │
│     }                                                            │
│                                                                  │
│  2. Combine Fields                                              │
│     full_text = title + description + requirements             │
│     ↓                                                            │
│     "Senior Python Developer Build ML systems... 5+ years..."  │
│                                                                  │
│  3. Generate Embedding                                          │
│     ┌──────────────────────────────────────┐                   │
│     │  EmbeddingService                    │                   │
│     │  ────────────────                     │                   │
│     │  - Check cache (Redis)                │                   │
│     │  - all-MiniLM-L6-v2.encode()         │                   │
│     └────────┬─────────────────────────────┘                   │
│              ↓                                                   │
│     [0.234, 0.567, -0.123, ..., 0.456]  (384 floats)          │
│                                                                  │
│  4. Store Job & Embedding                                       │
│     ┌────────────────────┐                                      │
│     │  PostgreSQL        │                                      │
│     └────────┬───────────┘                                      │
│              ↓                                                   │
│     INSERT INTO jobs (id, title, description, embedding)       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
      │
      ↓
┌────────────┐
│  Job       │
│  Posted    │
│  ✓         │
└────────────┘
```

---

## Flow 3: Job-Resume Matching

```
┌────────────┐
│ Recruiter  │
│ Searches   │
│ Candidates │
└─────┬──────┘
      │
      ↓
┌─────────────────────────────────────────────────────────────────────┐
│  POST /api/v1/matching/calculate                                    │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  1. Get Job & Resume from Database                                  │
│     ┌──────────────────────────────────────────┐                   │
│     │  Job (ID: 123)                           │                   │
│     │  embedding: [0.234, 0.567, ..., 0.456]  │  Already stored!  │
│     └──────────────────────────────────────────┘                   │
│                                                                      │
│     ┌──────────────────────────────────────────┐                   │
│     │  Resume (ID: 456)                        │                   │
│     │  embedding: [0.123, -0.456, ..., 0.321] │  Already stored!  │
│     └──────────────────────────────────────────┘                   │
│                                                                      │
│  2. Calculate Similarity (No Model Needed!)                         │
│     ┌─────────────────────────────────────────┐                    │
│     │  SimilarityService                      │                    │
│     │  ──────────────────                      │                    │
│     │  cosine_similarity(job_emb, resume_emb) │                    │
│     │                                          │                    │
│     │  Formula:                                │                    │
│     │  similarity = dot(v1, v2) /              │                    │
│     │               (norm(v1) * norm(v2))      │                    │
│     └─────────────┬───────────────────────────┘                    │
│                   ↓                                                  │
│            Score: 0.85 (85%)                                        │
│                                                                      │
│  3. Extract & Match Skills                                          │
│     ┌─────────────────────────────────────────┐                    │
│     │  SkillExtractionService                 │                    │
│     │  Compare: ["Python", "ML", "Docker"]    │                    │
│     │  With:    ["Python", "ML", "AWS"]       │                    │
│     │  Match: 66%                              │                    │
│     └─────────────┬───────────────────────────┘                    │
│                   ↓                                                  │
│            Skill Match: 66%                                         │
│                                                                      │
│  4. Generate Explanation (Optional)                                 │
│     ┌─────────────────────────────────────────┐                    │
│     │  ExplanationService (OpenAI GPT-4)      │                    │
│     │  "Strong match because..."               │                    │
│     └─────────────────────────────────────────┘                    │
│                                                                      │
│  5. Combine Scores                                                  │
│     Overall Match = 0.6 * semantic_similarity +                    │
│                     0.3 * skill_match +                             │
│                     0.1 * other_factors                             │
│     ↓                                                                │
│     Final Score: 78%                                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
      │
      ↓
┌────────────┐
│  Results   │
│  Displayed │
│  to User   │
└────────────┘
```

---

## Flow 4: Semantic Search

```
┌────────────┐
│  User      │
│  Searches  │
│  "ML jobs" │
└─────┬──────┘
      │
      ↓
┌─────────────────────────────────────────────────────────────────────┐
│  POST /api/v1/matching/similarity-search                            │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  1. Receive Search Query                                            │
│     query: "Machine learning engineer with Python experience"      │
│                                                                      │
│  2. Generate Query Embedding                                        │
│     ┌──────────────────────────────────────┐                       │
│     │  EmbeddingService                    │                       │
│     │  ────────────────                     │                       │
│     │  all-MiniLM-L6-v2.encode(query)      │                       │
│     └────────┬─────────────────────────────┘                       │
│              ↓                                                       │
│     [0.345, -0.234, 0.678, ..., 0.123]  (384 floats)              │
│                                                                      │
│  3. Vector Similarity Search in Database                            │
│     ┌────────────────────────────────────────────┐                 │
│     │  PostgreSQL with pgvector                  │                 │
│     │  ────────────────────────────────────       │                 │
│     │  SELECT * FROM jobs                        │                 │
│     │  ORDER BY embedding <-> query_embedding    │                 │
│     │  LIMIT 10;                                  │                 │
│     │                                             │                 │
│     │  <-> is cosine distance operator            │                 │
│     └────────┬───────────────────────────────────┘                 │
│              ↓                                                       │
│     ┌──────────────────────────────────┐                           │
│     │ Top 10 Most Similar Jobs         │                           │
│     │ ──────────────────────────────    │                           │
│     │ 1. "ML Engineer" (95% match)     │                           │
│     │ 2. "Python Developer" (88%)      │                           │
│     │ 3. "Data Scientist" (85%)        │                           │
│     │ ...                               │                           │
│     └──────────────────────────────────┘                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
      │
      ↓
┌────────────┐
│  Results   │
│  Returned  │
│  to User   │
└────────────┘
```

---

## Caching Layer

```
┌──────────────────────────────────────────────────────────────┐
│                    REDIS CACHE                               │
│  ──────────────────────────────────────────────────────────  │
│                                                               │
│  When generating embedding:                                  │
│                                                               │
│  1. Hash the input text                                      │
│     text_hash = sha256("Software Engineer with...")          │
│     ↓                                                         │
│     "a3f5b2c8d9e1..."                                        │
│                                                               │
│  2. Check Redis                                              │
│     key = "embedding:a3f5b2c8d9e1..."                       │
│                                                               │
│     ┌─────────┐                                              │
│     │ CACHED? │                                              │
│     └────┬────┘                                              │
│          │                                                    │
│     YES  │  NO                                               │
│    ┌─────┴─────┐                                             │
│    │           │                                             │
│    ↓           ↓                                             │
│  Return     Generate                                         │
│  cached     new embedding                                    │
│  (1-5ms)    (50-200ms)                                      │
│             │                                                 │
│             ↓                                                 │
│          Store in                                            │
│          Redis                                               │
│          TTL: 24h                                            │
│                                                               │
│  Cache Hit Rate: ~70-80% in production                       │
│  Benefit: 40-100x faster response time                       │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Error Handling & Fallback

```
┌──────────────────────────────────────────────────────────────┐
│              CIRCUIT BREAKER PATTERN                         │
│  ──────────────────────────────────────────────────────────  │
│                                                               │
│  Normal Operation:                                           │
│  ┌────────────┐                                              │
│  │  Request   │─────→ Generate Embedding ────→ Return       │
│  └────────────┘                                              │
│                                                               │
│  When Model Fails (3 times in 60 seconds):                  │
│  ┌────────────┐                                              │
│  │  Request   │─────→ ⚠️  Circuit OPEN  ⚠️                  │
│  └────────────┘           │                                  │
│                           ↓                                  │
│                    Return Fallback:                          │
│                    [0, 0, 0, ..., 0]                        │
│                    (zero vector)                             │
│                           │                                  │
│                           ↓                                  │
│                    System stays online!                      │
│                    (degraded mode)                           │
│                                                               │
│  After 60 seconds:                                           │
│  Circuit → HALF-OPEN → Test → CLOSED (if successful)        │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Performance Metrics

```
┌────────────────────────────────────────────────────────────────┐
│                    TIMING BREAKDOWN                            │
│  ────────────────────────────────────────────────────────────  │
│                                                                 │
│  Single Embedding Generation:                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                               │
│                                                                 │
│  WITH CACHE (70% of requests):                                 │
│  ├─ Redis lookup:        1-5ms                                 │
│  ├─ Deserialization:     <1ms                                  │
│  └─ Total:               ~2-6ms ✓                              │
│                                                                 │
│  WITHOUT CACHE (30% of requests):                              │
│  ├─ Text preprocessing:  1-2ms                                 │
│  ├─ Model inference:     50-150ms                              │
│  ├─ Cache storage:       2-5ms                                 │
│  └─ Total:               ~53-157ms                             │
│                                                                 │
│  Batch Processing (10 texts):                                  │
│  ├─ Model inference:     200-400ms                             │
│  └─ Per text:            ~20-40ms ✓ (2-5x faster!)            │
│                                                                 │
│  ────────────────────────────────────────────────────────────  │
│                                                                 │
│  Memory Usage:                                                  │
│  ━━━━━━━━━━━━━━                                               │
│  ├─ Model in RAM:        ~200 MB                               │
│  ├─ Per request:         ~10-20 MB                             │
│  └─ Total (1 worker):    ~220-250 MB                           │
│                                                                 │
│  ────────────────────────────────────────────────────────────  │
│                                                                 │
│  Throughput (single worker):                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━                                     │
│  ├─ With cache:          ~500 embeddings/sec                   │
│  ├─ Without cache:       ~20-50 embeddings/sec                 │
│  └─ Mixed (typical):     ~100-200 embeddings/sec               │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Summary

```
                    ┌─────────────────┐
                    │  User Actions   │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ↓                 ↓                 ↓
    ┌──────────┐      ┌──────────┐     ┌──────────┐
    │ Upload   │      │  Create  │     │ Search & │
    │ Resume   │      │   Job    │     │  Match   │
    └────┬─────┘      └────┬─────┘     └────┬─────┘
         │                 │                 │
         ↓                 ↓                 ↓
    ┌──────────────────────────────────────────┐
    │      all-MiniLM-L6-v2 Model             │
    │      (Embedding Generation)              │
    └──────────────┬───────────────────────────┘
                   │
                   ↓
         [0.123, -0.456, ..., 0.789]
                384 floats
                   │
         ┌─────────┴─────────┐
         ↓                   ↓
    ┌─────────┐         ┌─────────┐
    │  Redis  │         │  Postgres│
    │  Cache  │         │  pgvector│
    │  24h    │         │  Permanent
    └─────────┘         └─────────┘
                             │
                             ↓
                    ┌────────────────┐
                    │  Match Results │
                    │  & Search      │
                    └────────────────┘
```

---

## Key Takeaways

1. **Model loads once at startup** - stays in memory
2. **Embeddings generated only when needed** - for new content
3. **Cached in Redis** - subsequent requests are fast
4. **Stored in PostgreSQL** - permanent storage with pgvector
5. **Matching uses stored embeddings** - no re-generation needed
6. **Semantic search powered by vector similarity** - PostgreSQL pgvector
7. **Graceful degradation** - circuit breaker prevents cascading failures
8. **Batch processing available** - for bulk operations

---

**Model**: `all-MiniLM-L6-v2`  
**Output**: 384-dimensional vectors  
**Speed**: 50-200ms per embedding (uncached), 2-6ms (cached)  
**Memory**: ~200 MB  
**Accuracy**: Good balance of speed and quality  
