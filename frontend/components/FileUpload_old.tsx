'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { CloudArrowUpIcon, DocumentIcon, CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import { apiClient } from '@/lib/api';

interface FileUploadProps {
  onJobUpdate: () => void;
}

export default function FileUpload({ onJobUpdate }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
    jobId?: number;
  }>({ type: null, message: '' });
  const [selectedUCs, setSelectedUCs] = useState<string[]>(['UC1', 'UC4']); // Default: both UCs selected

  const toggleUC = (uc: string) => {
    setSelectedUCs(prev => 
      prev.includes(uc) 
        ? prev.filter(u => u !== uc)
        : [...prev, uc]
    );
  };

  const startProcessing = async (jobId: number) => {
    try {
      const response = await apiClient.post(`/jobs/${jobId}/start`);
      setUploadStatus({
        type: 'success',
        message: `Processing started! Job will go through: ${selectedUCs.join(', ')}`,
        jobId
      });
      onJobUpdate(); // Refresh job list to show processing status
    } catch (error: any) {
      setUploadStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Failed to start processing.',
      });
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    if (selectedUCs.length === 0) {
      setUploadStatus({
        type: 'error',
        message: 'Please select at least one analysis type (UC1 or UC4).',
      });
      return;
    }

    setUploading(true);
    setUploadStatus({ type: null, message: '' });

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('selected_ucs', selectedUCs.join(','));

      const response = await apiClient.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadStatus({
        type: 'success',
        message: response.data.message,
        jobId: response.data.job_id,
      });
      
      // Notify parent component to refresh data
      onJobUpdate();
    } catch (error: any) {
      setUploadStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Upload failed. Please try again.',
      });
    } finally {
      setUploading(false);
    }
  }, [selectedUCs, onJobUpdate]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div className="space-y-6">
      {/* UC Selection */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">
          Analysis Types (Select one or more)
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            onClick={() => toggleUC('UC1')}
            className={`p-4 text-left border rounded-lg cursor-pointer transition-colors ${
              selectedUCs.includes('UC1')
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={selectedUCs.includes('UC1')}
                onChange={() => toggleUC('UC1')}
                className="h-4 w-4 text-blue-600 rounded border-gray-300"
              />
              <div>
                <div className="font-medium">UC1 - Sparse Data Analysis</div>
                <div className="text-sm text-gray-600 mt-1">
                  Detect incomplete data and assess data quality
                </div>
              </div>
            </div>
          </div>
          <div
            onClick={() => toggleUC('UC4')}
            className={`p-4 text-left border rounded-lg cursor-pointer transition-colors ${
              selectedUCs.includes('UC4')
                ? 'border-green-500 bg-green-50 text-green-700'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={selectedUCs.includes('UC4')}
                onChange={() => toggleUC('UC4')}
                className="h-4 w-4 text-green-600 rounded border-gray-300"
              />
              <div>
                <div className="font-medium">UC4 - Duplicate Detection</div>
                <div className="text-sm text-gray-600 mt-1">
                  Find and remove duplicate records
                </div>
              </div>
            </div>
          </div>
        </div>
        {selectedUCs.length > 0 && (
          <div className="text-sm text-blue-600 bg-blue-50 p-3 rounded-lg">
            <strong>Selected:</strong> {selectedUCs.join(', ')} 
            <br />
            <span className="text-gray-600">Data will be processed through all selected UCs sequentially.</span>
          </div>
        )}
      </div>

      {/* File Upload Area */}
      <div
        {...getRootProps()}
        className={`file-upload-container border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors max-w-full ${
          isDragActive
            ? 'border-blue-400 bg-blue-50'
            : uploading
            ? 'border-gray-300 bg-gray-50 cursor-not-allowed'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-3 flex flex-col items-center">
          {uploading ? (
            <div className="loading-spinner animate-spin rounded-full border-b-2 border-blue-600"></div>
          ) : (
            <CloudArrowUpIcon className="cloud-upload-icon icon-lg text-gray-400" />
          )}
          
          <div className="max-w-md">
            <p className="text-base font-medium text-gray-900">
              {uploading
                ? 'Uploading...'
                : isDragActive
                ? 'Drop the CSV file here'
                : 'Drop a CSV file here, or click to select'}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              Only CSV files are supported (max 10MB)
            </p>
          </div>
        </div>
      </div>

      {/* Upload Status */}
      {uploadStatus.type && (
        <div
          className={`p-4 rounded-lg flex items-start space-x-3 ${
            uploadStatus.type === 'success'
              ? 'bg-green-50 border border-green-200'
              : 'bg-red-50 border border-red-200'
          }`}
        >
          {uploadStatus.type === 'success' ? (
            <CheckCircleIcon className="h-5 w-5 text-green-500 mt-0.5" />
          ) : (
            <ExclamationCircleIcon className="h-5 w-5 text-red-500 mt-0.5" />
          )}
          <div className="flex-1">
            <p
              className={`text-sm font-medium ${
                uploadStatus.type === 'success' ? 'text-green-800' : 'text-red-800'
              }`}
            >
              {uploadStatus.message}
            </p>
            {uploadStatus.type === 'success' && uploadStatus.jobId && (
              <div className="mt-3 flex space-x-3">
                <button
                  onClick={() => startProcessing(uploadStatus.jobId!)}
                  className="btn-primary text-sm py-1 px-3"
                >
                  Start Processing
                </button>
                <span className="text-xs text-gray-600 self-center">
                  Job ID: {uploadStatus.jobId}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Help Text */}
      <div className="text-sm text-gray-600">
        <p className="font-medium mb-2">Analysis Types:</p>
        <ul className="space-y-1 ml-4">
          <li>• <strong>UC1:</strong> Analyzes data completeness, missing values, and quality scores</li>
          <li>• <strong>UC4:</strong> Detects and removes duplicate records, generates cleaned files</li>
        </ul>
      </div>
    </div>
  );
}
