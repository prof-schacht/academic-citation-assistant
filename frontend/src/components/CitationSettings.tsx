import React, { useCallback, useRef } from 'react';
import { Settings, Search, Zap, Brain } from 'lucide-react';
import type { CitationConfig } from '../services/websocketService';

interface CitationSettingsProps {
  config: CitationConfig;
  onConfigChange: (config: Partial<CitationConfig>) => void;
}

export function CitationSettings({ config, onConfigChange }: CitationSettingsProps) {
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Debounced config change handler
  const handleConfigChange = useCallback((newConfig: Partial<CitationConfig>) => {
    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    // Set new timer
    debounceTimerRef.current = setTimeout(() => {
      onConfigChange(newConfig);
    }, 300); // 300ms debounce
  }, [onConfigChange]);
  return (
    <div className="p-4 bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="flex items-center gap-2 mb-4">
        <Settings className="w-5 h-5 text-gray-600" />
        <h3 className="text-lg font-medium text-gray-900">Citation Settings</h3>
      </div>
      
      <div className="space-y-4">
        {/* Enhanced Mode Toggle */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-blue-600" />
            <label htmlFor="enhanced-mode" className="text-sm font-medium text-gray-700">
              Enhanced Citations
            </label>
          </div>
          <input
            id="enhanced-mode"
            type="checkbox"
            checked={config.useEnhanced ?? true}
            onChange={(e) => handleConfigChange({ useEnhanced: e.target.checked })}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
        </div>
        
        {/* Reranking Toggle */}
        {config.useEnhanced && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-purple-600" />
              <label htmlFor="reranking" className="text-sm font-medium text-gray-700">
                Smart Reranking
              </label>
            </div>
            <input
              id="reranking"
              type="checkbox"
              checked={config.useReranking ?? false}
              onChange={(e) => handleConfigChange({ useReranking: e.target.checked })}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
          </div>
        )}
        
        {/* Search Strategy */}
        {config.useEnhanced && (
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <Search className="w-4 h-4 text-green-600" />
              Search Strategy
            </label>
            <select
              value={config.searchStrategy ?? 'hybrid'}
              onChange={(e) => handleConfigChange({ searchStrategy: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
              <option value="hybrid">Hybrid (Recommended)</option>
              <option value="vector">Semantic Search</option>
              <option value="bm25">Keyword Search</option>
            </select>
          </div>
        )}
        
        {/* Info Messages */}
        <div className="mt-4 space-y-2">
          {config.useEnhanced && (
            <p className="text-xs text-gray-500">
              Enhanced mode uses advanced chunking and retrieval techniques for better accuracy.
            </p>
          )}
          {config.useReranking && (
            <p className="text-xs text-gray-500">
              Smart reranking uses AI to improve relevance but may add 2-5 seconds latency.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}