/**
 * Zotero integration service
 */

import { api } from './api';

export interface ZoteroConfig {
  apiKey: string;
  zoteroUserId: string;
  autoSyncEnabled: boolean;
  syncIntervalMinutes: number;
}

export interface ZoteroStatus {
  configured: boolean;
  autoSyncEnabled: boolean;
  syncIntervalMinutes: number;
  lastSync?: string;
  lastSyncStatus?: string;
}

export interface ZoteroSyncResult {
  success: boolean;
  newPapers: number;
  updatedPapers: number;
  failedPapers: number;
  message: string;
}

class ZoteroService {
  async configure(config: ZoteroConfig): Promise<ZoteroStatus> {
    const response = await api.post('/zotero/configure', {
      api_key: config.apiKey,
      zotero_user_id: config.zoteroUserId,
      auto_sync_enabled: config.autoSyncEnabled,
      sync_interval_minutes: config.syncIntervalMinutes,
    });
    return this.mapStatus(response.data);
  }

  async getStatus(): Promise<ZoteroStatus> {
    const response = await api.get('/zotero/status');
    return this.mapStatus(response.data);
  }

  async sync(): Promise<ZoteroSyncResult> {
    const response = await api.post('/zotero/sync');
    return {
      success: response.data.success,
      newPapers: response.data.new_papers,
      updatedPapers: response.data.updated_papers,
      failedPapers: response.data.failed_papers,
      message: response.data.message,
    };
  }

  async testConnection(): Promise<{ connected: boolean; message: string }> {
    const response = await api.post('/zotero/test-connection');
    return response.data;
  }

  async disconnect(): Promise<{ success: boolean; message: string }> {
    const response = await api.delete('/zotero/disconnect');
    return response.data;
  }

  private mapStatus(data: any): ZoteroStatus {
    return {
      configured: data.configured,
      autoSyncEnabled: data.auto_sync_enabled,
      syncIntervalMinutes: data.sync_interval_minutes,
      lastSync: data.last_sync,
      lastSyncStatus: data.last_sync_status,
    };
  }
}

export const zoteroService = new ZoteroService();