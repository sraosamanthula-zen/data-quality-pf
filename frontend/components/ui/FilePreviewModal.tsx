'use client';

import { XMarkIcon } from '@heroicons/react/24/outline';

interface FilePreviewModalProps {
  isOpen: boolean;
  filename: string | null;
  onClose: () => void;
  loading: boolean;
  previewData: {
    headers: string[];
    rows: string[][];
    totalRows: number;
  } | null;
  modalSize: { width: number; height: number };
  onResizeStart: (e: React.MouseEvent) => void;
}

export default function FilePreviewModal({
  isOpen,
  filename,
  onClose,
  loading,
  previewData,
  modalSize,
  onResizeStart
}: FilePreviewModalProps) {
  if (!isOpen || !filename) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div 
        className="bg-white dark:bg-gray-800 rounded-lg mx-4 flex flex-col shadow-2xl relative"
        style={{ 
          width: `${modalSize.width}px`, 
          height: `${modalSize.height}px`,
          maxWidth: '95vw',
          maxHeight: '95vh'
        }}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-600 flex-shrink-0">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            File Preview: {filename}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>
        
        {/* Modal Content */}
        <div className="flex-1 overflow-hidden p-6 min-h-0">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 dark:border-blue-400"></div>
              <span className="ml-2 text-gray-600 dark:text-gray-300">Loading preview...</span>
            </div>
          ) : previewData ? (
            <div className="space-y-4 h-full flex flex-col">
              <div className="text-sm text-gray-600 dark:text-gray-300 flex-shrink-0">
                Showing first 100 rows of {previewData.totalRows} total rows
              </div>
              
              <div className="overflow-auto flex-1 border border-gray-200 dark:border-gray-600 rounded-lg">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-600">
                  <thead className="bg-gray-50 dark:bg-gray-700 sticky top-0">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider border-r border-gray-200 dark:border-gray-600">
                        #
                      </th>
                      {previewData.headers.map((header, index) => (
                        <th
                          key={index}
                          className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider border-r border-gray-200 dark:border-gray-600 last:border-r-0"
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600">
                    {previewData.rows.map((row, rowIndex) => (
                      <tr key={rowIndex} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400 border-r border-gray-200 dark:border-gray-600">
                          {rowIndex + 1}
                        </td>
                        {row.map((cell, cellIndex) => (
                          <td
                            key={cellIndex}
                            className="px-3 py-2 text-xs text-gray-900 dark:text-white border-r border-gray-200 dark:border-gray-600 last:border-r-0 max-w-xs truncate"
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
                <div className="text-xs text-gray-500 dark:text-gray-400 text-center flex-shrink-0">
                  ... and {previewData.totalRows - 100} more rows
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
              Failed to load preview
            </div>
          )}
        </div>

        {/* Resize Handle */}
        <div
          className="absolute bottom-0 right-0 w-4 h-4 cursor-nw-resize bg-gray-300 hover:bg-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500 transition-colors"
          style={{
            background: 'linear-gradient(-45deg, transparent 0%, transparent 30%, currentColor 30%, currentColor 40%, transparent 40%, transparent 60%, currentColor 60%, currentColor 70%, transparent 70%)',
            borderBottomRightRadius: '0.5rem'
          }}
          onMouseDown={onResizeStart}
          title="Drag to resize"
        />
      </div>
    </div>
  );
}
