'use client';

import { useState, useEffect } from 'react';
import Dashboard from '@/components/Dashboard';
import FileUpload from '@/components/FileUpload';
import JobList from '@/components/JobList';
import { Job, JobStatistics } from '@/types/job';
import { apiClient } from '@/lib/api';

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobStats, setJobStats] = useState<JobStatistics>({
    total_jobs: 0,
    completed_jobs: 0,
    failed_jobs: 0,
    processing_jobs: 0,
    pending_jobs: 0,
  });
  const [loading, setLoading] = useState(true);

  const fetchJobs = async () => {
    try {
      const response = await apiClient.get('/jobs');
      setJobs(response.data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  const fetchJobStats = async () => {
    try {
      const response = await apiClient.get('/statistics');
      setJobStats(response.data);
    } catch (error) {
      console.error('Error fetching job stats:', error);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchJobs(), fetchJobStats()]);
      setLoading(false);
    };

    loadData();

    // Set up polling for real-time updates
    const interval = setInterval(() => {
      fetchJobs();
      fetchJobStats();
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, []);

  const handleJobUpdate = () => {
    fetchJobs();
    fetchJobStats();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading platform...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-xl font-bold text-gray-900">
                  Agentic AI Data Quality Platform
                </h1>
                <p className="text-sm text-gray-600">Intelligent data processing and quality analysis</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-xs text-gray-500">
                Last updated: {new Date().toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="space-y-6">
          {/* Dashboard Stats */}
          <Dashboard stats={jobStats} />

          {/* File Processing Section */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Reference File & Batch Processing
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Upload a reference file to define data quality standards, then process all files in the directory against this reference.
            </p>
            <FileUpload onJobUpdate={handleJobUpdate} />
          </div>

          {/* Jobs List */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Processing Jobs
            </h2>
            <JobList jobs={jobs} onJobUpdate={handleJobUpdate} />
          </div>
        </div>
      </main>
    </div>
  );
}
