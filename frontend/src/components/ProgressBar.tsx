import React from 'react';

interface ProgressBarProps {
  percentage: number;
  status: string;
  currentItem?: number;
  totalItems?: number;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ 
  percentage, 
  status, 
  currentItem, 
  totalItems 
}) => {
  return (
    <div className="w-full bg-gray-200 rounded-lg overflow-hidden">
      <div className="bg-blue-50 p-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">
            {status}
          </span>
          <span className="text-sm text-gray-500">
            {percentage}%
          </span>
        </div>
        
        <div className="w-full bg-gray-300 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
          />
        </div>
        
        {currentItem !== undefined && totalItems !== undefined && (
          <div className="mt-2 text-xs text-gray-500">
            {currentItem} of {totalItems} items processed
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgressBar;