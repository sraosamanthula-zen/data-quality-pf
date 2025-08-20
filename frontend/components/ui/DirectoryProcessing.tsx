'use client';

import { useState } from 'react';
import { FolderIcon } from '@heroicons/react/24/outline';

interface DirectoryProcessingProps {
  directoryPath: string;
  setDirectoryPath: (path: string) => void;
  isProcessing: boolean;
  processDirectory: () => Promise<void>;
}

export default function DirectoryProcessing({
  directoryPath,
  setDirectoryPath,
  isProcessing,
  processDirectory
}: DirectoryProcessingProps) {
  const [errors, setErrors] = useState<string[]>([]);

  const handleProcessDirectory = async () => {
    setErrors([]);
    try {
      await processDirectory();
    } catch (error) {
      console.error('Directory processing error:', error);
      setErrors(['Failed to process directory. Please check the path and try again.']);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Directory Path
        </label>
        <div className="flex space-x-2">
          <div className="relative flex-1">
            <FolderIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={directoryPath}
              onChange={(e) => setDirectoryPath(e.target.value)}
              placeholder="Enter directory path..."
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
              disabled={isProcessing}
            />
          </div>
          <button
            onClick={handleProcessDirectory}
            disabled={!directoryPath.trim() || isProcessing}
            className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              !directoryPath.trim() || isProcessing
                ? 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white'
            }`}
          >
            {isProcessing ? 'Processing...' : 'Process Directory'}
          </button>
        </div>
      </div>

      {errors.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-3">
          <div className="text-sm text-red-600 dark:text-red-400">
            {errors.map((error, index) => (
              <div key={index}>{error}</div>
            ))}
          </div>
        </div>
      )}

      <div className="text-xs text-gray-600 dark:text-gray-400">
        <p>Process all CSV files in the specified directory for data quality analysis.</p>
        <p className="mt-1">Supported operations: UC1 (Incomplete Data) and UC4 (Duplicate Records)</p>
      </div>
    </div>
  );
}
