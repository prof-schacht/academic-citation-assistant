import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { zoteroService } from '../services/zoteroService';
import type { ZoteroStatus, ZoteroConfig } from '../services/zoteroService';

const ZoteroSettings: React.FC = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState<ZoteroStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Form state
  const [apiKey, setApiKey] = useState('');
  const [zoteroUserId, setZoteroUserId] = useState('');
  const [autoSyncEnabled, setAutoSyncEnabled] = useState(true);
  const [syncIntervalMinutes, setSyncIntervalMinutes] = useState(30);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const status = await zoteroService.getStatus();
      setStatus(status);
      
      // If already configured, don't show API key
      if (status.configured) {
        setAutoSyncEnabled(status.autoSyncEnabled);
        setSyncIntervalMinutes(status.syncIntervalMinutes);
      }
    } catch (err) {
      console.error('Failed to load Zotero status:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    
    if (!apiKey || !zoteroUserId) {
      setError('Please provide both API key and User ID');
      return;
    }
    
    setIsSaving(true);
    
    try {
      const config: ZoteroConfig = {
        apiKey,
        zoteroUserId,
        autoSyncEnabled,
        syncIntervalMinutes,
      };
      
      const newStatus = await zoteroService.configure(config);
      setStatus(newStatus);
      setSuccess('Zotero configuration saved successfully!');
      
      // Clear sensitive data
      setApiKey('');
      setZoteroUserId('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save configuration');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSync = async () => {
    setError(null);
    setSuccess(null);
    setIsSyncing(true);
    
    try {
      const result = await zoteroService.sync();
      setSuccess(result.message);
      
      // Reload status to get updated sync time
      await loadStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Sync failed');
    } finally {
      setIsSyncing(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect Zotero? This will remove the configuration but keep your papers.')) {
      return;
    }
    
    try {
      await zoteroService.disconnect();
      setStatus(null);
      setSuccess('Zotero disconnected successfully');
      await loadStatus();
    } catch (err) {
      setError('Failed to disconnect Zotero');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="mb-6">
          <button
            onClick={() => navigate('/papers')}
            className="text-gray-600 hover:text-gray-900 flex items-center"
          >
            ← Back to Papers
          </button>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-2xl font-bold mb-6">Zotero Integration</h1>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
              <p className="text-green-800">{success}</p>
            </div>
          )}

          {status?.configured ? (
            <div>
              <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                <h3 className="font-semibold text-blue-900 mb-2">Status</h3>
                <div className="space-y-1 text-sm">
                  <p>✓ Connected to Zotero</p>
                  {status.lastSync && (
                    <p>Last sync: {new Date(status.lastSync).toLocaleString()}</p>
                  )}
                  {status.lastSyncStatus && (
                    <p>Status: {status.lastSyncStatus}</p>
                  )}
                </div>
              </div>

              <form onSubmit={handleSave} className="space-y-4">
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={autoSyncEnabled}
                      onChange={(e) => setAutoSyncEnabled(e.target.checked)}
                      className="mr-2"
                    />
                    <span className="text-sm font-medium">Enable automatic sync</span>
                  </label>
                </div>

                {autoSyncEnabled && (
                  <div>
                    <label htmlFor="syncInterval" className="block text-sm font-medium text-gray-700">
                      Sync interval (minutes)
                    </label>
                    <input
                      type="number"
                      id="syncInterval"
                      min="10"
                      max="1440"
                      value={syncIntervalMinutes}
                      onChange={(e) => setSyncIntervalMinutes(parseInt(e.target.value) || 30)}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                )}

                <div className="flex gap-4">
                  <button
                    type="submit"
                    disabled={isSaving}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {isSaving ? 'Saving...' : 'Update Settings'}
                  </button>

                  <button
                    type="button"
                    onClick={handleSync}
                    disabled={isSyncing}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                  >
                    {isSyncing ? 'Syncing...' : 'Sync Now'}
                  </button>

                  <button
                    type="button"
                    onClick={handleDisconnect}
                    className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                  >
                    Disconnect
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <form onSubmit={handleSave} className="space-y-6">
              <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                <h3 className="font-semibold text-yellow-900 mb-2">Getting Started</h3>
                <ol className="list-decimal list-inside space-y-1 text-sm text-yellow-800">
                  <li>Go to <a href="https://www.zotero.org/settings/keys" target="_blank" rel="noopener noreferrer" className="underline">Zotero Settings → Keys</a></li>
                  <li>Create a new private key with library access</li>
                  <li>Copy your User ID (numeric value at top of page)</li>
                  <li>Copy your API Key</li>
                </ol>
              </div>

              <div>
                <label htmlFor="zoteroUserId" className="block text-sm font-medium text-gray-700">
                  Zotero User ID
                </label>
                <input
                  type="text"
                  id="zoteroUserId"
                  value={zoteroUserId}
                  onChange={(e) => setZoteroUserId(e.target.value)}
                  placeholder="e.g., 12345678"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  required
                />
                <p className="mt-1 text-sm text-gray-600">
                  Your numeric user ID from Zotero settings
                </p>
              </div>

              <div>
                <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700">
                  API Key
                </label>
                <input
                  type="password"
                  id="apiKey"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Your Zotero API key"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  required
                />
                <p className="mt-1 text-sm text-gray-600">
                  Private key with library read access
                </p>
              </div>

              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={autoSyncEnabled}
                    onChange={(e) => setAutoSyncEnabled(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium">Enable automatic sync</span>
                </label>
              </div>

              {autoSyncEnabled && (
                <div>
                  <label htmlFor="syncInterval" className="block text-sm font-medium text-gray-700">
                    Sync interval (minutes)
                  </label>
                  <input
                    type="number"
                    id="syncInterval"
                    min="10"
                    max="1440"
                    value={syncIntervalMinutes}
                    onChange={(e) => setSyncIntervalMinutes(parseInt(e.target.value) || 30)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
              )}

              <div>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {isSaving ? 'Connecting...' : 'Connect to Zotero'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default ZoteroSettings;