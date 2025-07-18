import React, { useState, useEffect, useCallback } from 'react';
import logService from '../services/logService';
import type { LogEntry, LogFilters, LogsResponse } from '../services/logService';
import { debounce } from '../utils/debounce';

interface LogViewerProps {
  userId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const LogViewer: React.FC<LogViewerProps> = ({
  userId,
  autoRefresh = false,
  refreshInterval = 5000,
}) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(50);
  const [total, setTotal] = useState(0);
  const [categories, setCategories] = useState<string[]>([]);
  const [filters, setFilters] = useState<LogFilters>({ user_id: userId });
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [isAutoRefreshEnabled, setIsAutoRefreshEnabled] = useState(autoRefresh);

  // Fetch logs
  const fetchLogs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response: LogsResponse = await logService.getLogs(page, perPage, filters);
      setLogs(response.logs);
      setTotal(response.total);
    } catch (err) {
      setError('Failed to fetch logs');
      console.error('Error fetching logs:', err);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, filters]);

  // Set static categories based on backend enum
  useEffect(() => {
    setCategories([
      'PDF_PROCESSING',
      'SYSTEM',
      'AUTH',
      'API',
      'DATABASE',
      'SEARCH',
      'DOCUMENT'
    ]);
  }, []);

  // Debounced search
  const debouncedSearch = useCallback(
    debounce((search: string) => {
      setFilters(prev => ({ ...prev, search }));
      setPage(1);
    }, 300),
    []
  );

  // Initial load
  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // Auto-refresh
  useEffect(() => {
    if (!isAutoRefreshEnabled) return;

    const interval = setInterval(() => {
      fetchLogs();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [isAutoRefreshEnabled, refreshInterval, fetchLogs]);

  // Handle filter changes
  const handleFilterChange = (key: keyof LogFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value || undefined }));
    setPage(1);
  };

  // Handle export
  const handleExport = async () => {
    try {
      const blob = await logService.exportLogs(filters);
      const filename = `logs_${new Date().toISOString().split('T')[0]}.json`;
      logService.downloadLogsFile(blob, filename);
    } catch (err) {
      console.error('Error exporting logs:', err);
    }
  };

  // Handle clear logs
  const handleClearLogs = async () => {
    if (!window.confirm('Are you sure you want to clear the logs?')) return;

    try {
      await logService.clearLogs(filters);
      fetchLogs();
    } catch (err) {
      console.error('Error clearing logs:', err);
    }
  };

  // Pagination
  const totalPages = Math.ceil(total / perPage);
  const canGoBack = page > 1;
  const canGoForward = page < totalPages;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Application Logs</h2>
        <div className="flex gap-2">
          <button
            onClick={handleExport}
            className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          >
            Export
          </button>
          <button
            onClick={handleClearLogs}
            className="px-3 py-1.5 text-sm bg-red-100 hover:bg-red-200 text-red-700 rounded-md transition-colors"
          >
            Clear Logs
          </button>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={isAutoRefreshEnabled}
              onChange={(e) => setIsAutoRefreshEnabled(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm">Auto-refresh</span>
          </label>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-gray-50 p-4 rounded-lg space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {/* Search */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <input
              type="text"
              placeholder="Search logs..."
              onChange={(e) => debouncedSearch(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Level Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Level
            </label>
            <select
              value={filters.level || ''}
              onChange={(e) => handleFilterChange('level', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Levels</option>
              <option value="CRITICAL">Critical</option>
              <option value="ERROR">Error</option>
              <option value="WARNING">Warning</option>
              <option value="INFO">Info</option>
              <option value="DEBUG">Debug</option>
            </select>
          </div>

          {/* Category Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={filters.category || ''}
              onChange={(e) => handleFilterChange('category', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{logService.formatCategory(cat)}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Date Range */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="datetime-local"
              value={filters.start_date || ''}
              onChange={(e) => handleFilterChange('start_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="datetime-local"
              value={filters.end_date || ''}
              onChange={(e) => handleFilterChange('end_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      {/* Logs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Level
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Message
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                    Loading logs...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                    No logs found
                  </td>
                </tr>
              ) : (
                logs.map((log) => {
                  const levelFormat = logService.formatLogLevel(log.level);
                  return (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {logService.formatTimestamp(log.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${levelFormat.color} ${levelFormat.bgColor}`}
                        >
                          {levelFormat.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {logService.formatCategory(log.category)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 max-w-md truncate">
                        {log.message}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <button
                          onClick={() => setSelectedLog(log)}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="bg-gray-50 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-700">
              Showing {((page - 1) * perPage) + 1} to {Math.min(page * perPage, total)} of {total} logs
            </span>
            <select
              value={perPage}
              onChange={(e) => {
                setPerPage(Number(e.target.value));
                setPage(1);
              }}
              className="ml-2 px-2 py-1 text-sm border border-gray-300 rounded-md"
            >
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => p - 1)}
              disabled={!canGoBack}
              className={`px-3 py-1.5 text-sm rounded-md ${
                canGoBack
                  ? 'bg-white border border-gray-300 hover:bg-gray-50'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              }`}
            >
              Previous
            </button>
            <span className="px-3 py-1.5 text-sm">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={!canGoForward}
              className={`px-3 py-1.5 text-sm rounded-md ${
                canGoForward
                  ? 'bg-white border border-gray-300 hover:bg-gray-50'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              }`}
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Log Details Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium">Log Details</h3>
            </div>
            <div className="px-6 py-4 overflow-y-auto max-h-[calc(90vh-8rem)]">
              <dl className="space-y-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">ID</dt>
                  <dd className="mt-1 text-sm text-gray-900 font-mono">{selectedLog.id}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Timestamp</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {logService.formatTimestamp(selectedLog.created_at)}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Level</dt>
                  <dd className="mt-1">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        logService.formatLogLevel(selectedLog.level).color
                      } ${logService.formatLogLevel(selectedLog.level).bgColor}`}
                    >
                      {logService.formatLogLevel(selectedLog.level).label}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Category</dt>
                  <dd className="mt-1 text-sm text-gray-900">{selectedLog.category}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Message</dt>
                  <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                    {selectedLog.message}
                  </dd>
                </div>
                {selectedLog.details && Object.keys(selectedLog.details).length > 0 && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Details</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      <pre className="bg-gray-50 p-3 rounded-md overflow-x-auto">
                        {logService.formatDetails(selectedLog.details)}
                      </pre>
                    </dd>
                  </div>
                )}
                {selectedLog.error_trace && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Error Trace</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      <pre className="bg-red-50 p-3 rounded-md overflow-x-auto text-xs">
                        {selectedLog.error_trace}
                      </pre>
                    </dd>
                  </div>
                )}
                {selectedLog.entity_type && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Entity Type</dt>
                    <dd className="mt-1 text-sm text-gray-900">{selectedLog.entity_type}</dd>
                  </div>
                )}
                {selectedLog.entity_id && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Entity ID</dt>
                    <dd className="mt-1 text-sm text-gray-900 font-mono">{selectedLog.entity_id}</dd>
                  </div>
                )}
                {selectedLog.user_id && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">User ID</dt>
                    <dd className="mt-1 text-sm text-gray-900 font-mono">{selectedLog.user_id}</dd>
                  </div>
                )}
                {selectedLog.user_email && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">User Email</dt>
                    <dd className="mt-1 text-sm text-gray-900">{selectedLog.user_email}</dd>
                  </div>
                )}
              </dl>
            </div>
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LogViewer;