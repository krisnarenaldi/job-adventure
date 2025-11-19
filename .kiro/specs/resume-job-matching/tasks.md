# Implementation Plan

- [x] 1. Set up project structure and core infrastructure
  - Create backend directory structure with FastAPI application
  - Set up Python virtual environment and requirements.txt with core dependencies
  - Create Docker configuration with docker-compose.yml for PostgreSQL and Redis
  - Initialize basic FastAPI application with health check endpoint
  - Set up environment configuration with .env file structure
  - _Requirements: 7.4, 7.5_

- [x] 2. Configure database and core models
  - [x] 2.1 Set up PostgreSQL with pgvector extension
    - Create docker-compose configuration for PostgreSQL with pgvector
    - Set up database connection using SQLAlchemy with async support
    - Create database initialization script and connection management
    - _Requirements: 7.5_
  
  - [x] 2.2 Implement core data models
    - Define SQLAlchemy models for User, JobDescription, Resume, and MatchResult
    - Create database migration system using Alembic
    - Add proper indexes and constraints for performance
    - _Requirements: 1.5, 7.5_
  
  - [x] 2.3 Create data access layer
    - Implement repository pattern for database operations
    - Add CRUD operations for all core entities
    - Create database session management and connection pooling
    - _Requirements: 1.5, 4.5, 6.5_

- [x] 3. Build document processing service
  - [x] 3.1 Implement file upload handling
    - Create FastAPI endpoints for file upload with validation
    - Add file type validation for PDF and DOCX formats
    - Implement secure file storage with proper access controls
    - _Requirements: 1.1, 1.2, 1.4_
  
  - [x] 3.2 Create document text extraction
    - Implement PDF text extraction using PyPDF2 or pdfminer
    - Add DOCX text extraction using python-docx
    - Create text normalization and cleaning utilities
    - _Requirements: 1.3, 1.4_
  
  - [x] 3.3 Build resume section extraction
    - Implement basic section identification using regex patterns
    - Create structured data extraction for Experience, Skills, Education sections
    - Add error handling for malformed documents
    - _Requirements: 1.3, 5.2_

- [x] 4. Implement AI matching engine
  - [x] 4.1 Set up embedding service
    - Install and configure Sentence Transformers (all-MiniLM-L6-v2)
    - Create embedding generation functions with batch processing
    - Implement embedding storage in PostgreSQL with pgvector
    - _Requirements: 2.4, 7.1_
  
  - [x] 4.2 Build similarity calculation
    - Implement cosine similarity calculation between embeddings
    - Create match score normalization to 0-100% range
    - Add batch processing for multiple resume comparisons
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [x] 4.3 Create skill extraction and matching
    - Implement basic skill extraction using keyword matching and spaCy
    - Build skill comparison algorithm to identify overlaps and gaps
    - Create structured output for matched and missing skills
    - _Requirements: 3.2, 3.3, 5.2_

- [x] 5. Add LLM explanation service
  - [x] 5.1 Set up Anthropic integration
    - Configure Anthropic API client with error handling and rate limiting
    - Create prompt templates for generating match explanations
    - Implement explanation generation with job and resume context
    - _Requirements: 3.1, 3.4, 3.5_
  
  - [x] 5.2 Build explanation formatting
    - Create structured explanation output with strengths and gaps
    - Add fallback template-based explanations for API failures
    - Implement basic caching for explanations
    - _Requirements: 3.1, 3.2, 3.3_

- [x] 6. Create core API endpoints
  - [x] 6.1 Implement basic authentication
    - Create user registration and login endpoints
    - Add JWT token generation and validation
    - Implement basic role-based access control
    - _Requirements: 4.5, 5.5, 6.4_
  
  - [x] 6.2 Build job and resume management APIs
    - Create endpoints for job description upload and storage
    - Implement resume upload and processing endpoints
    - Add endpoints for retrieving job and resume data
    - _Requirements: 1.1, 1.2, 1.5_
  
  - [x] 6.3 Implement matching and ranking APIs
    - Create endpoint for triggering resume-job matching
    - Build candidate ranking API with basic filtering
    - Implement match result retrieval with pagination
    - _Requirements: 2.1, 2.2, 2.5, 6.1, 6.2_

- [x] 7. Build basic analytics service
  - [x] 7.1 Implement core metrics calculation
    - Create functions for applicant counts per job
    - Implement average match score calculations
    - Build basic missing skills analysis
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [x] 7.2 Create analytics API endpoints
    - Build endpoints for recruitment metrics
    - Add basic historical data analysis
    - Implement simple report generation
    - _Requirements: 4.4, 4.5, 6.3_

- [x] 8. Create minimal frontend interface
  - [x] 8.1 Set up Next.js project
    - Initialize Next.js 14 project with TypeScript
    - Configure basic routing and API client
    - Set up Tailwind CSS for styling
    - _Requirements: 1.1, 4.5, 5.4_
  
  - [x] 8.2 Build recruiter interface
    - Create job description upload page
    - Implement resume upload interface with basic file handling
    - Build candidate ranking display with match scores
    - Add basic match result display with explanations
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 3.3_
  
  - [x] 8.3 Create job seeker interface
    - Build resume upload page for job seekers
    - Implement match score display with skill analysis
    - Create basic improvement suggestions display
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 9. Add error handling and basic monitoring
  - [x] 9.1 Implement error handling
    - Add comprehensive error handling for file processing
    - Implement retry logic for AI service calls
    - Create graceful degradation for service failures
    - _Requirements: 1.4, 2.5, 3.4_
  
  - [x] 9.2 Set up basic logging
    - Implement structured logging throughout the application
    - Add basic performance monitoring
    - Create health check endpoints
    - _Requirements: 7.2, 7.4_

- [x] 10. Performance optimization
  - [x] 10.1 Add Redis caching
    - Set up Redis for embedding caching
    - Implement session management with Redis
    - Add basic API response caching
    - _Requirements: 2.3, 7.1, 7.3_
  
  - [x] 10.2 Database optimization
    - Add proper database indexes for performance
    - Implement connection pooling optimization
    - Create query optimization for large datasets
    - _Requirements: 7.1, 7.2, 7.5_

- [ ]* 11. Testing and validation
  - [ ]* 11.1 Write core unit tests
    - Create unit tests for document processing functions
    - Write tests for embedding generation and similarity calculation
    - Add tests for skill extraction algorithms
    - _Requirements: 1.3, 2.1, 3.2_
  
  - [ ]* 11.2 Add integration tests
    - Create API endpoint integration tests
    - Write database integration tests
    - Add file upload and processing integration tests
    - _Requirements: 1.1, 1.2, 2.1_


- [x] 12. Implement candidate status management
  - [x] 12.1 Add status field to match results
    - Add status column to match_results table (shortlisted, rejected, maybe, pending)
    - Create database migration for status field
    - Add status update timestamp field
    - _Requirements: 2.1, 6.1_
  
  - [x] 12.2 Create status update API
    - Implement PATCH /api/v1/matching/results/{match_id}/status endpoint
    - Add validation for status values
    - Create status history tracking
    - _Requirements: 2.1, 6.1_
  
  - [x] 12.3 Build status management UI
    - Add status dropdown/buttons to candidate cards
    - Implement status badge display with colors
    - Add status filter in candidate list
    - Create bulk status update functionality
    - _Requirements: 2.1, 6.1_

- [x] 13. Add job description active/inactive toggle
  - [x] 13.1 Add is_active field to jobs
    - Add is_active boolean column to job_descriptions table
    - Create database migration
    - Set default value to true for existing jobs
    - _Requirements: 1.1, 6.1_
  
  - [x] 13.2 Create job status API
    - Implement PATCH /api/v1/jobs/{job_id}/status endpoint
    - Add logic to prevent matching on inactive jobs
    - Create job archival functionality
    - _Requirements: 1.1, 6.1_
  
  - [x] 13.3 Build job status UI
    - Add active/inactive toggle in job list
    - Display status badge on job cards
    - Add filter for active/inactive jobs
    - Show warning when trying to upload resume to inactive job
    - _Requirements: 1.1, 6.1_

- [x] 14. Implement interview scheduling system
  - [x] 14.1 Create interview data model
    - Add interviews table with fields (candidate_id, job_id, scheduled_time, status, meeting_link)
    - Create database migration
    - Add interview_type field (phone, video, in-person)
    - _Requirements: 2.1, 6.1_
  
  - [x] 14.2 Build interview scheduling API
    - Create POST /api/v1/interviews endpoint
    - Implement GET /api/v1/interviews/job/{job_id} endpoint
    - Add PATCH /api/v1/interviews/{interview_id} for updates
    - Create DELETE endpoint for cancellations
    - _Requirements: 2.1, 6.1_
  
  - [x] 14.3 Integrate email service
    - Set up email service (SendGrid, AWS SES, or SMTP)
    - Create email templates for interview invitations
    - Implement send invitation email function
    - Add email tracking (sent, opened, clicked)
    - _Requirements: 6.1, 6.4_
  
  - [x] 14.4 Create interview scheduling UI
    - Add "Schedule Interview" button on candidate detail modal
    - Build interview scheduling form (date, time, type, notes)
    - Implement calendar view for scheduled interviews
    - Add interview status tracking (scheduled, completed, cancelled)
    - Create email preview before sending
    - _Requirements: 2.1, 6.1_

- [x] 15. Add notes and comments system
  - [x] 15.1 Create notes data model
    - Add candidate_notes table with fields (match_id, user_id, note_text, created_at)
    - Create database migration
    - Add is_private field for note visibility
    - _Requirements: 6.1, 6.4_
  
  - [x] 15.2 Build notes API
    - Create POST /api/v1/matching/results/{match_id}/notes endpoint
    - Implement GET endpoint to retrieve notes
    - Add PATCH endpoint for note updates
    - Create DELETE endpoint for note removal
    - _Requirements: 6.1, 6.4_
  
  - [x] 15.3 Implement notes UI
    - Add notes section in candidate detail modal
    - Create note input with rich text editor
    - Display notes list with timestamps and author
    - Add edit and delete buttons for own notes
    - Implement note filtering and search
    - _Requirements: 6.1, 6.4_

- [x] 16. Build export and sharing functionality
  - [x] 16.1 Implement candidate export API
    - Create GET /api/v1/jobs/{job_id}/candidates/export endpoint
    - Add support for CSV format export
    - Add support for Excel (XLSX) format export
    - Include match scores, status, skills, and contact info
    - Add filtering options for export (by status, score range)
    - _Requirements: 6.3, 6.4_
  
  - [x] 16.2 Create export UI
    - Add "Export Candidates" button on candidates page
    - Build export options modal (format, filters, fields)
    - Implement download functionality
    - Add export history tracking
    - _Requirements: 6.3, 6.4_
  
  - [x] 16.3 Add sharing functionality
    - Create shareable link generation for job candidates
    - Implement access control for shared links (view-only, time-limited)
    - Add email sharing with custom message
    - Create shared view page for hiring managers
    - _Requirements: 6.4_

- [x] 17. Create candidate manager dashboard
  - [x] 17.1 Build candidate manager API
    - Create GET /api/v1/candidates/all endpoint with pagination
    - Add filtering by status, job, date range, match score
    - Implement search by candidate name or email
    - Add sorting options (by date, score, status)
    - _Requirements: 6.1, 6.2, 6.3_
  
  - [x] 17.2 Create candidate manager UI
    - Build new page at /recruiter/candidates
    - Implement data table with all candidates across jobs
    - Add columns: name, email, job title, status, match score, date
    - Create status filter chips (All, Shortlisted, Rejected, Maybe, Pending)
    - Add search bar for candidate filtering
    - Implement pagination controls
    - _Requirements: 6.1, 6.2, 6.3_
  
  - [x] 17.3 Add bulk operations
    - Implement checkbox selection for multiple candidates
    - Add bulk status update functionality
    - Create bulk export button
    - Add bulk delete option with confirmation
    - _Requirements: 6.1, 6.3_
  
  - [x] 17.4 Implement export from candidate manager
    - Add "Export to Excel" button
    - Add "Export to CSV" button
    - Include all visible columns in export
    - Respect current filters in export
    - Add export progress indicator
    - _Requirements: 6.3_

- [x] 18. Add navigation and routing
  - [x] 18.1 Update navigation menu
    - Add "Candidate Manager" link to main navigation
    - Add "Interviews" link to navigation
    - Update breadcrumbs for new pages
    - _Requirements: 6.1_
  
  - [x] 18.2 Create new routes
    - Add /recruiter/candidates route for candidate manager
    - Add /recruiter/interviews route for interview calendar
    - Update routing configuration
    - _Requirements: 6.1_
