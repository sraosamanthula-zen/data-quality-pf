'use client';

import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { CloudArrowUpIcon, DocumentIcon, CheckCircleIcon, ExclamationCircleIcon, FolderIcon, PlayIcon } from '@heroicons/react/24/outline';
import { apiClient } from '@/lib/api';

interface FileUploadProps {
  onJobUpdate: () => void;
}

interface DirectoryFile {
  name: string;
  processed: boolean;
  size?: number;
  lastModified?: string;
}

export default function FileUpload({ onJobUpdate }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
    jobId?: number;
  }>({ type: null, message: '' });
  const [selectedUCs, setSelectedUCs] = useState<string[]>(['UC1', 'UC4']); // Default: both UCs selected
  const [referenceFile, setReferenceFile] = useState<string | null>(null);
  const [directoryFiles, setDirectoryFiles] = useState<DirectoryFile[]>([]);
  const [processingBatch, setProcessingBatch] = useState(false);
  const [batchStatus, setBatchStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
  }>({ type: null, message: '' });

  // Fetch directory files on component mount
  useEffect(() => {
    fetchDirectoryFiles();
  }, []);

  const fetchDirectoryFiles = async () => {
    try {
      const response = await apiClient.get('/directory-files');
      setDirectoryFiles(response.data.files || []);
    } catch (error) {
      console.error('Error fetching directory files:', error);
    }
  };

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

  const startBatchProcessing = async () => {
    if (selectedUCs.length === 0) {
      setBatchStatus({
        type: 'error',
        message: 'Please select at least one analysis type (UC1 or UC4).',
      });
      return;
    }

    setProcessingBatch(true);
    setBatchStatus({ type: null, message: '' });

    try {
      const response = await apiClient.post('/batch-process', {
        selected_ucs: selectedUCs.join(','),
        reference_file: referenceFile
      });

      setBatchStatus({
        type: 'success',
        message: `Batch processing started for ${response.data.files.length} files with UCs: ${selectedUCs.join(', ')}`,
      });
      
      // Refresh directory files and job list
      fetchDirectoryFiles();
      onJobUpdate();
    } catch (error: any) {
      setBatchStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Batch processing failed. Please try again.',
      });
    } finally {
      setProcessingBatch(false);
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setUploadStatus({ type: null, message: '' });

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('is_reference', 'true');
      formData.append('selected_ucs', selectedUCs.join(','));

      const response = await apiClient.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setReferenceFile(file.name);
      setUploadStatus({
        type: 'success',
        message: `Reference file "${file.name}" uploaded successfully. Ready for batch processing.`,
        jobId: response.data.job_id,
      });
      
      // Refresh directory files and notify parent
      fetchDirectoryFiles();
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
      <div>
        <h3 className="text-sm font-medium text-gray-900 mb-3">
          Analysis Types (Select one or more)
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <label className="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-blue-50 transition-colors">
            <input
              type="checkbox"
              checked={selectedUCs.includes('UC1')}
              onChange={() => toggleUC('UC1')}
              className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <div>
              <h4 className="text-sm font-medium text-blue-900">UC1 - Sparse Data Analysis</h4>
              <p className="text-xs text-gray-600">Detect incomplete data and assess data quality compared to reference</p>
            </div>
          </label>
          <label className="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-green-50 transition-colors">
            <input
              type="checkbox"
              checked={selectedUCs.includes('UC4')}
              onChange={() => toggleUC('UC4')}
              className="mt-1 h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
            />
            <div>
              <h4 className="text-sm font-medium text-green-900">UC4 - Duplicate Detection</h4>
              <p className="text-xs text-gray-600">Find and remove duplicate records, generates cleaned files</p>
            </div>
          </label>
        </div>
        <div className="mt-2 text-xs text-blue-600">
          Selected: {selectedUCs.join(', ')}
          <br />
          Data will be processed through all selected UCs sequentially.
        </div>
      </div>

      {/* Reference File Upload */}
      <div>
        <h3 className="text-sm font-medium text-gray-900 mb-2">
          Upload Reference File
        </h3>
        <p className="text-xs text-gray-600 mb-4">
          Upload a high-quality CSV file that will serve as the reference standard for data quality analysis.
        </p>
        
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-blue-400 bg-blue-50'
              : uploading
              ? 'border-gray-300 bg-gray-50 cursor-not-allowed'
              : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
          }`}
        >
          <input {...getInputProps()} />
          <div className="space-y-2">
            {uploading ? (
              <>
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-sm text-gray-600">Uploading reference file...</p>
              </>
            ) : isDragActive ? (
              <>
                <CloudArrowUpIcon className="h-8 w-8 text-blue-500 mx-auto" />
                <p className="text-sm text-blue-600">Drop the reference file here</p>
              </>
            ) : (
              <>
                <DocumentIcon className="h-8 w-8 text-gray-400 mx-auto" />
                <p className="text-sm text-gray-600">
                  Drop a CSV reference file here, or click to select
                </p>
                <p className="text-xs text-gray-500">Only CSV files are supported (max 10MB)</p>
              </>
            )}
          </div>
        </div>

        {/* Upload Status */}
        {uploadStatus.type && (
          <div className={`mt-4 p-3 rounded-md ${
            uploadStatus.type === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}>
            <div className="flex items-center space-x-2">
              {uploadStatus.type === 'success' ? (
                <CheckCircleIcon className="h-5 w-5 text-green-500 status-icon" />
              ) : (
                <ExclamationCircleIcon className="h-5 w-5 text-red-500 status-icon" />
              )}
              <span className={`text-sm ${
                uploadStatus.type === 'success' ? 'text-green-800' : 'text-red-800'
              }`}>
                {uploadStatus.message}
              </span>
            </div>
            {uploadStatus.type === 'success' && uploadStatus.jobId && (
              <button
                onClick={() => startProcessing(uploadStatus.jobId!)}
                className="mt-2 px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition-colors"
              >
                Process Reference File
              </button>
            )}
          </div>
        )}
      </div>

      {/* Directory Files & Batch Processing */}
      {referenceFile && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-900">
              Directory Files ({directoryFiles.length} files found)
            </h3>
            <button
              onClick={startBatchProcessing}
              disabled={processingBatch || selectedUCs.length === 0}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              <PlayIcon className="h-4 w-4" />
              <span>{processingBatch ? 'Processing...' : 'Start Batch Processing'}</span>
            </button>
          </div>

          {/* Files List */}
          <div className="border rounded-lg bg-gray-50 max-h-60 overflow-y-auto">
            {directoryFiles.length > 0 ? (
              <div className="divide-y divide-gray-200">
                {directoryFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-3 hover:bg-gray-100">
                    <div className="flex items-center space-x-3">
                      <DocumentIcon className="h-5 w-5 text-gray-400 status-icon" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{file.name}</p>
                        {file.size && (
                          <p className="text-xs text-gray-500">
                            {(file.size / 1024).toFixed(1)} KB
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {file.processed ? (
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                          Processed
                        </span>
                      ) : (
                        <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                          Pending
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 text-center text-gray-500 text-sm">
                <FolderIcon className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                No CSV files found in directory
              </div>
            )}
          </div>

          {/* Batch Status */}
          {batchStatus.type && (
            <div className={`mt-4 p-3 rounded-md ${
              batchStatus.type === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
            }`}>
              <div className="flex items-center space-x-2">
                {batchStatus.type === 'success' ? (
                  <CheckCircleIcon className="h-5 w-5 text-green-500 status-icon" />
                ) : (
                  <ExclamationCircleIcon className="h-5 w-5 text-red-500 status-icon" />
                )}
                <span className={`text-sm ${
                  batchStatus.type === 'success' ? 'text-green-800' : 'text-red-800'
                }`}>
                  {batchStatus.message}
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
