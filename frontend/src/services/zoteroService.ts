/**
 * Zotero integration service
 */

import { api } from './api';

export interface ZoteroConfig {
  apiKey: string;
  zoteroUserId: string;
  autoSyncEnabled: boolean;
  syncIntervalMinutes: number;
  selectedGroups?: string[];
  selectedCollections?: string[];
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

export interface ZoteroGroup {
  id: string;
  name: string;
  type: string;
  owner: string | null;
}

export interface ZoteroCollection {
  key: string;
  name: string;
  parentCollection: string | null;
  libraryId: string;
}

class ZoteroService {
  async configure(config: ZoteroConfig): Promise<ZoteroStatus> {
    const response = await api.post('/zotero/configure', {
      api_key: config.apiKey,
      zotero_user_id: config.zoteroUserId,
      auto_sync_enabled: config.autoSyncEnabled,
      sync_interval_minutes: config.syncIntervalMinutes,
      selected_groups: config.selectedGroups,
      selected_collections: config.selectedCollections,
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
  
  async getGroups(): Promise<ZoteroGroup[]> {
    const response = await api.get('/zotero/groups');
    return response.data;
  }
  
  async getCollections(libraryId?: string): Promise<ZoteroCollection[]> {
    const response = await api.get('/zotero/collections', {
      params: { library_id: libraryId }
    });
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