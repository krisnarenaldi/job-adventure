# Design Document

## Overview

The Job Analytics Dashboard is a comprehensive data visualization system that provides recruiters with actionable insights about their candidate pools. The system aggregates data from resumes, match results, and job descriptions to generate interactive charts and metrics. The architecture follows a modular approach with dedicated analytics services, caching layers, and a responsive frontend built with React and Chart.js.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Dashboard    │  │ Chart        │  │ Filter       │     │
│  │ Container    │  │ Components   │  │ Controls     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Analytics    │  │ Aggregation  │  │ Cache        │     │
│  │ Endpoints    │  │ Service      │  │ Layer        │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ PostgreSQL   │  │ Redis Cache  │  │ Analytics    │     │
│  │ Database     │  │              │  │ Repository   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **User Request**: Recruiter accesses dashboard for a specific job
2. **API Call**: Frontend requests analytics data from backend
3. **Cache Check**: Backend checks Redis for cached analytics
4. **Data Aggregation**: If not cached, aggregate data from PostgreSQL
5. **Computation**: Calculate metrics, distributions, and trends
6. **Cache Store**: Store computed results in Redis (TTL: 5 minutes)
7. **Response**: Return JSON data to frontend
8. **Visualization**: Frontend renders charts using Chart.js/Recharts

## Components and Interfaces

### Backend Components

#### 1. Analytics Service (`analytics_service.py`)

**Purpose**: Core service for computing analytics metrics and aggregations

**Key Methods**:
```python
class AnalyticsService:
    async def get_skills_distribution(
        self, 
        job_id: UUID, 
        limit: int = 10
    ) -> SkillsDistribution
    
    async def get_match_score_distribution(
        self, 
        job_id: UUID
    ) -> MatchScoreDistribution
    
    async def get_location_distribution(
        self, 
        job_id: UUID, 
        limit: int = 10
    ) -> LocationDistribution
    
    async def get_experience_distribution(
        self, 
        job_id: UUID
    ) -> ExperienceDistribution
    
    async def get_missing_skills_analysis(
        self, 
        job_id: UUID, 
        limit: int = 10
    ) -> MissingSkillsAnalysis
    
    async def get_application_trends(
        self, 
        job_id: UUID, 
        days: int = 30
    ) -> ApplicationTrends
    
    async def get_skill_coverage(
        self, 
        job_id: UUID
    ) -> SkillCoverage
    
    async def compare_jobs(
        self, 
        job_ids: List[UUID]
    ) -> JobComparison
```

#### 2. Analytics Repository (`analytics_repository.py`)

**Purpose**: Optimized database queries for analytics data

**Key Methods**:
```python
class AnalyticsRepository:
    async def get_candidate_skills_aggregation(
        self, 
        job_id: UUID
    ) -> List[SkillCount]
    
    async def get_match_scores_by_range(
        self, 
        job_id: UUID
    ) -> Dict[str, int]
    
    async def get_candidates_by_location(
        self, 
        job_id: UUID
    ) -> List[LocationCount]
    
    async def get_applications_by_date(
        self, 
        job_id: UUID, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[DateCount]
```

#### 3. Analytics Endpoints (`/api/v1/analytics/`)

**Routes**:
- `GET /analytics/jobs/{job_id}/skills-distribution`
- `GET /analytics/jobs/{job_id}/match-distribution`
- `GET /analytics/jobs/{job_id}/demographics`
- `GET /analytics/jobs/{job_id}/missing-skills`
- `GET /analytics/jobs/{job_id}/trends`
- `GET /analytics/jobs/{job_id}/skill-coverage`
- `POST /analytics/jobs/compare`
- `GET /analytics/jobs/{job_id}/export`

### Frontend Components

#### 1. Dashboard Container (`DashboardPage.tsx`)

**Purpose**: Main container managing dashboard state and layout

**Responsibilities**:
- Fetch analytics data from API
- Manage filter state
- Coordinate updates across widgets
- Handle real-time data refresh

#### 2. Chart Components

**SkillsDistributionChart.tsx**
- Bar chart showing top skills
- Interactive tooltips with percentages
- Color coding for required vs additional skills

**MatchScoreHistogram.tsx**
- Histogram with 5 bins (0-20%, 20-40%, etc.)
- Average score indicator line
- Click-through to candidate list

**LocationChart.tsx**
- Horizontal bar chart for locations
- Optional map view toggle
- Remote work indicator

**ExperiencePieChart.tsx**
- Pie chart with 4 segments
- Interactive legend
- Click to filter candidates

**MissingSkillsChart.tsx**
- Bar chart showing skill gaps
- Priority indicators
- Recommendations panel

**TrendsLineChart.tsx**
- Multi-line chart for time series
- Date range selector
- Zoom and pan controls

**SkillCoverageRadar.tsx**
- Radar/spider chart
- Coverage percentage per skill
- Threshold indicators

**JobComparisonChart.tsx**
- Grouped bar chart
- Multiple metrics comparison
- Job selector dropdown

#### 3. Filter Controls (`FilterPanel.tsx`)

**Features**:
- Date range picker
- Match score range slider
- Location multi-select
- Experience level checkboxes
- Save/load filter presets
- Clear all button

## Data Models

### Analytics Response Models

```python
class SkillDistributionItem(BaseModel):
    skill_name: str
    candidate_count: int
    percentage: float
    is_required: bool
    avg_proficiency: Optional[float]

class SkillsDistribution(BaseModel):
    job_id: UUID
    total_candidates: int
    skills: List[SkillDistributionItem]
    generated_at: datetime

class MatchScoreBin(BaseModel):
    range_label: str  # "0-20%", "20-40%", etc.
    min_score: float
    max_score: float
    candidate_count: int
    percentage: float

class MatchScoreDistribution(BaseModel):
    job_id: UUID
    bins: List[MatchScoreBin]
    average_score: float
    median_score: float
    total_candidates: int

class LocationItem(BaseModel):
    location: str
    candidate_count: int
    percentage: float
    remote_count: int

class LocationDistribution(BaseModel):
    job_id: UUID
    locations: List[LocationItem]
    total_candidates: int

class ExperienceLevel(BaseModel):
    level: str  # "Junior", "Mid-level", "Senior", "Expert"
    years_range: str  # "0-2", "3-5", "6-10", "10+"
    candidate_count: int
    percentage: float

class ExperienceDistribution(BaseModel):
    job_id: UUID
    levels: List[ExperienceLevel]
    total_candidates: int

class MissingSkillItem(BaseModel):
    skill_name: str
    missing_count: int
    percentage: float
    priority: str  # "High", "Medium", "Low"

class MissingSkillsAnalysis(BaseModel):
    job_id: UUID
    missing_skills: List[MissingSkillItem]
    total_candidates: int

class TrendDataPoint(BaseModel):
    date: date
    application_count: int
    average_match_score: Optional[float]

class ApplicationTrends(BaseModel):
    job_id: UUID
    data_points: List[TrendDataPoint]
    avg_applications_per_day: float
    peak_day: date
    peak_count: int

class SkillCoverageItem(BaseModel):
    skill_name: str
    coverage_percentage: float
    candidate_count: int

class SkillCoverage(BaseModel):
    job_id: UUID
    overall_coverage: float
    skills: List[SkillCoverageItem]
    critical_gaps: List[str]

class JobComparisonMetrics(BaseModel):
    job_id: UUID
    job_title: str
    total_candidates: int
    average_match_score: float
    top_skills: List[str]
    time_to_fill_days: Optional[int]

class JobComparison(BaseModel):
    jobs: List[JobComparisonMetrics]
    comparison_date: datetime
```

## Error Handling

### Error Scenarios

1. **No Candidates Available**
   - Return empty datasets with appropriate messages
   - Display "No data available" state in UI
   - Suggest actions (upload resumes, run matching)

2. **Insufficient Data**
   - Minimum 3 candidates required for meaningful analytics
   - Display warning message
   - Show partial data with disclaimer

3. **Cache Failures**
   - Gracefully fall back to direct database queries
   - Log cache errors for monitoring
   - Continue serving requests

4. **Database Query Timeouts**
   - Implement query timeouts (30 seconds)
   - Return partial results if available
   - Display error message to user

5. **Invalid Date Ranges**
   - Validate date ranges on backend
   - Return 400 Bad Request with clear message
   - Frontend validates before sending

## Testing Strategy

### Unit Tests

1. **Analytics Service Tests**
   - Test each aggregation method with mock data
   - Verify calculations (percentages, averages, distributions)
   - Test edge cases (empty data, single candidate, etc.)

2. **Repository Tests**
   - Test SQL queries with test database
   - Verify correct data aggregation
   - Test query performance with large datasets

3. **API Endpoint Tests**
   - Test request/response formats
   - Verify authentication and authorization
   - Test error handling and validation

### Integration Tests

1. **End-to-End Analytics Flow**
   - Create test job and candidates
   - Request analytics data
   - Verify correct calculations
   - Test caching behavior

2. **Real-time Update Tests**
   - Add new candidate
   - Verify analytics update
   - Test cache invalidation

3. **Export Functionality Tests**
   - Test CSV export format
   - Test PDF generation
   - Verify data accuracy in exports

### Performance Tests

1. **Load Testing**
   - Test with 1000+ candidates per job
   - Measure response times
   - Verify cache effectiveness

2. **Concurrent Request Testing**
   - Multiple users accessing dashboard
   - Verify no data corruption
   - Test cache hit rates

## Performance Optimization

### Caching Strategy

1. **Redis Cache Layers**
   - **L1**: Individual analytics queries (TTL: 5 minutes)
   - **L2**: Aggregated dashboard data (TTL: 10 minutes)
   - Cache invalidation on new candidate or match result

2. **Database Optimization**
   - Create materialized views for common aggregations
   - Add indexes on frequently queried columns
   - Use database-level aggregation functions

3. **Query Optimization**
   - Use CTEs for complex queries
   - Implement pagination for large result sets
   - Batch queries where possible

### Frontend Optimization

1. **Lazy Loading**
   - Load charts on-demand as user scrolls
   - Defer non-critical visualizations

2. **Data Streaming**
   - Stream large datasets incrementally
   - Update charts progressively

3. **Memoization**
   - Cache computed chart data
   - Prevent unnecessary re-renders

## Security Considerations

1. **Authorization**
   - Only job owner or admin can view analytics
   - Verify job access before returning data

2. **Data Privacy**
   - Aggregate data only, no PII in analytics
   - Anonymize location data if needed
   - Respect candidate privacy settings

3. **Rate Limiting**
   - Limit analytics API calls per user
   - Prevent abuse of export functionality

## Deployment Considerations

1. **Database Migrations**
   - Add indexes for analytics queries
   - Create materialized views if needed

2. **Cache Warming**
   - Pre-compute analytics for active jobs
   - Background job to refresh cache

3. **Monitoring**
   - Track analytics query performance
   - Monitor cache hit rates
   - Alert on slow queries

## Future Enhancements

1. **Advanced Filtering**
   - Custom filter combinations
   - Saved filter templates
   - Filter sharing between users

2. **Predictive Analytics**
   - Predict time-to-fill
   - Forecast application trends
   - Recommend optimal posting times

3. **Custom Dashboards**
   - User-configurable layouts
   - Widget customization
   - Personal dashboard templates

4. **Automated Insights**
   - AI-generated insights and recommendations
   - Anomaly detection
   - Trend alerts
