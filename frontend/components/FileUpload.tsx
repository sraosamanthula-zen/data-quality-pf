'use client';

import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { CloudArrowUpIcon, DocumentIcon, CheckCircleIcon, ExclamationCircleIcon, FolderIcon, PlayIcon, CogIcon, EyeIcon, XMarkIcon } from '@heroicons/react/24/outline';
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

interface ReferenceFile {
  id: number;
  uc_type: string;
  filename: string;
  file_path?: string;
  description: string;
  created_at: string;
}

interface PlatformConfig {
  data_directory: string;
  uploads_directory: string;
  reference_files_directory: string;
  storage_directory: string;
  result_suffix: string;
  batch_processing_enabled: boolean;
}

export default function FileUpload({ onJobUpdate }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
    jobId?: number;
  }>({ type: null, message: '' });
  const [selectedUCs, setSelectedUCs] = useState<string[]>(['UC1', 'UC4']); // Default: both UCs selected
  const [referenceFiles, setReferenceFiles] = useState<{[key: string]: ReferenceFile | null}>({
    UC1: null,
    UC4: null
  });
  const [directoryFiles, setDirectoryFiles] = useState<DirectoryFile[]>([]);
  const [directoryPath, setDirectoryPath] = useState<string>('');
  const [customDirectory, setCustomDirectory] = useState<string>('');
  const [processingBatch, setProcessingBatch] = useState(false);
  const [batchStatus, setBatchStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
  }>({ type: null, message: '' });
  const [uploadingRefFile, setUploadingRefFile] = useState<string | null>(null);
  const [config, setConfig] = useState<PlatformConfig | null>(null);
  const [showHistory, setShowHistory] = useState<string | null>(null);
  const [referenceHistory, setReferenceHistory] = useState<{[key: string]: any}>({});
  const [previewFile, setPreviewFile] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<{
    headers: string[];
    rows: string[][];
    totalRows: number;
  } | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [modalSize, setModalSize] = useState({ width: 1200, height: 600 });
  const [isResizing, setIsResizing] = useState(false);
  const [resizeStartPos, setResizeStartPos] = useState({ x: 0, y: 0 });
  const [resizeStartSize, setResizeStartSize] = useState({ width: 0, height: 0 });

  // Fetch configuration, directory files, and reference files on component mount
  useEffect(() => {
    fetchConfig();
    fetchReferenceFiles();
  }, []);

  // Fetch directory files when directory path changes
  useEffect(() => {
    if (directoryPath) {
      fetchDirectoryFiles(directoryPath);
    }
  }, [directoryPath]);

  const fetchConfig = async () => {
    try {
      const response = await apiClient.get('/config');
      const configData = response.data;
      setConfig(configData);
      setDirectoryPath(configData.data_directory);
      setCustomDirectory(configData.data_directory);
    } catch (error) {
      console.error('Error fetching config:', error);
    }
  };

  const fetchDirectoryFiles = async (directory?: string) => {
    try {
      const queryParam = directory ? `?directory=${encodeURIComponent(directory)}` : '';
      const response = await apiClient.get(`/upload/directory-files${queryParam}`);
      setDirectoryFiles(response.data.files || []);
      if (!directory) {
        setDirectoryPath(response.data.directory);
        setCustomDirectory(response.data.directory);
      }
    } catch (error) {
      console.error('Error fetching directory files:', error);
      setDirectoryFiles([]);
    }
  };

  const fetchReferenceFiles = async () => {
    try {
      const response = await apiClient.get('/upload/reference-files');
      const refFiles = response.data.reference_files || [];
      
      // Organize reference files by UC type
      const refFilesByUC: {[key: string]: ReferenceFile | null} = { UC1: null, UC4: null };
      refFiles.forEach((ref: ReferenceFile) => {
        refFilesByUC[ref.uc_type] = ref;
      });
      setReferenceFiles(refFilesByUC);
    } catch (error) {
      console.error('Error fetching reference files:', error);
    }
  };

  const toggleUC = (uc: string) => {
    setSelectedUCs(prev => 
      prev.includes(uc) 
        ? prev.filter(u => u !== uc)
        : [...prev, uc]
    );
  };

  const handleDirectoryChange = async () => {
    if (!customDirectory.trim()) {
      setBatchStatus({
        type: 'error',
        message: 'Please enter a valid directory path.',
      });
      return;
    }

    try {
      // Validate the directory
      const response = await apiClient.post('/upload/set-directory', {
        directory_path: customDirectory
      });
      
      setDirectoryPath(customDirectory);
      setBatchStatus({
        type: 'success',
        message: `Directory validated: ${response.data.csv_files_count} CSV files found`,
      });
      
      // Fetch files from new directory
      fetchDirectoryFiles(customDirectory);
    } catch (error: any) {
      setBatchStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Failed to validate directory',
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

    // Check if selected UCs have reference files
    const missingRefFiles = selectedUCs.filter(uc => !referenceFiles[uc]);
    if (missingRefFiles.length > 0) {
      setBatchStatus({
        type: 'error',
        message: `Please upload reference files for: ${missingRefFiles.join(', ')}`,
      });
      return;
    }

    setProcessingBatch(true);
    setBatchStatus({ type: null, message: '' });

    try {
      const response = await apiClient.post('/batch/process-directory', {
        directory_path: directoryPath,
        selected_ucs: selectedUCs,
        reference_file_paths: Object.fromEntries(
          selectedUCs.map(uc => [uc, referenceFiles[uc]?.filename])
        )
      });

      setBatchStatus({
        type: 'success',
        message: `Batch processing started for ${response.data.total_files || 'multiple'} files with UCs: ${selectedUCs.join(', ')}`,
      });
      
      // Refresh directory files and job list
      fetchDirectoryFiles(directoryPath);
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

  const uploadReferenceFile = async (file: File, ucType: string) => {
    setUploadingRefFile(ucType);
    setUploadStatus({ type: null, message: '' });

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('uc_type', ucType);
      formData.append('description', `Reference file for ${ucType}`);

      const response = await apiClient.post('/upload/reference-file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Update the reference files state
      setReferenceFiles(prev => ({
        ...prev,
        [ucType]: {
          id: response.data.id,
          uc_type: ucType,
          filename: file.name,
          description: `Reference file for ${ucType}`,
          created_at: new Date().toISOString()
        }
      }));

      setUploadStatus({
        type: 'success',
        message: `Reference file for ${ucType} uploaded successfully: "${file.name}"`,
      });
      
      // Refresh reference files
      fetchReferenceFiles();
    } catch (error: any) {
      setUploadStatus({
        type: 'error',
        message: error.response?.data?.detail || `Failed to upload reference file for ${ucType}`,
      });
    } finally {
      setUploadingRefFile(null);
    }
  };

  // Handle replace reference file - trigger file input
  const handleOverride = (ucType: string) => {
    const fileInput = document.getElementById(`${ucType}-replace-input`) as HTMLInputElement;
    if (fileInput) {
      fileInput.click();
    }
  };

  // Handle file selection for replacement
  const handleReplaceFileSelect = async (event: React.ChangeEvent<HTMLInputElement>, ucType: string) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.name.endsWith('.csv')) {
      setUploadStatus({
        type: 'error',
        message: 'Please select a CSV file',
      });
      return;
    }

    try {
      setUploadingRefFile(ucType);
      
      // First remove the existing reference file
      await apiClient.delete(`/upload/reference-file/${ucType}`);
      
      // Then upload the new file
      const formData = new FormData();
      formData.append('file', file);
      formData.append('uc_type', ucType);

      const response = await apiClient.post('/upload/reference-file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setReferenceFiles(prev => ({
        ...prev,
        [ucType]: response.data
      }));

      setUploadStatus({
        type: 'success',
        message: `${ucType} reference file replaced successfully`,
      });

      // Clear the file input
      event.target.value = '';
      
    } catch (error: any) {
      setUploadStatus({
        type: 'error',
        message: error.response?.data?.detail || `Failed to replace ${ucType} reference file`,
      });
    } finally {
      setUploadingRefFile(null);
    }
  };

  const fetchReferenceHistory = async (ucType: string) => {
    try {
      const response = await apiClient.get(`/upload/reference-file/${ucType}/history`);
      setReferenceHistory(prev => ({
        ...prev,
        [ucType]: response.data
      }));
      setShowHistory(ucType);
    } catch (error) {
      console.error(`Error fetching ${ucType} history:`, error);
    }
  };

  const closeHistory = () => {
    setShowHistory(null);
  };

  const handlePreviewFile = async (filename: string) => {
    setLoadingPreview(true);
    setPreviewFile(filename);
    
    try {
      const response = await apiClient.get(`/upload/preview-file`, {
        params: {
          filename: filename,
          directory: directoryPath
        }
      });
      
      setPreviewData(response.data);
    } catch (error: any) {
      console.error('Error previewing file:', error);
      setUploadStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Failed to preview file',
      });
    } finally {
      setLoadingPreview(false);
    }
  };

  const closePreview = () => {
    setPreviewFile(null);
    setPreviewData(null);
  };

  const handleResizeStart = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    setResizeStartPos({ x: e.clientX, y: e.clientY });
    setResizeStartSize({ width: modalSize.width, height: modalSize.height });
  };

  const handleResizeMove = useCallback((e: MouseEvent) => {
    if (!isResizing) return;
    
    const deltaX = e.clientX - resizeStartPos.x;
    const deltaY = e.clientY - resizeStartPos.y;
    
    const newWidth = Math.max(400, Math.min(window.innerWidth - 100, resizeStartSize.width + deltaX));
    const newHeight = Math.max(300, Math.min(window.innerHeight - 100, resizeStartSize.height + deltaY));
    
    setModalSize({ width: newWidth, height: newHeight });
  }, [isResizing, resizeStartPos, resizeStartSize]);

  const handleResizeEnd = useCallback(() => {
    setIsResizing(false);
  }, []);

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleResizeMove);
      document.addEventListener('mouseup', handleResizeEnd);
      document.body.style.cursor = 'nw-resize';
      document.body.style.userSelect = 'none';
      
      return () => {
        document.removeEventListener('mousemove', handleResizeMove);
        document.removeEventListener('mouseup', handleResizeEnd);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      };
    }
  }, [isResizing, handleResizeMove, handleResizeEnd]);

  const createUCDropzone = (ucType: string) => {
    const { getRootProps, getInputProps, isDragActive } = useDropzone({
      onDrop: (files) => {
        if (files[0]) uploadReferenceFile(files[0], ucType);
      },
      accept: {
        'text/csv': ['.csv'],
      },
      maxFiles: 1,
      disabled: uploadingRefFile === ucType,
    });

    return { getRootProps, getInputProps, isDragActive };
  };

  return (
    <div className="space-y-6">
      {/* Configuration Display */}
      {config && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 shadow-sm">
          <div className="flex items-center space-x-2 mb-3">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <CogIcon className="h-4 w-4 text-blue-600" />
            </div>
            <h3 className="text-sm font-medium text-blue-900">Platform Configuration</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="bg-white bg-opacity-60 rounded-md p-3 border border-blue-100">
              <div className="text-xs font-medium text-blue-800 mb-1">Storage Directory</div>
              <div className="text-xs text-blue-700 font-mono break-all">{config.storage_directory}</div>
            </div>
            <div className="bg-white bg-opacity-60 rounded-md p-3 border border-blue-100">
              <div className="text-xs font-medium text-blue-800 mb-1">Result Suffix</div>
              <div className="text-xs text-blue-700 font-mono">{config.result_suffix}</div>
            </div>
          </div>
        </div>
      )}

      {/* UC Selection with Reference File Upload */}
      <div>
        <h3 className="text-sm font-medium text-gray-900 mb-3">
          Analysis Types & Reference Files
        </h3>
        <p className="text-xs text-gray-600 mb-4">
          Select analysis types and upload corresponding reference files. Reference files will be shown below each UC until a new one is uploaded.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* UC1 */}
          <div className="border rounded-lg p-4">
            <label className="flex items-start space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedUCs.includes('UC1')}
                onChange={() => toggleUC('UC1')}
                className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <div className="flex-1">
                <h4 className="text-sm font-medium text-blue-900">UC1 - Sparse Data Analysis</h4>
                <p className="text-xs text-gray-600 mb-3">Detect incomplete data and assess data quality</p>
                
                {/* Reference File Status/Upload */}
                {referenceFiles.UC1 ? (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <CheckCircleIcon className="h-4 w-4 text-green-500" />
                        <span className="text-xs text-green-800 font-medium">{referenceFiles.UC1.filename}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => fetchReferenceHistory('UC1')}
                          className="text-gray-600 hover:text-gray-800 p-1 rounded hover:bg-gray-100"
                          title="View History"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleOverride('UC1')}
                          className="text-blue-600 hover:text-blue-800 p-1 rounded hover:bg-blue-50"
                          title="Replace File"
                          disabled={uploadingRefFile === 'UC1'}
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                        </button>
                      </div>
                    </div>
                    <p className="text-xs text-green-600 mt-1">
                      {uploadingRefFile === 'UC1' ? 'Replacing file...' : 'Reference file ready'}
                    </p>
                    {/* Hidden file input for replacement */}
                    <input
                      id="UC1-replace-input"
                      type="file"
                      accept=".csv"
                      onChange={(e) => handleReplaceFileSelect(e, 'UC1')}
                      className="hidden"
                    />
                  </div>
                ) : (
                  <ReferenceFileDropzone ucType="UC1" createDropzone={createUCDropzone} isUploading={uploadingRefFile === 'UC1'} />
                )}
              </div>
            </label>
          </div>

          {/* UC4 */}
          <div className="border rounded-lg p-4">
            <label className="flex items-start space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedUCs.includes('UC4')}
                onChange={() => toggleUC('UC4')}
                className="mt-1 h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
              />
              <div className="flex-1">
                <h4 className="text-sm font-medium text-green-900">UC4 - Duplicate Detection</h4>
                <p className="text-xs text-gray-600 mb-3">Find and remove duplicate records</p>
                
                {/* Reference File Status/Upload */}
                {referenceFiles.UC4 ? (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <CheckCircleIcon className="h-4 w-4 text-green-500" />
                        <span className="text-xs text-green-800 font-medium">{referenceFiles.UC4.filename}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => fetchReferenceHistory('UC4')}
                          className="text-gray-600 hover:text-gray-800 p-1 rounded hover:bg-gray-100"
                          title="View History"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleOverride('UC4')}
                          className="text-blue-600 hover:text-blue-800 p-1 rounded hover:bg-blue-50"
                          title="Replace File"
                          disabled={uploadingRefFile === 'UC4'}
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                        </button>
                      </div>
                    </div>
                    <p className="text-xs text-green-600 mt-1">
                      {uploadingRefFile === 'UC4' ? 'Replacing file...' : 'Reference file ready'}
                    </p>
                    {/* Hidden file input for replacement */}
                    <input
                      id="UC4-replace-input"
                      type="file"
                      accept=".csv"
                      onChange={(e) => handleReplaceFileSelect(e, 'UC4')}
                      className="hidden"
                    />
                  </div>
                ) : (
                  <ReferenceFileDropzone ucType="UC4" createDropzone={createUCDropzone} isUploading={uploadingRefFile === 'UC4'} />
                )}
              </div>
            </label>
          </div>
        </div>

        <div className="mt-3 text-xs text-blue-600">
          Selected UCs: {selectedUCs.length > 0 ? selectedUCs.join(', ') : 'None selected'}
        </div>
      </div>

      {/* Upload Status */}
      {uploadStatus.type && (
        <div className={`p-3 rounded-md ${
          uploadStatus.type === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        }`}>
          <div className="flex items-center space-x-2">
            {uploadStatus.type === 'success' ? (
              <CheckCircleIcon className="h-5 w-5 text-green-500" />
            ) : (
              <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
            )}
            <span className={`text-sm ${
              uploadStatus.type === 'success' ? 'text-green-800' : 'text-red-800'
            }`}>
              {uploadStatus.message}
            </span>
          </div>
        </div>
      )}

      {/* Directory Input & Batch Processing */}
      <div>
        <h3 className="text-sm font-medium text-gray-900 mb-3">
          Directory Processing
        </h3>
        
        {/* Directory Input */}
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Directory Path</label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={customDirectory}
                onChange={(e) => setCustomDirectory(e.target.value)}
                placeholder="Enter directory path or use default from environment"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                onClick={handleDirectoryChange}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Set Directory
              </button>
            </div>
            {config && (
              <p className="text-xs text-gray-500 mt-1">
                Default: {config.data_directory}
              </p>
            )}
          </div>

          {/* Directory Files & Processing */}
          {directoryPath && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">
                    Files in Directory ({directoryFiles.length} files found)
                  </h4>
                  <p className="text-xs text-gray-600">{directoryPath}</p>
                </div>
                <button
                  onClick={startBatchProcessing}
                  disabled={processingBatch || selectedUCs.length === 0 || directoryFiles.length === 0}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  <PlayIcon className="h-4 w-4" />
                  <span>{processingBatch ? 'Processing...' : 'Start Processing'}</span>
                </button>
              </div>

              {/* Files List - Tile Layout */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-3 max-h-96 overflow-y-auto p-4 bg-gray-50 rounded-lg">
                {directoryFiles.length > 0 ? (
                  directoryFiles.map((file, index) => (
                    <div key={index} className="bg-white rounded-lg border border-gray-200 p-3 hover:shadow-md transition-shadow duration-200 relative min-h-[120px] flex flex-col">
                      {/* Status and Preview Icons */}
                      <div className="absolute top-2 right-2 z-10 flex items-center space-x-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handlePreviewFile(file.name);
                          }}
                          className="bg-blue-100 hover:bg-blue-200 text-blue-600 hover:text-blue-800 rounded-full p-1 transition-colors"
                          title="Preview file"
                        >
                          <EyeIcon className="h-3 w-3" />
                        </button>
                        {file.processed ? (
                          <span className="px-1.5 py-0.5 bg-green-100 text-green-800 text-xs rounded-full font-medium">
                            ✓
                          </span>
                        ) : (
                          <span className="px-1.5 py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded-full font-medium">
                            •
                          </span>
                        )}
                      </div>

                      {/* File Icon */}
                      <div className="flex flex-col items-center justify-center flex-1 space-y-2 mt-2">
                        <div className="relative">
                          <DocumentIcon className="h-8 w-8 text-blue-500 flex-shrink-0" />
                        </div>

                        {/* Filename */}
                        <div className="text-center w-full px-1">
                          <p className="text-xs font-medium text-gray-900 break-words line-clamp-2 leading-tight" title={file.name}>
                            {file.name.length > 25 ? `${file.name.substring(0, 22)}...` : file.name}
                          </p>
                          {file.size && (
                            <p className="text-xs text-gray-500 mt-1">
                              {(file.size / 1024).toFixed(1)} KB
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="col-span-full flex flex-col items-center justify-center py-12 text-center">
                    <FolderIcon className="h-12 w-12 text-gray-400 mb-4" />
                    <p className="text-gray-500 text-sm">No CSV files found in directory</p>
                  </div>
                )}
              </div>
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
                <CheckCircleIcon className="h-5 w-5 text-green-500" />
              ) : (
                <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
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

      {/* File Preview Modal */}
      {previewFile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div 
            className="bg-white rounded-lg mx-4 flex flex-col shadow-2xl relative"
            style={{ 
              width: `${modalSize.width}px`, 
              height: `${modalSize.height}px`,
              maxWidth: '95vw',
              maxHeight: '95vh'
            }}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 flex-shrink-0">
              <h3 className="text-lg font-medium text-gray-900">
                File Preview: {previewFile}
              </h3>
              <button
                onClick={closePreview}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
            
            {/* Modal Content */}
            <div className="flex-1 overflow-hidden p-6 min-h-0">
              {loadingPreview ? (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-2 text-gray-600">Loading preview...</span>
                </div>
              ) : previewData ? (
                <div className="space-y-4 h-full flex flex-col">
                  <div className="text-sm text-gray-600 flex-shrink-0">
                    Showing first 100 rows of {previewData.totalRows} total rows
                  </div>
                  
                  <div className="overflow-auto flex-1 border border-gray-200 rounded-lg">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">
                            #
                          </th>
                          {previewData.headers.map((header, index) => (
                            <th
                              key={index}
                              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 last:border-r-0"
                            >
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {previewData.rows.map((row, rowIndex) => (
                          <tr key={rowIndex} className="hover:bg-gray-50">
                            <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500 border-r border-gray-200">
                              {rowIndex + 1}
                            </td>
                            {row.map((cell, cellIndex) => (
                              <td
                                key={cellIndex}
                                className="px-3 py-2 text-xs text-gray-900 border-r border-gray-200 last:border-r-0 max-w-xs truncate"
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
                    <div className="text-xs text-gray-500 text-center flex-shrink-0">
                      ... and {previewData.totalRows - 100} more rows
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  Failed to load preview
                </div>
              )}
            </div>

            {/* Resize Handle */}
            <div
              className="absolute bottom-0 right-0 w-4 h-4 cursor-nw-resize bg-gray-300 hover:bg-gray-400 transition-colors"
              style={{
                background: 'linear-gradient(-45deg, transparent 0%, transparent 30%, #9CA3AF 30%, #9CA3AF 40%, transparent 40%, transparent 60%, #9CA3AF 60%, #9CA3AF 70%, transparent 70%)',
                borderBottomRightRadius: '0.5rem'
              }}
              onMouseDown={handleResizeStart}
              title="Drag to resize"
            />
          </div>
        </div>
      )}

      {/* Reference File History Modal */}
      {showHistory && referenceHistory[showHistory] && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                {showHistory} Reference File History
              </h3>
              <button
                onClick={closeHistory}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="space-y-3">
              <div className="text-sm text-gray-600 mb-3">
                Total uploads: {referenceHistory[showHistory].total_uploads} | 
                Active: {referenceHistory[showHistory].active_count}
              </div>
              
              {referenceHistory[showHistory].history.map((file: any, index: number) => (
                <div
                  key={file.id}
                  className={`p-3 rounded-lg border ${
                    file.is_active 
                      ? 'bg-green-50 border-green-200' 
                      : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {file.is_active ? (
                        <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      ) : (
                        <div className="h-4 w-4 rounded-full bg-gray-300"></div>
                      )}
                      <span className={`text-sm font-medium ${
                        file.is_active ? 'text-green-800' : 'text-gray-600'
                      }`}>
                        {file.filename}
                      </span>
                      {file.is_active && (
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                          Current
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-gray-500">
                      {new Date(file.created_at).toLocaleDateString()} {new Date(file.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 mt-1">{file.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Helper component for reference file dropzone
interface ReferenceFileDropzoneProps {
  ucType: string;
  createDropzone: (ucType: string) => {
    getRootProps: () => any;
    getInputProps: () => any;
    isDragActive: boolean;
  };
  isUploading: boolean;
  isReplacement?: boolean;
}

function ReferenceFileDropzone({ ucType, createDropzone, isUploading, isReplacement = false }: ReferenceFileDropzoneProps) {
  const { getRootProps, getInputProps, isDragActive } = createDropzone(ucType);
  
  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-3 text-center cursor-pointer transition-colors ${
        isDragActive
          ? 'border-blue-400 bg-blue-50'
          : isUploading
          ? 'border-gray-300 bg-gray-50 cursor-not-allowed'
          : isReplacement
          ? 'border-orange-300 hover:border-orange-400 hover:bg-orange-50 bg-orange-25'
          : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
      }`}
    >
      <input {...getInputProps()} />
      <div className="space-y-1">
        {isUploading ? (
          <>
            <CloudArrowUpIcon className="h-5 w-5 text-gray-400 mx-auto animate-pulse" />
            <p className="text-xs text-gray-500">Uploading...</p>
          </>
        ) : isDragActive ? (
          <>
            <CloudArrowUpIcon className="h-5 w-5 text-blue-500 mx-auto" />
            <p className="text-xs text-blue-600">Drop {ucType} reference file here</p>
          </>
        ) : (
          <>
            <DocumentIcon className={`h-5 w-5 mx-auto ${isReplacement ? 'text-orange-400' : 'text-gray-400'}`} />
            <p className={`text-xs ${isReplacement ? 'text-orange-600' : 'text-gray-600'}`}>
              {isReplacement ? `Replace ${ucType} reference file` : `Drop or click to upload ${ucType} reference file`}
            </p>
            <p className="text-xs text-gray-500">CSV files only</p>
          </>
        )}
      </div>
    </div>
  );
}
