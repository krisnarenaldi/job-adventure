from fastapi import APIRouter
from app.api.v1.endpoints import files, documents, resume_parsing, explanations, auth, jobs, resumes, matching, analytics, health, database_optimization, interviews, candidate_notes, sharing, companies, contacts

api_router = APIRouter()

# Include API endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["job-management"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["resume-management"])
api_router.include_router(matching.router, prefix="/matching", tags=["matching-ranking"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["interview-scheduling"])
api_router.include_router(candidate_notes.router, prefix="/notes", tags=["candidate-notes"])
api_router.include_router(sharing.router, prefix="/sharing", tags=["candidate-sharing"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(resume_parsing.router, prefix="/resume-parsing", tags=["resume-parsing"])
api_router.include_router(explanations.router, prefix="/explanations", tags=["explanations"])
api_router.include_router(health.router, prefix="/health", tags=["health-monitoring"])
api_router.include_router(database_optimization.router, prefix="/database", tags=["database-optimization"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "Resume Job Matching API v1"}