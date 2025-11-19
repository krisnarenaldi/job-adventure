'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { apiClient, JobDescription, JobMetrics } from '@/lib/api';
import { LoadingSpinner } from '@/components/LoadingSpinner';

export default function JobDetails() {
  const params = useParams();
  const jobId = params.id as string;
  
  const [job, setJob] = useState<JobDescription | null>(null);
  const [metrics, setMetrics] = useState<JobMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingStatus, setUpdatingStatus] = useState(false);

  useEffect(() => {
    loadJobDetails();
  }, [jobId]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadJobDetails = async () => {
    setLoading(true);
    
    // Load job details
    const jobResponse = await apiClient.getJob(jobId);
    if (jobResponse.error) {
      setError(jobResponse.error);
    } else {
      setJob(jobResponse.data || null);
    }

    // Load job metrics
    const metricsResponse = await apiClient.getJobMetrics(jobId);
    if (metricsResponse.data) {
      setMetrics(metricsResponse.data);
    }
    
    setLoading(false);
  };

  const toggleJobStatus = async () => {
    if (!job) return;
    
    setUpdatingStatus(true);
    const response = await apiClient.updateJobStatus(jobId, !job.is_active);
    
    if (response.error) {
      setError(response.error);
    } else {
      setJob({ ...job, is_active: !job.is_active });
    }
    
    setUpdatingStatus(false);
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex justify-center">
          <LoadingSpinner size="lg" />
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900">Job not found</h2>
          <p className="mt-2 text-gray-600">The job you&apos;re looking for doesn&apos;t exist.</p>
          <Link
            href="/recruiter"
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-8">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-3xl font-bold text-gray-900">{job.title}</h1>
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  job.is_active
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {job.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            <p className="mt-1 text-lg text-gray-600">{job.company}</p>
            <p className="mt-1 text-sm text-gray-500">
              Posted on {new Date(job.created_at).toLocaleDateString()}
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={toggleJobStatus}
              disabled={updatingStatus}
              className={`inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md ${
                updatingStatus
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              {updatingStatus ? 'Updating...' : job.is_active ? 'Deactivate' : 'Activate'}
            </button>
            <Link
              href={`/recruiter/jobs/${job.id}/candidates`}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              View Candidates
            </Link>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Job Details */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Job Description</h2>
            <div className="prose max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap">{job.description}</p>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Requirements</h2>
            <div className="prose max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap">{job.requirements}</p>
            </div>
          </div>
        </div>

        {/* Metrics Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Job Metrics</h2>
            
            {metrics ? (
              <div className="space-y-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Total Applicants</dt>
                  <dd className="mt-1 text-2xl font-semibold text-gray-900">
                    {metrics.total_applicants}
                  </dd>
                </div>
                
                <div>
                  <dt className="text-sm font-medium text-gray-500">Average Match Score</dt>
                  <dd className="mt-1 text-2xl font-semibold text-gray-900">
                    {metrics.average_match_score ? `${Math.round(metrics.average_match_score)}%` : 'N/A'}
                  </dd>
                </div>
                
                {metrics.top_missing_skills.length > 0 && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500 mb-2">Top Missing Skills</dt>
                    <dd className="space-y-1">
                      {metrics.top_missing_skills.slice(0, 5).map((skill, index) => (
                        <span
                          key={index}
                          className="inline-block bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full mr-1 mb-1"
                        >
                          {skill}
                        </span>
                      ))}
                    </dd>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No metrics available yet. Upload some resumes to see analytics.</p>
            )}
          </div>

          <div className="mt-6 bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <Link
                href={`/recruiter/jobs/${job.id}/candidates`}
                className="block w-full text-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Manage Candidates
              </Link>
              <button
                onClick={() => window.print()}
                className="block w-full text-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Print Job Details
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}