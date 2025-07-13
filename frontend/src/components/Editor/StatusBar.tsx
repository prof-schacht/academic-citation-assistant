import React from 'react';

interface StatusBarProps {
  wordCount: number;
  characterCount: number;
  lastSaved: Date | null;
  isSaving: boolean;
}

const StatusBar: React.FC<StatusBarProps> = ({
  wordCount,
  characterCount,
  lastSaved,
  isSaving,
}) => {
  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) {
      return 'Just now';
    } else if (diff < 3600000) {
      const minutes = Math.floor(diff / 60000);
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleTimeString();
    }
  };

  return (
    <div className="border-t border-gray-200 px-4 py-2 flex items-center justify-between text-sm bg-gray-50">
      <div className="flex items-center space-x-6 text-gray-600">
        <span>{wordCount.toLocaleString()} words</span>
        <span>{characterCount.toLocaleString()} characters</span>
      </div>
      
      <div className="flex items-center space-x-2">
        {isSaving ? (
          <div className="flex items-center text-blue-600">
            <svg className="animate-spin h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24">
              <circle 
                className="opacity-25" 
                cx="12" 
                cy="12" 
                r="10" 
                stroke="currentColor" 
                strokeWidth="4"
              />
              <path 
                className="opacity-75" 
                fill="currentColor" 
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span>Saving...</span>
          </div>
        ) : lastSaved ? (
          <div className="flex items-center text-green-600">
            <svg className="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path 
                fillRule="evenodd" 
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" 
                clipRule="evenodd" 
              />
            </svg>
            <span>Saved {formatTime(lastSaved)}</span>
          </div>
        ) : (
          <span className="text-gray-500">Not saved</span>
        )}
      </div>
    </div>
  );
};

export default StatusBar;