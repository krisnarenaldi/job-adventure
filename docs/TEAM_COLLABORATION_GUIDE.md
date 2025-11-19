# Team Collaboration Guide

## Overview

The system now supports team collaboration, allowing multiple users from the same company to work together on job postings and candidate evaluations.

## How It Works

### 1. Company-Based Access

When users register, they can specify a **Company Name**. Users with the same company name automatically become part of the same team.

### 2. Shared Job Access

- All team members can see jobs created by anyone in their company
- Jobs are no longer limited to just the creator
- This enables collaborative hiring workflows

### 3. Notes System

The notes feature supports two types of notes:

- **Public Notes** (default): Visible to all team members working on the same job
- **Private Notes**: Only visible to the note author

This allows team members to:
- Share candidate feedback with the team (public notes)
- Keep personal observations private (private notes)

## Setup Instructions

### For New Users

1. Go to the registration page
2. Fill in your details including **Company Name**
3. **Select from existing companies** or type a new one:
   - As you type, you'll see a dropdown of existing companies
   - Click on an existing company to join that team
   - Or type a new name to create a new company
4. You'll see a preview showing whether you're joining an existing company or creating a new one
5. After registration, you'll automatically see all jobs from your company

**Note**: Company names are automatically normalized:
- "Tech Corp" → "tech corp"
- "  ACME  Inc  " → "acme inc"
- "My-Company" → "my-company"

This ensures teammates can find each other even with slight variations in capitalization or spacing.

**Autocomplete Feature**: The company field now shows existing companies as you type, making it easy to:
- Find your company without typos
- See if your company already exists
- Avoid creating duplicate companies

### For Existing Users

Existing users currently have `company_id = NULL`. To enable team collaboration:

**Option 1: Update via Database**
```sql
-- First, create a company
INSERT INTO companies (id, name, created_at, updated_at) 
VALUES (gen_random_uuid(), 'Your Company Name', NOW(), NOW());

-- Then update users to belong to that company
UPDATE users 
SET company_id = (SELECT id FROM companies WHERE name = 'Your Company Name')
WHERE email IN ('user1@example.com', 'user2@example.com');
```

**Option 2: Re-register**
- Create a new account with the company name
- This is simpler for testing

## Features Enabled by Team Collaboration

### 1. Shared Job Listings
- All team members see the same job postings
- No need to manually share access

### 2. Collaborative Notes
- Team members can leave feedback on candidates
- Public notes are visible to everyone
- Private notes remain confidential

### 3. Candidate Status Updates
- Any team member can update candidate status
- Status changes are visible to the whole team

### 4. Interview Scheduling
- Team members can schedule interviews for candidates
- Interview information is shared across the team

## Testing Team Collaboration

### Test Scenario

1. **Create two users with the same company:**
   - User A: `alice@company.com` with company "Acme Corp"
   - User B: `bob@company.com` with company "Acme Corp"

2. **User A creates a job posting**

3. **User B logs in and should see:**
   - The job created by User A
   - All candidates added to that job
   - Public notes left by User A

4. **User B can:**
   - Add candidates to the job
   - Leave public notes (visible to User A)
   - Leave private notes (only visible to User B)
   - Update candidate status
   - Schedule interviews

## Privacy & Permissions

### What's Shared
- Job postings
- Candidate information
- Match results
- Public notes
- Interview schedules
- Candidate status updates

### What's Private
- Private notes (marked with checkbox)
- User passwords and authentication
- Personal user settings

## Technical Implementation

### Database Changes
- Added `companies` table
- Added foreign key `company_id` to `users` table
- Modified job queries to filter by company instead of individual user

### Backend Changes
- `CompanyRepository`: Manages company records
- `JobRepository.get_by_company_id()`: Fetches jobs for entire company
- `CandidateNoteRepository`: Filters notes based on privacy settings
- Auth endpoint: Auto-creates companies during registration

### Frontend Changes
- Registration form: Added "Company Name" field
- Job listings: Now show company-wide jobs
- Notes UI: Shows author information for team context

## Future Enhancements

Potential improvements for full team management:

1. **Team Invitations**: Invite members via email
2. **Role-Based Permissions**: Different access levels (admin, recruiter, viewer)
3. **Activity Feed**: See what team members are doing
4. **Team Settings**: Manage company profile and preferences
5. **User Directory**: See all team members
6. **Audit Logs**: Track who made what changes

## Troubleshooting

### I don't see my teammate's jobs
- Verify you both used the exact same company name (case-sensitive)
- Check your `company_id` in the database
- Ensure you're both logged in

### Notes aren't showing up
- Public notes are visible to all team members
- Private notes are only visible to the author
- Check the "Private note" checkbox status

### Can't update teammate's candidates
- All team members should be able to update candidate status
- If not, check your role permissions in the database
