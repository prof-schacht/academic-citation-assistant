import api from './api';

export interface LogEntry {
  id: string;
  created_at: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  category: 'ZOTERO_SYNC' | 'PDF_PROCESSING' | 'SYSTEM' | 'AUTH' | 'API' | 'DATABASE' | 'SEARCH';
  message: string;
  details?: Record<string, any>;
  error_trace?: string;
  entity_type?: string;
  entity_id?: string;
  user_id?: string;
  user_email?: string;
}

export interface LogFilters {
  level?: string;
  category?: string;
  search?: string;
  start_date?: string;
  end_date?: string;
  user_id?: string;
  entity_type?: string;
  entity_id?: string;
}

export interface LogsResponse {
  logs: LogEntry[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

class LogService {
  async getLogs(
    page = 1,
    perPage = 50,
    filters: LogFilters = {}
  ): Promise<LogsResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    });

    // Add filters to params
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        params.append(key, value);
      }
    });

    const response = await api.get(`/logs?${params.toString()}`);
    return response.data;
  }

  async getLogCategories(): Promise<string[]> {
    const response = await api.get('/logs/categories');
    return response.data;
  }

  async clearLogs(filters: LogFilters = {}): Promise<void> {
    await api.delete('/logs', { data: filters });
  }

  async exportLogs(filters: LogFilters = {}): Promise<Blob> {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        params.append(key, value);
      }
    });

    const response = await api.get(`/logs/export?${params.toString()}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  downloadLogsFile(blob: Blob, filename: string) {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  formatLogLevel(level: string): {
    label: string;
    color: string;
    bgColor: string;
  } {
    switch (level) {
      case 'CRITICAL':
        return {
          label: 'CRITICAL',
          color: 'text-red-900',
          bgColor: 'bg-red-200',
        };
      case 'ERROR':
        return {
          label: 'ERROR',
          color: 'text-red-700',
          bgColor: 'bg-red-100',
        };
      case 'WARNING':
        return {
          label: 'WARNING',
          color: 'text-yellow-700',
          bgColor: 'bg-yellow-100',
        };
      case 'INFO':
        return {
          label: 'INFO',
          color: 'text-blue-700',
          bgColor: 'bg-blue-100',
        };
      case 'DEBUG':
        return {
          label: 'DEBUG',
          color: 'text-gray-700',
          bgColor: 'bg-gray-100',
        };
      default:
        return {
          label: level,
          color: 'text-gray-700',
          bgColor: 'bg-gray-100',
        };
    }
  }

  formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  }

  formatDetails(details?: Record<string, any>): string {
    if (!details || Object.keys(details).length === 0) {
      return '';
    }
    return JSON.stringify(details, null, 2);
  }

  formatCategory(category: string): string {
    const categoryMap: Record<string, string> = {
      'ZOTERO_SYNC': 'Zotero Sync',
      'PDF_PROCESSING': 'PDF Processing',
      'SYSTEM': 'System',
      'AUTH': 'Authentication',
      'API': 'API',
      'DATABASE': 'Database',
      'SEARCH': 'Search'
    };
    return categoryMap[category] || category;
  }
}

export default new LogService();