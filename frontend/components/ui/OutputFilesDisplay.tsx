'use client';

import { useState } from 'react';
import { 
  EyeIcon, 
  ArrowDownTrayIcon, 
  DocumentTextIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import FilePreviewModal from './FilePreviewModal';

interface OutputFile {
  filename: string;
  path: string;
  size: number;
  created: string;
  status?: 'completed' | 'processing' | 'failed';
  type?: string;
}

interface OutputFilesDisplayProps {
  outputFiles: OutputFile[];
  onPreviewFile: (filename: string) => Promise<{
    headers: string[];
    rows: string[][];
    totalRows: number;
  } | null>;
  onDownloadFile: (filename: string) => Promise<void>;
}

export default function OutputFilesDisplay({
  outputFiles,
  onPreviewFile,
  onDownloadFile
}: OutputFilesDisplayProps) {
  const [previewModal, setPreviewModal] = useState({
    isOpen: false,
    filename: null as string | null,
    loading: false,
    data: null as any
  });
  const [modalSize, setModalSize] = useState({ width: 800, height: 600 });

  const handlePreviewFile = async (filename: string) => {
    setPreviewModal({
      isOpen: true,
      filename,
      loading: true,
      data: null
    });

    try {
      const data = await onPreviewFile(filename);
      setPreviewModal(prev => ({
        ...prev,
        loading: false,
        data
      }));
    } catch (error) {
      console.error('Preview error:', error);
      setPreviewModal(prev => ({
        ...prev,
        loading: false,
        data: null
      }));
    }
  };

  const closePreviewModal = () => {
    setPreviewModal({
      isOpen: false,
      filename: null,
      loading: false,
      data: null
    });
  };

  const handleResizeStart = (e: React.MouseEvent) => {
    const startX = e.clientX;
    const startY = e.clientY;
    const startWidth = modalSize.width;
    const startHeight = modalSize.height;

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.max(400, startWidth + (e.clientX - startX));
      const newHeight = Math.max(300, startHeight + (e.clientY - startY));
      setModalSize({ width: newWidth, height: newHeight });
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-4 h-4 text-green-500 dark:text-green-400" />;
      case 'processing':
        return <ClockIcon className="w-4 h-4 text-blue-500 dark:text-blue-400 animate-pulse" />;
      case 'failed':
        return <ExclamationTriangleIcon className="w-4 h-4 text-red-500 dark:text-red-400" />;
      default:
        return <CheckCircleIcon className="w-4 h-4 text-green-500 dark:text-green-400" />;
    }
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border border-green-200 dark:border-green-700">
            <span className="w-1.5 h-1.5 bg-green-500 dark:bg-green-400 rounded-full mr-1"></span>
            Completed
          </span>
        );
      case 'processing':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 border border-blue-200 dark:border-blue-700">
            <span className="w-1.5 h-1.5 bg-blue-500 dark:bg-blue-400 rounded-full mr-1 animate-pulse"></span>
            Processing
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border border-red-200 dark:border-red-700">
            <span className="w-1.5 h-1.5 bg-red-500 dark:bg-red-400 rounded-full mr-1"></span>
            Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border border-green-200 dark:border-green-700">
            <span className="w-1.5 h-1.5 bg-green-500 dark:bg-green-400 rounded-full mr-1"></span>
            Ready
          </span>
        );
    }
  };

  const getFileTypeIcon = (filename: string) => {
    if (filename.includes('_uc1_') || filename.includes('UC1')) {
      return (
        <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
          <span className="text-xs font-bold text-blue-600 dark:text-blue-400">UC1</span>
        </div>
      );
    } else if (filename.includes('_uc4_') || filename.includes('UC4')) {
      return (
        <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
          <span className="text-xs font-bold text-purple-600 dark:text-purple-400">UC4</span>
        </div>
      );
    }
    return (
      <div className="w-8 h-8 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
        <DocumentTextIcon className="w-4 h-4 text-gray-500 dark:text-gray-400" />
      </div>
    );
  };

  if (outputFiles.length === 0) {
    return (
      <div className="text-center py-8">
        <DocumentTextIcon className="w-12 h-12 mx-auto text-gray-400 dark:text-gray-500 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No output files</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Process some files to see the results here
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {outputFiles.length} file{outputFiles.length !== 1 ? 's' : ''} found
          </p>
          <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
            <div className="flex items-center space-x-1">
              <span className="w-2 h-2 bg-green-500 dark:bg-green-400 rounded-full"></span>
              <span>Completed</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="w-2 h-2 bg-blue-500 dark:bg-blue-400 rounded-full animate-pulse"></span>
              <span>Processing</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="w-2 h-2 bg-red-500 dark:bg-red-400 rounded-full"></span>
              <span>Failed</span>
            </div>
          </div>
        </div>

        {outputFiles.map((file, index) => (
          <div
            key={index}
            className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
          >
            <div className="flex items-center space-x-3 flex-1 min-w-0">
              {getFileTypeIcon(file.filename)}
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {file.filename}
                  </h4>
                  {getStatusBadge(file.status)}
                </div>
                <div className="flex items-center space-x-4 mt-1">
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {formatFileSize(file.size)}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Created {formatDate(file.created)}
                  </span>
                  {file.type && (
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Type: {file.type}
                    </span>
                  )}
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2 ml-4">
              <button
                onClick={() => handlePreviewFile(file.filename)}
                className="p-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md transition-colors"
                title="Preview file"
              >
                <EyeIcon className="w-4 h-4" />
              </button>
              <button
                onClick={() => onDownloadFile(file.filename)}
                className="p-2 text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-md transition-colors"
                title="Download file"
              >
                <ArrowDownTrayIcon className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      <FilePreviewModal
        isOpen={previewModal.isOpen}
        filename={previewModal.filename}
        onClose={closePreviewModal}
        loading={previewModal.loading}
        previewData={previewModal.data}
        modalSize={modalSize}
        onResizeStart={handleResizeStart}
      />
    </>
  );
}
