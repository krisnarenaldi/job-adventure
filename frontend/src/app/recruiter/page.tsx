'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient, JobDescription } from '@/lib/api';
import { LoadingSpinner } from '@/components/LoadingSpinner';

export default function RecruiterDashboard() {
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');
  const [updatingStatus, setUpdatingStatus] = useState<string | null>(null);

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    setLoading(true);
    const response = await apiClient.getJobs();
    
    if (response.error) {
      setError(response.error);
    } else {
      setJobs(response.data || []);
    }
    
    setLoading(false);
  };

  const toggleJobStatus = async (jobId: string, currentStatus: boolean) => {
    setUpdatingStatus(jobId);
    const response = await apiClient.updateJobStatus(jobId, !currentStatus);
    
    if (response.error) {
      setError(response.error);
    } else {
      // Update the job in the list
      setJobs(jobs.map(job => 
        job.id === jobId ? { ...job, is_active: !currentStatus } : job
      ));
    }
    
    setUpdatingStatus(null);
  };

  const filteredJobs = jobs.filter(job => {
    if (filterStatus === 'active') return job.is_active;
    if (filterStatus === 'inactive') return !job.is_active;
    return true;
  });

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
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Recruiter Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Manage job postings and review candidate matches
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <Link
            href="/recruiter/jobs/new"
            className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Create Job Posting
          </Link>
        </div>
      </div>

      {error && (
        <div className="mt-6 bg-red-50 border border-red-200 rounded-md p-4">
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

      <div className="mt-8">
        {/* Filter Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setFilterStatus('all')}
              className={`${
                filterStatus === 'all'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              All Jobs ({jobs.length})
            </button>
            <button
              onClick={() => setFilterStatus('active')}
              className={`${
                filterStatus === 'active'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Active ({jobs.filter(j => j.is_active).length})
            </button>
            <button
              onClick={() => setFilterStatus('inactive')}
              className={`${
                filterStatus === 'inactive'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              Inactive ({jobs.filter(j => !j.is_active).length})
            </button>
          </nav>
        </div>

        {filteredJobs.length === 0 ? (
          <div className="text-center py-12">
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
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No job postings</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating your first job posting.
            </p>
            <div className="mt-6">
              <Link
                href="/recruiter/jobs/new"
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Create Job Posting
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filteredJobs.map((job) => (
              <div
                key={job.id}
                className={`bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow ${
                  !job.is_active ? 'opacity-75' : ''
                }`}
              >
                <div className="p-6">
                  <div className="flex items-center justify-between mb-3">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        job.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {job.is_active ? 'Active' : 'Inactive'}
                    </span>
                    <button
                      onClick={() => toggleJobStatus(job.id, job.is_active)}
                      disabled={updatingStatus === job.id}
                      className={`text-xs font-medium ${
                        updatingStatus === job.id
                          ? 'text-gray-400 cursor-not-allowed'
                          : 'text-blue-600 hover:text-blue-900'
                      }`}
                      title={job.is_active ? 'Deactivate job' : 'Activate job'}
                    >
                      {updatingStatus === job.id ? 'Updating...' : job.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </div>
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center">
                        <span className="text-white font-medium text-sm">
                          {job.company.charAt(0).toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <h3 className="text-lg font-medium text-gray-900 truncate">
                        {job.title}
                      </h3>
                      <p className="text-sm text-gray-500">{job.company}</p>
                    </div>
                  </div>
                  <div className="mt-4">
                    <p className="text-sm text-gray-600 line-clamp-3">
                      {job.description.substring(0, 150)}...
                    </p>
                  </div>
                  <div className="mt-4 flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {job.candidate_count || 0} {job.candidate_count === 1 ? 'Candidate' : 'Candidates'}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(job.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="flex space-x-2">
                      <Link
                        href={`/recruiter/jobs/${job.id}/candidates`}
                        className="text-blue-600 hover:text-blue-900 text-sm font-medium"
                      >
                        View
                      </Link>
                      <Link
                        href={`/recruiter/jobs/${job.id}`}
                        className="text-gray-600 hover:text-gray-900 text-sm font-medium"
                      >
                        Details
                      </Link>
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