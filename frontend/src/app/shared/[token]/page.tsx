"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { apiClient, SharedView } from "@/lib/api";
import { LoadingSpinner } from "@/components/LoadingSpinner";

export default function SharedCandidatesView() {
  const params = useParams();
  const token = params.token as string;

  const [data, setData] = useState<SharedView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSharedData();
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadSharedData = async () => {
    setLoading(true);
    const response = await apiClient.viewSharedCandidates(token);
    
    if (response.error) {
      setError(response.error);
    } else {
      setData(response.data || null);
    }
    
    setLoading(false);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600 bg-green-100";
    if (score >= 60) return "text-yellow-600 bg-yellow-100";
    return "text-red-600 bg-red-100";
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
          <svg
            className="h-16 w-16 text-red-500 mx-auto mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Access Denied
          </h2>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">No data available</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {data.job_title}
              </h1>
              <p className="text-lg text-gray-600 mt-1">{data.job_company}</p>
              <p className="text-sm text-gray-500 mt-2">
                Shared by {data.shared_by}
              </p>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
              <span>View-only access</span>
            </div>
          </div>

          {/* Custom Message */}
          {data.custom_message && (
            <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-900">{data.custom_message}</p>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Job Description */}
          <div className="lg:col-span-1">
            <div className="bg-white shadow rounded-lg p-6 sticky top-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Job Description
              </h2>
              <div className="prose prose-sm max-w-none text-gray-700">
                <p className="whitespace-pre-wrap">{data.job_description}</p>
              </div>
            </div>
          </div>

          {/* Candidates List */}
          <div className="lg:col-span-2">
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">
                  Candidate Rankings ({data.candidates.length})
                </h2>
              </div>

              {data.candidates.length === 0 ? (
                <div className="p-6 text-center">
                  <p className="text-gray-500">No candidates available</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {data.candidates.map((candidate) => (
                    <div key={candidate.rank} className="p-6 hover:bg-gray-50">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center">
                          <div className="flex-shrink-0">
                            <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                              <span className="text-gray-600 font-medium text-sm">
                                #{candidate.rank}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <h3 className="text-lg font-medium text-gray-900">
                              {candidate.candidate_name}
                            </h3>
                          </div>
                        </div>
                        <span
                          className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(
                            candidate.match_score
                          )}`}
                        >
                          {Math.round(candidate.match_score)}% Match
                        </span>
                      </div>

                      <div className="mt-4">
                        {/* Key Strengths */}
                        {candidate.key_strengths.length > 0 && (
                          <div className="mb-3">
                            <p className="text-xs font-medium text-gray-500 mb-2">
                              Key Strengths
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {candidate.key_strengths.map((strength, idx) => (
                                <span
                                  key={idx}
                                  className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-green-100 text-green-800"
                                >
                                  {strength}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Missing Skills */}
                        {candidate.missing_skills.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-gray-500 mb-2">
                              Areas for Development
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {candidate.missing_skills.map((skill, idx) => (
                                <span
                                  key={idx}
                                  className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-red-100 text-red-800"
                                >
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            Powered by Job Matching Platform • View-only access
          </p>
        </div>
      </div>
    </div>
  );
}
