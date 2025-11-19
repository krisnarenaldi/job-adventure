# Team Collaboration Setup - Quick Guide

## What Was Implemented

We've implemented **Option 1: Simple Team Collaboration** using the existing `company_id` field.

## Changes Made

### Backend Changes

1. **Created Company Model** (`backend/app/models/company.py`)
   - Simple table with `id` and `name`
   - Linked to users via foreign key

2. **Database Migration** (`backend/alembic/versions/007_add_companies_table.py`)
   - Created `companies` table
   - Added foreign key constraint from `users.company_id` to `companies.id`
   - Run with: `alembic upgrade head` ✅ (Already completed)

3. **Updated User Model** (`backend/app/models/user.py`)
   - Added ForeignKey constraint to `company_id`

4. **Created Company Repository** (`backend/app/repositories/company.py`)
   - Methods to create and retrieve companies

5. **Updated Auth Endpoint** (`backend/app/api/v1/endpoints/auth.py`)
   - Registration now accepts `company_name`
   - Auto-creates company if it doesn't exist
   - Assigns user to company

6. **Updated Auth Schema** (`backend/app/schemas/auth.py`)
   - Changed `company_id` to `company_name` in UserCreate

7. **Updated Job Repository** (`backend/app/repositories/job.py`)
   - Added `get_by_company_id()` method to fetch jobs for all team members

8. **Updated Jobs Endpoint** (`backend/app/api/v1/endpoints/jobs.py`)
   - Modified `list_jobs()` to show company jobs when user has `company_id`
   - Falls back to user-only jobs if no company

### Frontend Changes

1. **Updated Registration Form** (`frontend/src/app/auth/register/page.tsx`)
   - Added "Company Name" input field
   - Added helper text explaining team collaboration

2. **Updated API Client** (`frontend/src/lib/api.ts`)
   - Modified `register()` to accept `company_name` parameter

## How It Works

### For New Users
1. User registers with email, password, name, and **company name**
2. System checks if company exists:
   - If exists: User joins that company
   - If new: System creates company and assigns user to it
3. User can now see jobs from all team members in the same company

### For Existing Users
- Users without `company_id` (NULL) will only see their own jobs
- To enable collaboration, they need to re-register or manually update their `company_id` in the database

### Team Collaboration Features

**What Works Now:**
- ✅ Multiple users can register with the same company name
- ✅ All team members see all jobs posted by anyone in their company
- ✅ Notes system already supports private/public notes
  - Public notes: Visible to all team members
  - Private notes: Only visible to the author
- ✅ All team members can view candidates for company jobs
- ✅ All team members can add notes, schedule interviews, update statuses

**What's Visible:**
- Job listings: All jobs from your company
- Candidates: All candidates for company jobs
- Notes: Public notes from all team members + your private notes
- Interviews: All interviews scheduled by team members

## Testing Team Collaboration

### Test Scenario 1: Same Company
1. Register User A with company "Acme Corp"
2. Register User B with company "Acme Corp"
3. User A creates a job
4. User B should see User A's job in their job list
5. Both can add candidates, notes, and schedule interviews

### Test Scenario 2: Different Companies
1. Register User C with company "Tech Inc"
2. User C should NOT see jobs from "Acme Corp"
3. User C only sees jobs from "Tech Inc" team members

### Test Scenario 3: No Company
1. Existing users with NULL company_id
2. They only see their own jobs (backward compatible)

## Database Query to Check

```sql
-- See all companies
SELECT * FROM companies;

-- See users and their companies
SELECT u.id, u.email, u.full_name, c.name as company_name
FROM users u
LEFT JOIN companies c ON u.company_id = c.id;

-- See jobs by company
SELECT j.id, j.title, u.full_name as creator, c.name as company
FROM job_descriptions j
JOIN users u ON j.created_by = u.id
LEFT JOIN companies c ON u.company_id = c.id;
```

## Future Enhancements (Not Implemented)

- Team member invitation system
- Role-based permissions within company
- Company settings/preferences
- Activity feed showing team actions
- Company admin dashboard
- Remove team members
- Transfer job ownership

## Notes

- The private note checkbox now makes sense for team collaboration
- Existing users need to update their company_id to join a team
- Company names are case-sensitive (can be changed to case-insensitive)
