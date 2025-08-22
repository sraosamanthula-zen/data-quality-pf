'use client';

import { useState } from 'react';
import { 
  ClockIcon, 
  CheckCircleIcon, 
  ExclamationCircleIcon, 
  XCircleIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import { Job } from '@/types/job';
import { apiClient } from '@/lib/api';

interface JobListProps {
  jobs: Job[];
  onJobUpdate: () => void;
}

interface JobDetailsModalProps {
  job: Job | null;
  isOpen: boolean;
  onClose: () => void;
}

function JobDetailsModal({ job, isOpen, onClose }: JobDetailsModalProps) {
  if (!isOpen || !job) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 dark:bg-gray-900 bg-opacity-50 dark:bg-opacity-75 overflow-y-auto h-full w-full z-50 theme-transition">
      <div className="relative top-20 mx-auto p-5 border border-gray-200 dark:border-gray-700 w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white dark:bg-gray-800 theme-transition">
        <div className="mt-3">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 theme-transition">
              Job Details - {job.id}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 theme-transition"
            >
              <XCircleIcon className="h-5 w-5" />
            </button>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400 theme-transition">File</p>
                <p className="text-sm text-gray-900 dark:text-gray-100 theme-transition">{job.filename}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500">Status</p>
                <p className="text-sm text-gray-900">{job.status}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500">Created</p>
                <p className="text-sm text-gray-900">
                  {new Date(job.created_at).toLocaleString()}
                </p>
              </div>
              {job.completed_at && (
                <div>
                  <p className="text-sm font-medium text-gray-500">Completed</p>
                  <p className="text-sm text-gray-900">
                    {new Date(job.completed_at).toLocaleString()}
                  </p>
                </div>
              )}
            </div>

            {/* Data Quality Indicators */}
            <div className="mt-6">
              <h4 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-3 theme-transition">Data Quality</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-500 dark:text-gray-400 theme-transition">Sparse Data:</span>
                  {job.is_sparse === true && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                      Yes
                    </span>
                  )}
                  {job.is_sparse === false && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      No
                    </span>
                  )}
                  {job.is_sparse === null && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      Not Analyzed
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-500 dark:text-gray-400 theme-transition">Duplicates:</span>
                  {job.has_duplicates === true && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                      Yes
                    </span>
                  )}
                  {job.has_duplicates === false && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      No
                    </span>
                  )}
                  {job.has_duplicates === null && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      Not Analyzed
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Error Message Display */}
            {job.error_message && (
              <div className="mt-6">
                <h4 className="text-md font-medium text-red-800 dark:text-red-400 mb-3 theme-transition">Error Details</h4>
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-3 theme-transition">
                  <p className="text-sm text-red-700 dark:text-red-300 theme-transition">{job.error_message}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function JobList({ jobs, onJobUpdate }: JobListProps) {
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploaded':
        return <ClockIcon className="h-4 w-4 text-gray-500 status-icon" />;
      case 'pending':
        return <ClockIcon className="h-4 w-4 text-yellow-500 status-icon" />;
      case 'processing':
      case 'processing_uc1':
      case 'processing_uc4':
      case 'analyzing_completeness':
      case 'detecting_duplicates':
      case 'cleaning_file':
        return <ClockIcon className="h-4 w-4 text-blue-500 animate-pulse status-icon" />;
      case 'completed':
      case 'analysis_complete':
      case 'cleaning_complete':
        return <CheckCircleIcon className="h-4 w-4 text-green-500 status-icon" />;
      case 'failed':
      case 'cleaning_failed':
        return <XCircleIcon className="h-4 w-4 text-red-500 status-icon" />;
      case 'analysis_complete_with_warnings':
        return <ExclamationCircleIcon className="h-4 w-4 text-yellow-500 status-icon" />;
      default:
        return <ClockIcon className="h-4 w-4 text-gray-500 status-icon" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'uploaded':
        return 'bg-gray-100 text-gray-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'processing':
      case 'processing_uc1':
      case 'processing_uc4':
      case 'analyzing_completeness':
      case 'detecting_duplicates':
      case 'cleaning_file':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
      case 'analysis_complete':
      case 'cleaning_complete':
        return 'bg-green-100 text-green-800';
      case 'failed':
      case 'cleaning_failed':
        return 'bg-red-100 text-red-800';
      case 'analysis_complete_with_warnings':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'uploaded':
        return 'Uploaded';
      case 'pending':
        return 'Processing Soon';
      case 'processing':
        return 'Processing';
      case 'processing_uc1':
        return 'Processing UC1';
      case 'processing_uc4':
        return 'Processing UC4';
      case 'analyzing_completeness':
        return 'Analyzing Completeness';
      case 'detecting_duplicates':
        return 'Detecting Duplicates';
      case 'cleaning_file':
        return 'Cleaning File';
      case 'completed':
        return 'Completed';
      case 'analysis_complete':
        return 'Analysis Complete';
      case 'cleaning_complete':
        return 'Cleaning Complete';
      case 'failed':
        return 'Failed';
      case 'cleaning_failed':
        return 'Cleaning Failed';
      case 'analysis_complete_with_warnings':
        return 'Complete with Warnings';
      default:
        return status.charAt(0).toUpperCase() + status.slice(1);
    }
  };

  const handleViewDetails = (job: Job) => {
    setSelectedJob(job);
    setIsModalOpen(true);
  };

  const handleDeleteJob = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this job?')) return;

    try {
      await apiClient.delete(`/jobs/${jobId}`);
      onJobUpdate();
    } catch (error) {
      console.error('Error deleting job:', error);
    }
  };

  const handleStartProcessing = async (jobId: string) => {
    try {
      await apiClient.post(`/jobs/${jobId}/start`);
      onJobUpdate();
    } catch (error) {
      console.error('Error starting job processing:', error);
    }
  };

  const handleDownloadFile = async (jobId: string, job: Job) => {
    try {
      // Use the jobs download endpoint
      const response = await apiClient.get(`/jobs/${jobId}/download`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', job.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading file:', error);
    }
  };

  if (jobs.length === 0) {
    return (
      <div className="text-center py-8">
        <ClockIcon className="h-8 w-8 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-500">No jobs found. Upload a file to get started.</p>
      </div>
    );
  }

  return (
    <>
      <div className="max-h-96 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg theme-transition">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700 sticky top-0 z-10 theme-transition">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider theme-transition">
                  File
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider theme-transition">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider theme-transition">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider theme-transition">
                  Quality
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider theme-transition">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider theme-transition">
                  Actions
                </th>
              </tr>
            </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700 theme-transition">
            {jobs.map((job) => (
              <tr key={job.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 theme-transition">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100 theme-transition">
                    {job.filename}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400 theme-transition">ID: {job.id}</div>
                  {/* {job.selected_ucs && (
                    <div className="text-xs text-blue-600 dark:text-blue-400 theme-transition">UCs: {job.selected_ucs}</div>
                  )} */}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {/* Render each selected UC as an individual bubble */}
                  {Array.isArray(job.selected_ucs) && job.selected_ucs.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {job.selected_ucs.map((uc: string) => (
                        <span
                          key={uc}
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            uc === 'UC1' ? 'bg-blue-100 text-blue-800' : uc === 'UC4' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {uc}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-xs text-gray-500">—</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(job.status)}
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                      {getStatusText(job.status)}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {(() => {
                      // Priority: failed > duplicates > sparse > clean > pending
                      if (job.status === 'failed') {
                        return (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 truncate">
                            Failed
                          </span>
                        );
                      }
                      if (job.has_duplicates === true) {
                        return (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800 truncate">
                            Duplicates
                          </span>
                        );
                      }
                      if (job.is_sparse === true) {
                        return (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 truncate">
                            Sparse
                          </span>
                        );
                      }
                      if (job.status === 'completed' && job.is_sparse === false && job.has_duplicates === false) {
                        return (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 truncate">
                            Clean
                          </span>
                        );
                      }

                      return (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 truncate">
                          Pending
                        </span>
                      );
                    })()}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(job.created_at).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                  <button
                    onClick={() => handleViewDetails(job)}
                    className="text-blue-600 hover:text-blue-900"
                    title="View Details"
                  >
                    <EyeIcon className="h-4 w-4 status-icon" />
                  </button>
                  {job.status === 'completed' && (
                    <button
                      onClick={() => handleDownloadFile(job.id.toString(), job)}
                      className="text-green-600 hover:text-green-900"
                      title="Download Result"
                    >
                      <ArrowDownTrayIcon className="h-4 w-4 status-icon" />
                    </button>
                  )}
                  <button
                    onClick={() => handleDeleteJob(job.id.toString())}
                    className="text-red-600 hover:text-red-900"
                    title="Delete Job"
                    >
                    <TrashIcon className="h-4 w-4 status-icon" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </div>

      <JobDetailsModal
        job={selectedJob}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
}
