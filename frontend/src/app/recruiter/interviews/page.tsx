"use client";

import { useState, useEffect } from "react";
import { apiClient, Interview, InterviewStatus } from "@/lib/api";
import { LoadingSpinner } from "@/components/LoadingSpinner";

export default function InterviewsPage() {
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<InterviewStatus | "all">("all");
  const [updatingStatus, setUpdatingStatus] = useState<string | null>(null);

  useEffect(() => {
    loadInterviews();
  }, []);

  const loadInterviews = async () => {
    setLoading(true);
    setError(null);

    try {
      // Get all jobs for the current user
      const jobsResponse = await apiClient.getJobs();
      if (jobsResponse.error || !jobsResponse.data) {
        setError(jobsResponse.error || "Failed to load jobs");
        setInterviews([]);
        setLoading(false);
        return;
      }

      // Get interviews for each job
      const allInterviews: Interview[] = [];
      for (const job of jobsResponse.data) {
        const interviewsResponse = await apiClient.getInterviewsByJob(job.id);
        if (interviewsResponse.data) {
          allInterviews.push(...interviewsResponse.data);
        }
      }

      setInterviews(allInterviews);
    } catch (err) {
      setError("Failed to load interviews");
      setInterviews([]);
    }

    setLoading(false);
  };

  const handleStatusUpdate = async (interviewId: string, newStatus: InterviewStatus) => {
    setUpdatingStatus(interviewId);
    setError(null);
    
    const response = await apiClient.updateInterview(interviewId, { status: newStatus });
    if (response.error) {
      setError(response.error);
    } else {
      // Update the interview in the local state
      setInterviews(prevInterviews =>
        prevInterviews.map(interview =>
          interview.id === interviewId ? { ...interview, status: newStatus } : interview
        )
      );
    }
    
    setUpdatingStatus(null);
  };

  const getStatusColor = (status: InterviewStatus) => {
    switch (status) {
      case "scheduled":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "completed":
        return "bg-green-100 text-green-800 border-green-200";
      case "cancelled":
        return "bg-red-100 text-red-800 border-red-200";
      case "rescheduled":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "video":
        return (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        );
      case "phone":
        return (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
          </svg>
        );
      case "in-person":
        return (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        );
    }
  };

  const filteredInterviews = statusFilter === "all"
    ? interviews
    : interviews.filter(interview => interview.status === statusFilter);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex justify-center">
          <LoadingSpinner size="lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Scheduled Interviews</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage and track all your scheduled interviews
        </p>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Status Filter */}
      <div className="mb-6 flex flex-wrap gap-2">
        <button
          onClick={() => setStatusFilter("all")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            statusFilter === "all"
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          All ({interviews.length})
        </button>
        <button
          onClick={() => setStatusFilter("scheduled")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            statusFilter === "scheduled"
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          Scheduled ({interviews.filter(i => i.status === "scheduled").length})
        </button>
        <button
          onClick={() => setStatusFilter("completed")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            statusFilter === "completed"
              ? "bg-green-600 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          Completed ({interviews.filter(i => i.status === "completed").length})
        </button>
        <button
          onClick={() => setStatusFilter("cancelled")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            statusFilter === "cancelled"
              ? "bg-red-600 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          Cancelled ({interviews.filter(i => i.status === "cancelled").length})
        </button>
      </div>

      {/* Interviews List */}
      <div className="bg-white shadow rounded-lg">
        {filteredInterviews.length === 0 ? (
          <div className="p-12 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No interviews</h3>
            <p className="mt-1 text-sm text-gray-500">
              {interviews.length === 0
                ? "Schedule interviews from the candidates page."
                : `No ${statusFilter} interviews.`}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredInterviews
              .sort((a, b) => new Date(a.scheduled_time).getTime() - new Date(b.scheduled_time).getTime())
              .map((interview) => (
                <div key={interview.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4">
                      <div className="flex-shrink-0">
                        <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
                          {getTypeIcon(interview.interview_type)}
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h3 className="text-lg font-medium text-gray-900">
                            Interview
                          </h3>
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-lg text-xs font-medium border ${getStatusColor(
                              interview.status
                            )}`}
                          >
                            {interview.status.charAt(0).toUpperCase() + interview.status.slice(1)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-500 mt-1">
                          {new Date(interview.scheduled_time).toLocaleDateString('en-GB', { 
                            day: '2-digit', 
                            month: 'short', 
                            year: 'numeric' 
                          })} at {new Date(interview.scheduled_time).toLocaleTimeString('en-US', {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </p>
                        <p className="text-sm text-gray-600 mt-1 capitalize">
                          {interview.interview_type} Interview
                        </p>
                        {interview.meeting_link && (
                          <a
                            href={interview.meeting_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:text-blue-800 mt-1 inline-block"
                          >
                            Join Meeting →
                          </a>
                        )}
                        {interview.location && (
                          <p className="text-sm text-gray-600 mt-1">
                            📍 {interview.location}
                          </p>
                        )}
                        {interview.notes && (
                          <p className="text-sm text-gray-500 mt-2 italic">
                            {interview.notes}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="ml-4">
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Update Status
                      </label>
                      <div className="relative">
                        <select
                          value={interview.status}
                          onChange={(e) => handleStatusUpdate(interview.id, e.target.value as InterviewStatus)}
                          disabled={updatingStatus === interview.id}
                          className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <option value="scheduled">Scheduled</option>
                          <option value="completed">Completed</option>
                          <option value="cancelled">Cancelled</option>
                          <option value="rescheduled">Rescheduled</option>
                        </select>
                        {updatingStatus === interview.id && (
                          <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                            <LoadingSpinner size="sm" />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
