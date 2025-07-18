import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import LogViewer from '../components/LogViewer';

const LogsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation */}
        <div className="mb-6">
          <Link
            to="/library"
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="mr-1 h-4 w-4" />
            Back to Library
          </Link>
        </div>

        {/* Page Title */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">System Logs</h1>
          <p className="mt-2 text-gray-600">
            View and manage application logs, including sync operations, errors, and system events.
          </p>
        </div>

        {/* Log Viewer */}
        <div className="bg-white rounded-lg shadow p-6">
          <LogViewer autoRefresh={true} refreshInterval={10000} />
        </div>

        {/* Help Section */}
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-2">Understanding Log Levels</h3>
          <div className="space-y-2 text-sm text-blue-800">
            <div>
              <span className="font-semibold">ERROR:</span> Critical issues that need immediate attention
            </div>
            <div>
              <span className="font-semibold">WARN:</span> Important warnings that may indicate problems
            </div>
            <div>
              <span className="font-semibold">INFO:</span> General information about system operations
            </div>
            <div>
              <span className="font-semibold">DEBUG:</span> Detailed information for troubleshooting
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LogsPage;