const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface JobDescription {
  id: string;
  title: string;
  company: string;
  description: string;
  requirements: string;
  created_at: string;
  candidate_count?: number;
  is_active: boolean;
}

export interface Resume {
  id: string;
  candidate_name: string;
  email?: string;
  phone?: string;
  content: string;
  sections: Record<string, string>;
  uploaded_at: string;
}

export type CandidateStatus = "pending" | "shortlisted" | "rejected" | "maybe";

export interface MatchResult {
  id: string;
  job_id: string;
  resume_id: string;
  match_score: number;
  explanation: string;
  key_strengths: string[];
  missing_skills: string[];
  status?: CandidateStatus;
  status_updated_at?: string;
  status_updated_by?: string;
  created_at: string;
  candidate_name?: string;
  candidate_email?: string;
  job_title?: string;
  job_company?: string;
  resume?: Resume;
}

export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface SkillAnalysis {
  matched_skills: string[];
  missing_skills: string[];
  skill_match_percentage: number;
}

export interface JobMetrics {
  total_applicants: number;
  average_match_score: number;
  top_missing_skills: string[];
}

export type InterviewType = "phone" | "video" | "in-person";
export type InterviewStatus = "scheduled" | "completed" | "cancelled" | "rescheduled";

export interface Interview {
  id: string;
  match_result_id: string;
  job_id: string;
  scheduled_time: string;
  interview_type: InterviewType;
  status: InterviewStatus;
  meeting_link?: string;
  location?: string;
  notes?: string;
  invitation_sent?: string;
  invitation_opened?: string;
  invitation_clicked?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  cancelled_at?: string;
  cancelled_by?: string;
}

export interface InterviewCreate {
  match_result_id: string;
  job_id: string;
  scheduled_time: string;
  interview_type: InterviewType;
  meeting_link?: string;
  location?: string;
  notes?: string;
}

export interface InterviewUpdate {
  scheduled_time?: string;
  interview_type?: InterviewType;
  status?: InterviewStatus;
  meeting_link?: string;
  location?: string;
  notes?: string;
}

export interface CandidateNote {
  id: string;
  match_result_id: string;
  user_id: string;
  author_name?: string;
  author_email?: string;
  note_text: string;
  is_private: boolean;
  created_at: string;
  updated_at: string;
}

export interface NoteCreate {
  match_id: string;
  note_text: string;
  is_private?: boolean;
}

export interface NoteUpdate {
  note_text?: string;
  is_private?: boolean;
}

export interface SharedLink {
  id: string;
  job_id: string;
  share_token: string;
  recipient_email?: string;
  custom_message?: string;
  expires_at?: string;
  is_active: boolean;
  view_count: number;
  last_viewed_at?: string;
  created_at: string;
  share_url?: string;
}

export interface SharedView {
  job_title: string;
  job_company: string;
  job_description: string;
  candidates: Array<{
    rank: number;
    candidate_name: string;
    match_score: number;
    key_strengths: string[];
    missing_skills: string[];
  }>;
  shared_by: string;
  custom_message?: string;
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("auth_token");
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== "undefined") {
      localStorage.setItem("auth_token", token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    // Only set Content-Type if not already set and body is not FormData
    if (!headers["Content-Type"] && !(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    // Always check localStorage for the latest token
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("auth_token");
      if (token) {
        this.token = token;
        headers.Authorization = `Bearer ${token}`;
      }
    } else if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        // Try multiple possible error message fields
        const errorMessage = 
          errorData.detail || 
          errorData.message || 
          errorData.error ||
          (typeof errorData === 'string' ? errorData : null);
        
        // Provide user-friendly fallback messages for common status codes
        if (!errorMessage) {
          if (response.status === 401) {
            return { error: "Incorrect email or password. Please try again." };
          } else if (response.status === 403) {
            return { error: "You don't have permission to perform this action." };
          } else if (response.status === 404) {
            return { error: "The requested resource was not found." };
          } else if (response.status === 422) {
            return { error: "Please check your input and try again." };
          } else if (response.status >= 500) {
            return { error: "A server error occurred. Please try again later." };
          }
        }
        
        return {
          error: errorMessage || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Network error",
      };
    }
  }

  // Authentication
  async login(
    email: string,
    password: string
  ): Promise<
    ApiResponse<{ access_token: string; token_type: string; user: User }>
  > {
    return this.request("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async register(
    email: string,
    password: string,
    full_name: string,
    role: string = "recruiter",
    company_name?: string
  ): Promise<ApiResponse<{ message: string }>> {
    return this.request("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name, role, company_name }),
    });
  }

  async changePassword(
    currentPassword: string,
    newPassword: string
  ): Promise<ApiResponse<{ message: string }>> {
    return this.request("/api/v1/auth/change-password", {
      method: "POST",
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
  }

  async getCurrentUser(): Promise<
    ApiResponse<{ id: string; email: string; full_name: string; role: string }>
  > {
    return this.request("/api/v1/auth/me");
  }

  async getCompanies(search?: string): Promise<
    ApiResponse<Array<{ id: string; name: string }>>
  > {
    const params = search ? `?search=${encodeURIComponent(search)}` : "";
    // Public endpoint - no auth required, but auth header will be added if token exists
    return this.request(`/api/v1/companies${params}`);
  }

  // Job Management
  async createJob(
    jobData: Omit<JobDescription, "id" | "created_at">
  ): Promise<ApiResponse<JobDescription>> {
    return this.request("/api/v1/jobs/", {
      method: "POST",
      body: JSON.stringify(jobData),
    });
  }

  async getJobs(): Promise<ApiResponse<JobDescription[]>> {
    const response = await this.request<{
      jobs: JobDescription[];
      total: number;
      skip: number;
      limit: number;
    }>("/api/v1/jobs/");
    if (response.data) {
      // Extract the jobs array from the response
      const jobs = response.data.jobs || [];
      // Ensure each job has a candidate_count, defaulting to 0 if not provided
      const jobsWithCandidateCount = jobs.map((job) => ({
        ...job,
        candidate_count: job.candidate_count || 0,
      }));
      return { data: jobsWithCandidateCount };
    }
    return { data: [] };
  }

  async getJob(jobId: string): Promise<ApiResponse<JobDescription>> {
    return this.request(`/api/v1/jobs/${jobId}`);
  }

  async updateJobStatus(
    jobId: string,
    isActive: boolean
  ): Promise<ApiResponse<JobDescription>> {
    return this.request(`/api/v1/jobs/${jobId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive }),
    });
  }

  // Resume Management
  async uploadResume(
    file: File,
    candidateName: string,
    email: string,
    phone?: string,
    jobId?: string
  ): Promise<ApiResponse<Resume>> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("candidate_name", candidateName);
    formData.append("email", email);
    if (phone) {
      formData.append("phone", phone);
    }
    if (jobId) {
      formData.append("job_id", jobId);
    }

    return this.request("/api/v1/resumes/upload", {
      method: "POST",
      body: formData,
    });
  }

  async getResumes(): Promise<ApiResponse<Resume[]>> {
    return this.request("/api/v1/resumes/");
  }

  // Matching
  async matchResumeToJob(
    resumeId: string,
    jobId: string
  ): Promise<ApiResponse<MatchResult>> {
    // If resumeId is empty or null, send null to match all resumes
    const resumeIds = resumeId && resumeId.trim() ? [resumeId] : null;
    return this.request("/api/v1/matching/match", {
      method: "POST",
      body: JSON.stringify({ job_id: jobId, resume_ids: resumeIds }),
    });
  }

  async getMatchResults(jobId: string): Promise<ApiResponse<MatchResult[]>> {
    const response = await this.request<{ matches: MatchResult[] }>(
      `/api/v1/matching/results/${jobId}`
    );
    if (response.data) {
      // Extract the matches array from the response
      const matches = response.data.matches || [];
      return {
        ...response,
        data: matches,
      };
    }
    return { data: [] };
  }

  async analyzeSkills(
    resumeId: string,
    jobId: string
  ): Promise<ApiResponse<SkillAnalysis>> {
    return this.request(`/api/v1/matching/skills/${resumeId}/${jobId}`);
  }

  // Analytics
  async getJobMetrics(jobId: string): Promise<ApiResponse<JobMetrics>> {
    return this.request(`/api/v1/analytics/job/${jobId}/metrics`);
  }

  // Interviews
  async createInterview(data: InterviewCreate): Promise<ApiResponse<Interview>> {
    return this.request("/api/v1/interviews/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getInterviewsByJob(jobId: string, status?: InterviewStatus): Promise<ApiResponse<Interview[]>> {
    const params = status ? `?status=${status}` : "";
    return this.request(`/api/v1/interviews/job/${jobId}${params}`);
  }

  async getInterview(interviewId: string): Promise<ApiResponse<Interview>> {
    return this.request(`/api/v1/interviews/${interviewId}`);
  }

  async updateInterview(interviewId: string, data: InterviewUpdate): Promise<ApiResponse<Interview>> {
    return this.request(`/api/v1/interviews/${interviewId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async cancelInterview(interviewId: string): Promise<ApiResponse<void>> {
    return this.request(`/api/v1/interviews/${interviewId}`, {
      method: "DELETE",
    });
  }

  async sendInterviewInvitation(interviewId: string): Promise<ApiResponse<Interview>> {
    return this.request(`/api/v1/interviews/${interviewId}/send-invitation`, {
      method: "POST",
    });
  }

  async previewInterviewInvitation(interviewId: string): Promise<ApiResponse<{ subject: string; body: string }>> {
    return this.request(`/api/v1/interviews/${interviewId}/preview-invitation`);
  }

  // File Upload
  async uploadFile(
    file: File
  ): Promise<ApiResponse<{ file_id: string; filename: string }>> {
    const formData = new FormData();
    formData.append("file", file);

    return this.request("/api/v1/files/upload", {
      method: "POST",
      headers: {},
      body: formData,
    });
  }

  // Status Management
  async updateMatchStatus(
    matchId: string,
    status: CandidateStatus
  ): Promise<ApiResponse<{ id: string; status: CandidateStatus; message: string }>> {
    return this.request(`/api/v1/matching/results/${matchId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
  }

  async getMatchesByStatus(
    jobId: string,
    status: CandidateStatus
  ): Promise<ApiResponse<MatchResult[]>> {
    const response = await this.request<{ matches: MatchResult[] }>(
      `/api/v1/matching/results/${jobId}/by-status/${status}`
    );
    if (response.data) {
      const matches = response.data.matches || [];
      return {
        ...response,
        data: matches,
      };
    }
    return { data: [] };
  }

  // Notes Management
  async getNotes(matchId: string): Promise<ApiResponse<CandidateNote[]>> {
    return this.request(`/api/v1/notes/match/${matchId}`);
  }

  async createNote(data: NoteCreate): Promise<ApiResponse<CandidateNote>> {
    return this.request(`/api/v1/notes`, {
      method: "POST",
      body: JSON.stringify({ match_result_id: data.match_id, note_text: data.note_text, is_private: data.is_private }),
    });
  }

  async updateNote(noteId: string, data: NoteUpdate): Promise<ApiResponse<CandidateNote>> {
    return this.request(`/api/v1/notes/${noteId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteNote(noteId: string): Promise<ApiResponse<void>> {
    return this.request(`/api/v1/notes/${noteId}`, {
      method: "DELETE",
    });
  }

  // Export functionality
  async exportCandidates(
    jobId: string,
    format: "csv" | "xlsx",
    filters?: {
      status?: CandidateStatus;
      minScore?: number;
      maxScore?: number;
    }
  ): Promise<Blob | null> {
    const params = new URLSearchParams({ format });
    
    if (filters?.status) {
      params.append("status", filters.status);
    }
    if (filters?.minScore !== undefined) {
      params.append("min_score", filters.minScore.toString());
    }
    if (filters?.maxScore !== undefined) {
      params.append("max_score", filters.maxScore.toString());
    }

    const url = `${this.baseUrl}/api/v1/matching/jobs/${jobId}/candidates/export?${params.toString()}`;
    const headers: Record<string, string> = {};

    if (typeof window !== "undefined") {
      const token = localStorage.getItem("auth_token");
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
    } else if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, { headers });

      if (!response.ok) {
        console.error("Export failed:", response.statusText);
        return null;
      }

      return await response.blob();
    } catch (error) {
      console.error("Export error:", error);
      return null;
    }
  }

  // Sharing functionality
  async createSharedLink(data: {
    job_id: string;
    recipient_email?: string;
    custom_message?: string;
    expires_in_days?: number;
  }): Promise<ApiResponse<SharedLink>> {
    return this.request("/api/v1/sharing/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getSharedLinksForJob(jobId: string): Promise<ApiResponse<SharedLink[]>> {
    const response = await this.request<{ links: SharedLink[]; total: number }>(
      `/api/v1/sharing/job/${jobId}`
    );
    if (response.data) {
      return { data: response.data.links };
    }
    return { data: [] };
  }

  async deactivateSharedLink(linkId: string): Promise<ApiResponse<{ message: string }>> {
    return this.request(`/api/v1/sharing/${linkId}`, {
      method: "DELETE",
    });
  }

  async viewSharedCandidates(token: string): Promise<ApiResponse<SharedView>> {
    return this.request(`/api/v1/sharing/view/${token}`);
  }

  // Candidate Manager
  async getAllCandidates(params: {
    skip?: number;
    limit?: number;
    status?: CandidateStatus;
    job_id?: string;
    min_score?: number;
    max_score?: number;
    search?: string;
    sort_by?: 'created_at' | 'match_score' | 'status';
    sort_order?: 'asc' | 'desc';
    date_from?: string;
    date_to?: string;
  }): Promise<ApiResponse<{ matches: MatchResult[]; total: number; skip: number; limit: number }>> {
    const queryParams = new URLSearchParams();
    
    if (params.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params.status) queryParams.append('status', params.status);
    if (params.job_id) queryParams.append('job_id', params.job_id);
    if (params.min_score !== undefined) queryParams.append('min_score', params.min_score.toString());
    if (params.max_score !== undefined) queryParams.append('max_score', params.max_score.toString());
    if (params.search) queryParams.append('search', params.search);
    if (params.sort_by) queryParams.append('sort_by', params.sort_by);
    if (params.sort_order) queryParams.append('sort_order', params.sort_order);
    if (params.date_from) queryParams.append('date_from', params.date_from);
    if (params.date_to) queryParams.append('date_to', params.date_to);

    return this.request(`/api/v1/matching/candidates/all?${queryParams.toString()}`);
  }

  async exportAllCandidates(
    format: "csv" | "xlsx",
    filters?: {
      status?: CandidateStatus;
      job_id?: string;
      minScore?: number;
      maxScore?: number;
      search?: string;
      dateFrom?: string;
      dateTo?: string;
    }
  ): Promise<Blob | null> {
    const params = new URLSearchParams({ format });
    
    if (filters?.status) {
      params.append("status", filters.status);
    }
    if (filters?.job_id) {
      params.append("job_id", filters.job_id);
    }
    if (filters?.minScore !== undefined) {
      params.append("min_score", filters.minScore.toString());
    }
    if (filters?.maxScore !== undefined) {
      params.append("max_score", filters.maxScore.toString());
    }
    if (filters?.search) {
      params.append("search", filters.search);
    }
    if (filters?.dateFrom) {
      params.append("date_from", filters.dateFrom);
    }
    if (filters?.dateTo) {
      params.append("date_to", filters.dateTo);
    }

    const url = `${this.baseUrl}/api/v1/matching/candidates/export?${params.toString()}`;
    const headers: Record<string, string> = {};

    if (typeof window !== "undefined") {
      const token = localStorage.getItem("auth_token");
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
    } else if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, { headers });

      if (!response.ok) {
        console.error("Export failed:", response.statusText);
        return null;
      }

      return await response.blob();
    } catch (error) {
      console.error("Export error:", error);
      return null;
    }
  }

  // Contact submission
  async submitContact(
    email: string,
    description?: string,
    file?: File
  ): Promise<ApiResponse<{ id: string; message: string }>> {
    const formData = new FormData();
    formData.append("email", email);
    if (description) {
      formData.append("description", description);
    }
    if (file) {
      formData.append("file", file);
    }

    return this.request("/api/v1/contacts/", {
      method: "POST",
      body: formData,
    });
  }
}

export const apiClient = new ApiClient();
