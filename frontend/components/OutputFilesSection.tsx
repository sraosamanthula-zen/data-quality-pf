'use client';

import { useState, useEffect } from 'react';
import { 
  ChevronDownIcon, 
  ChevronRightIcon,
  DocumentTextIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import { apiClient } from '@/lib/api';

interface OutputFile {
  filename: string;
  path: string;
  size: number;
  created: number;
  status: string;
  batch_name?: string;
  uc_type?: string;
  relative_path?: string;
  job_id?: number;
  original_filename?: string;
  unique_filename?: string;
}

interface OutputFilesSectionProps {
  onJobUpdate: () => void;
}

export default function OutputFilesSection({ onJobUpdate }: OutputFilesSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [outputFiles, setOutputFiles] = useState<OutputFile[]>([]);
  const [outputDirectory, setOutputDirectory] = useState<string>('');
  const [completedJobs, setCompletedJobs] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewFile, setPreviewFile] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<{
    headers: string[];
    rows: string[][];
    totalRows: number;
  } | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  const fetchOutputFiles = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get('/jobs/outputs');
      setOutputFiles(response.data.files || []);
      setOutputDirectory(response.data.directory || '');
      setCompletedJobs(response.data.completed_jobs || 0);
    } catch (error: any) {
      console.error('Error fetching output files:', error);
      setError(error.response?.data?.detail || 'Failed to fetch output files');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadFile = async (file: OutputFile) => {
    try {
      const response = await apiClient.get('/upload/download-file', {
        params: { 
          filepath: file.path
        },
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', file.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error: any) {
      console.error('Error downloading file:', error);
      setError(error.response?.data?.detail || 'Failed to download file');
    }
  };

  const handlePreviewFile = async (file: OutputFile) => {
    setLoadingPreview(true);
    setPreviewFile(file.filename);
    
    try {
      const response = await apiClient.get('/upload/preview-file', {
        params: {
          filepath: file.path
        }
      });
      setPreviewData(response.data);
    } catch (error: any) {
      console.error('Error previewing file:', error);
      setError(error.response?.data?.detail || 'Failed to preview file');
    } finally {
      setLoadingPreview(false);
    }
  };

  const closePreview = () => {
    setPreviewFile(null);
    setPreviewData(null);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  const getUCBadgeStyle = (ucType: string) => {
    switch (ucType.toLowerCase()) {
      case 'uc1':
        return 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200';
      case 'uc4':
        return 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200';
      case 'processed':
        return 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200';
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200';
    }
  };

  const getBatchBadgeStyle = (batchName: string) => {
    if (batchName === 'individual') {
      return 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200';
    }
    return 'bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-200';
  };

  useEffect(() => {
    if (isExpanded) {
      fetchOutputFiles();
    }
  }, [isExpanded]);

  return (
    <div className="card theme-transition">
      <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-2">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 theme-transition">
            Result Files
          </h2>
          {outputFiles.length > 0 && (
            <span className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs font-medium px-2.5 py-0.5 rounded-full theme-transition">
              {outputFiles.length}
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {isExpanded ? (
            <ChevronDownIcon className="h-5 w-5 text-gray-500 dark:text-gray-400" />
          ) : (
            <ChevronRightIcon className="h-5 w-5 text-gray-500 dark:text-gray-400" />
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-4">
          {/* Directory Information */}
          {outputDirectory && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 theme-transition">
              <div className="flex items-center space-x-2">
                <svg className="h-4 w-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5a2 2 0 012-2h4a2 2 0 012 2v2H8V5z" />
                </svg>
                <span className="text-sm font-medium text-blue-800 dark:text-blue-200 theme-transition">Results Directory:</span>
                <code className="text-sm text-blue-700 dark:text-blue-300 bg-blue-100 dark:bg-blue-800 px-2 py-1 rounded theme-transition">
                  {outputDirectory}
                </code>
              </div>
              {completedJobs > 0 && (
                <div className="mt-2 text-xs text-blue-600 dark:text-blue-400 theme-transition">
                  From {completedJobs} completed job{completedJobs !== 1 ? 's' : ''}
                </div>
              )}
            </div>
          )}

          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 dark:border-blue-400 theme-transition"></div>
              <span className="ml-2 text-gray-600 dark:text-gray-400 theme-transition">Loading output files...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 theme-transition">
              <div className="flex items-center space-x-2">
                <ExclamationCircleIcon className="h-5 w-5 text-red-500 dark:text-red-400 theme-transition" />
                <span className="text-sm text-red-800 dark:text-red-200 theme-transition">{error}</span>
              </div>
            </div>
          )}

          {!loading && !error && outputFiles.length === 0 && (
            <div className="text-center py-8">
              <DocumentTextIcon className="h-12 w-12 text-gray-400 dark:text-gray-600 mx-auto mb-4 theme-transition" />
              <p className="text-gray-500 dark:text-gray-400 text-sm theme-transition">No result files found</p>
              <p className="text-gray-400 dark:text-gray-500 text-xs mt-1 theme-transition">
                Process some files to see results here
              </p>
            </div>
          )}

          {!loading && !error && outputFiles.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-3">
              {outputFiles.map((file, index) => (
                <div
                  key={index}
                  className="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 p-3 hover:shadow-md dark:hover:shadow-lg transition-shadow duration-200 relative min-h-[120px] flex flex-col theme-transition"
                >
                  {/* Status and Preview Icons */}
                  <div className="absolute top-2 right-2 z-10 flex items-center space-x-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handlePreviewFile(file);
                      }}
                      className="bg-blue-100 dark:bg-blue-900 hover:bg-blue-200 dark:hover:bg-blue-800 text-blue-600 dark:text-blue-300 hover:text-blue-800 dark:hover:text-blue-200 rounded-full p-1 transition-colors theme-transition"
                      title="Preview file"
                    >
                      <EyeIcon className="h-3 w-3" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownloadFile(file);
                      }}
                      className="bg-green-100 dark:bg-green-900 hover:bg-green-200 dark:hover:bg-green-800 text-green-600 dark:text-green-300 hover:text-green-800 dark:hover:text-green-200 rounded-full p-1 transition-colors theme-transition"
                      title="Download file"
                    >
                      <ArrowDownTrayIcon className="h-3 w-3" />
                    </button>
                    <span className="px-1.5 py-0.5 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs rounded-full font-medium theme-transition">
                      ✓
                    </span>
                  </div>

                  {/* File Icon */}
                  <div className="flex flex-col items-center justify-center flex-1 space-y-2 mt-2">
                    <div className="relative">
                      <DocumentTextIcon className="h-8 w-8 text-blue-500 dark:text-blue-400 flex-shrink-0 theme-transition" />
                    </div>

                    {/* Filename */}
                    <div className="text-center w-full px-1">
                      <p className="text-xs font-medium text-gray-900 dark:text-gray-100 break-words line-clamp-2 leading-tight theme-transition" title={file.filename}>
                        {file.filename.length > 25 ? `${file.filename.substring(0, 22)}...` : file.filename}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 theme-transition">
                        {formatFileSize(file.size)}
                      </p>
                    </div>

                    {/* Badges */}
                    <div className="flex flex-col space-y-1 items-center">
                      {file.uc_type && file.uc_type !== 'processed' && (
                        <span className={`text-xs font-medium px-2 py-1 rounded-full ${getUCBadgeStyle(file.uc_type)} theme-transition`}>
                          {file.uc_type.toUpperCase()}
                        </span>
                      )}
                      {/* {file.batch_name && (
                        <span className={`text-xs font-medium px-2 py-1 rounded-full ${getBatchBadgeStyle(file.batch_name)} theme-transition`}>
                          {file.batch_name === 'individual' ? 'Individual' : file.batch_name.replace('batch_', 'Batch ')}
                        </span>
                      )} */}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* File Preview Modal */}
      {previewFile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg mx-4 flex flex-col shadow-2xl w-full max-w-6xl h-5/6 theme-transition">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700 flex-shrink-0 theme-transition">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 theme-transition">
                File Preview: {previewFile}
              </h3>
              <button
                onClick={closePreview}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 theme-transition"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Modal Content */}
            <div className="flex-1 overflow-hidden p-6 min-h-0">
              {loadingPreview ? (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-2 text-gray-600 dark:text-gray-400">Loading preview...</span>
                </div>
              ) : previewData ? (
                <div className="space-y-4 h-full flex flex-col">
                  <div className="text-sm text-gray-600 dark:text-gray-400 flex-shrink-0 theme-transition">
                    Showing first 100 rows of {previewData.totalRows} total rows
                  </div>
                  
                  <div className="overflow-auto flex-1 border border-gray-200 dark:border-gray-700 rounded-lg theme-transition">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                      <thead className="bg-gray-50 dark:bg-gray-700 sticky top-0 theme-transition">
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-200 dark:border-gray-700 theme-transition">
                            #
                          </th>
                          {previewData.headers.map((header, index) => (
                            <th
                              key={index}
                              className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-200 dark:border-gray-700 last:border-r-0 theme-transition"
                            >
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700 theme-transition">
                        {previewData.rows.map((row, rowIndex) => (
                          <tr key={rowIndex} className="hover:bg-gray-50 dark:hover:bg-gray-700 theme-transition">
                            <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400 border-r border-gray-200 dark:border-gray-700 theme-transition">
                              {rowIndex + 1}
                            </td>
                            {row.map((cell, cellIndex) => (
                              <td
                                key={cellIndex}
                                className="px-3 py-2 text-xs text-gray-900 dark:text-gray-100 border-r border-gray-200 dark:border-gray-700 last:border-r-0 max-w-xs truncate theme-transition"
                                title={cell}
                              >
                                {cell || '-'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {previewData.totalRows > 100 && (
                    <div className="text-xs text-gray-500 dark:text-gray-400 text-center flex-shrink-0 theme-transition">
                      ... and {previewData.totalRows - 100} more rows
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400 theme-transition">
                  Failed to load preview
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
