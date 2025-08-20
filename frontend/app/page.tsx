'use client';

import { useState, useEffect, useCallback } from 'react';
import Header from '@/components/Header';
import Dashboard from '@/components/Dashboard';
import FileUpload from '@/components/FileUpload';
import JobList from '@/components/JobList';
import OutputFilesSection from '@/components/OutputFilesSection';
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
  const [lastUpdate, setLastUpdate] = useState<string>('');

  // API calls for data fetching
  const fetchJobs = useCallback(async () => {
    try {
      const response = await apiClient.get('/jobs');
      setJobs(response.data);
      setLoading(false);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (error) {
      console.error('Error fetching jobs:', error);
      setLoading(false);
    }
  }, []);

  const fetchJobStats = useCallback(async () => {
    try {
      const response = await apiClient.get('/statistics');
      setJobStats(response.data);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (error) {
      console.error('Error fetching job stats:', error);
    }
  }, []);

  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchJobs(), fetchJobStats()]);
      setLoading(false);
    };
    loadData();
  }, [fetchJobs, fetchJobStats]);

  // Set up polling for regular updates
  useEffect(() => {
    const interval = setInterval(() => {
      fetchJobs();
      fetchJobStats();
    }, 5000); // Poll every 5 seconds
    
    return () => clearInterval(interval);
  }, [fetchJobs, fetchJobStats]);

  const handleJobUpdate = useCallback(() => {
    // Trigger immediate refresh
    fetchJobs();
    fetchJobStats();
  }, [fetchJobs, fetchJobStats]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 theme-transition">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400 theme-transition">Loading platform...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 theme-transition">
      {/* Header */}
      <Header lastUpdated={lastUpdate} />

      {/* Main Content */}
      <main className="w-full px-4 sm:px-6 lg:px-8 py-6">
        <div className="space-y-6">
          {/* Dashboard Stats */}
          <Dashboard stats={jobStats} />

          {/* File Processing Section */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 theme-transition">
              Reference File & Batch Processing
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 theme-transition">
              Upload a reference file to define data quality standards, then process all files in the directory against this reference.
            </p>
            <FileUpload onJobUpdate={handleJobUpdate} />
          </div>

          {/* Jobs List */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 theme-transition">
              Processing Jobs
            </h2>
            <JobList jobs={jobs} onJobUpdate={handleJobUpdate} />
          </div>

          {/* Output Files Section */}
          <OutputFilesSection onJobUpdate={handleJobUpdate} />
        </div>
      </main>
    </div>
  );
}
