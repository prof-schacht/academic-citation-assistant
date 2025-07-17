# Document Save Analysis - Academic Citation Assistant

## Overview
This document analyzes how documents are saved in the frontend of the Academic Citation Assistant.

## Key Components

### 1. DocumentEditor Component (`/frontend/src/pages/DocumentEditor.tsx`)
- Main component that manages the document editing interface
- Handles tab switching between "Editor", "Bibliography", and "Citations"
- Manages the document state and passes save handlers to the Editor component

### 2. Editor Component (`/frontend/src/components/Editor/Editor.tsx`)
- Implements auto-save functionality using Lexical editor
- Uses debounced saving with a default delay of 2000ms (2 seconds)
- Tracks content changes and only saves after user modifications

## Save Mechanisms

### Auto-Save Logic
1. **Debounced Save Function**:
   - Created using `lodash.debounce` with configurable delay (default: 2000ms)
   - Triggered on every content change via `OnChangePlugin`
   - Only activates after the user has made changes (`hasContentChanged` flag)
   - Serializes editor state to JSON and sends to backend via `documentService.update()`

2. **Manual Save**:
   - Triggered by Ctrl/Cmd+S keyboard shortcut
   - Calls `debouncedSave.flush()` to immediately execute pending saves

### Save Flow
```
User types → OnChangePlugin → handleChange → debouncedSave (waits 2s) → documentService.update()
                                     ↓
                             Sets hasContentChanged = true
```

## Critical Issues Identified

### 1. Tab Switching Without Saving
When users switch tabs (Editor → Bibliography → Citations), the Editor component is **conditionally rendered**:
```tsx
{activeTab === 'editor' && (
  <Editor ... />
)}
```

This means:
- The Editor component is **unmounted** when switching tabs
- The cleanup effect calls `debouncedSave.cancel()`, which **cancels any pending saves**
- **Unsaved changes are lost** if the user switches tabs within the 2-second debounce window

### 2. Navigation Without Saving
When navigating away (e.g., clicking "Back" button):
- No save is triggered before navigation
- Any pending debounced saves are cancelled
- No warning is shown to the user about unsaved changes

### 3. No Browser Close Protection
- No `beforeunload` event handler to warn users about unsaved changes
- Users can close the browser tab and lose recent edits

## Impact on Users

1. **Data Loss Risk**: Users may lose work if they:
   - Switch tabs quickly after typing
   - Navigate away within 2 seconds of their last edit
   - Close the browser without waiting for auto-save

2. **No Visual Feedback**: While there is a "Saving..." indicator, users may not notice it and assume their work is saved immediately

3. **Inconsistent State**: The document state in different tabs may be out of sync if changes haven't been saved

## Recommended Solutions

1. **Immediate Save on Tab Switch**:
   - Add a handler to flush pending saves before switching tabs
   - Ensure the Editor remains mounted or saves state before unmounting

2. **Navigation Guards**:
   - Implement route guards to check for unsaved changes
   - Show confirmation dialog if there are pending saves

3. **Browser Close Protection**:
   - Add `beforeunload` event handler when there are unsaved changes
   - Remove handler after successful save

4. **Persistent Editor State**:
   - Keep Editor mounted but hidden when switching tabs
   - Or save editor state to a ref/context before unmounting

5. **Reduce Debounce Delay**:
   - Consider reducing from 2000ms to 500-1000ms for more frequent saves
   - Balance between API calls and data safety