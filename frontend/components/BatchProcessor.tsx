'use client';

import { useState } from 'react';
import { 
  FolderIcon, 
  PlayIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { apiClient } from '@/lib/api';

interface BatchProcessorProps {
  onJobUpdate: () => void;
}

export default function BatchProcessor({ onJobUpdate }: BatchProcessorProps) {
  const [selectedUCs, setSelectedUCs] = useState<string[]>(['UC1', 'UC4']);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const availableUCs = [
    {
      id: 'UC1',
      name: 'Sparse Data Analysis',
      description: 'Detect incomplete data and assess data quality'
    },
    {
      id: 'UC4',
      name: 'Duplicate Detection',
      description: 'Find and remove duplicate records, generates cleaned files'
    }
  ];

  const toggleUC = (ucId: string) => {
    setSelectedUCs(prev => 
      prev.includes(ucId) 
        ? prev.filter(id => id !== ucId)
        : [...prev, ucId]
    );
  };

  const handleBatchProcess = async () => {
    if (selectedUCs.length === 0) {
      setError('Please select at least one UC to process');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setResult(null);

    try {
      const response = await apiClient.post('/batch-process', null, {
        params: {
          selected_ucs: selectedUCs.join(',')
        }
      });
      
      setResult(response.data);
      onJobUpdate(); // Refresh the jobs list
      
    } catch (error: any) {
      console.error('Batch processing error:', error);
      setError(error.response?.data?.detail || 'Failed to start batch processing');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Directory Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <FolderIcon className="h-5 w-5 text-blue-500 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-medium text-blue-900">
              Batch Processing Configuration
            </h3>
            <p className="text-sm text-blue-700 mt-1">
              Process all CSV files in the configured data directory. Processed files will be saved 
              with the "_processed" suffix in the same directory.
            </p>
            <p className="text-xs text-blue-600 mt-2">
              Directory: <code className="bg-blue-100 px-1 rounded">.</code>
            </p>
          </div>
        </div>
      </div>

      {/* UC Selection */}
      <div>
        <h3 className="text-sm font-medium text-gray-900 mb-3">
          Analysis Types (Select one or more)
        </h3>
        <div className="space-y-3">
          {availableUCs.map((uc) => (
            <div key={uc.id} className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  id={uc.id}
                  type="checkbox"
                  checked={selectedUCs.includes(uc.id)}
                  onChange={() => toggleUC(uc.id)}
                  className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                />
              </div>
              <div className="ml-3">
                <label htmlFor={uc.id} className="text-sm font-medium text-gray-700">
                  {uc.name}
                </label>
                <p className="text-sm text-gray-500">{uc.description}</p>
              </div>
            </div>
          ))}
        </div>

        {selectedUCs.length > 0 && (
          <div className="mt-3 text-sm text-blue-600">
            Selected: {selectedUCs.join(', ')} - Files will be processed through all selected UCs sequentially.
          </div>
        )}
      </div>

      {/* Start Processing Button */}
      <div className="flex items-center justify-between">
        <button
          onClick={handleBatchProcess}
          disabled={isProcessing || selectedUCs.length === 0}
          className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${
            isProcessing || selectedUCs.length === 0
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
          }`}
        >
          {isProcessing ? (
            <>
              <div className="animate-spin -ml-1 mr-3 h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
              Starting Batch Process...
            </>
          ) : (
            <>
              <PlayIcon className="h-4 w-4 mr-2" />
              Start Batch Processing
            </>
          )}
        </button>

        {selectedUCs.length === 0 && (
          <span className="text-sm text-gray-500">
            Select at least one analysis type to proceed
          </span>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-medium text-red-900">Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Success Result */}
      {result && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start">
            <CheckCircleIcon className="h-5 w-5 text-green-500 mt-0.5 mr-3 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-green-900">
                Batch Processing Started Successfully
              </h3>
              <div className="text-sm text-green-700 mt-2 space-y-1">
                <p><strong>Files Found:</strong> {result.files?.length || 0}</p>
                <p><strong>Job IDs:</strong> {result.job_ids?.join(', ')}</p>
                <p><strong>Selected UCs:</strong> {result.selected_ucs?.join(', ')}</p>
                <p><strong>Directory:</strong> {result.data_directory}</p>
              </div>
              {result.files && result.files.length > 0 && (
                <div className="mt-3">
                  <h4 className="text-xs font-medium text-green-900 mb-1">Files being processed:</h4>
                  <ul className="text-xs text-green-700 space-y-1">
                    {result.files.map((file: string, index: number) => (
                      <li key={index} className="flex items-center">
                        <span className="inline-block w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                        {file}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <p className="text-xs text-green-600 mt-3">
                Check the "Processing Jobs" section below to monitor progress in real-time.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
