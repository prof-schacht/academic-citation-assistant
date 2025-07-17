# Citation Insertion Save Issue Analysis

## Problem Description
After inserting a citation into the editor, the document doesn't auto-save. The user needs to type additional text for the save to trigger.

## Key Findings from Code Analysis

### 1. Citation Insertion Process (CitationInsertPlugin.tsx)
- When a citation is inserted, the plugin:
  1. Creates a CitationNode
  2. Uses `$insertNodes` to add it to the editor
  3. Calls `editor.focus()` at the end
  4. Triggers the `onCitationInserted` callback

### 2. Editor Change Detection (Editor.tsx)
- The editor uses `OnChangePlugin` with a `handleChange` callback
- Auto-save is triggered by the `handleChange` function 
- Auto-save only happens if `hasContentChanged` is true
- The `hasContentChanged` flag is set on the first change

### 3. Potential Issues Identified

#### Issue 1: Focus/Blur Timing
After citation insertion, `editor.focus()` is called (line 95 in CitationInsertPlugin). This might not properly trigger the onChange event if the editor already had focus.

#### Issue 2: Node Insertion Method
The `$insertNodes` operation might not be triggering the onChange handler properly. Lexical might be batching the update in a way that doesn't fire the change event.

#### Issue 3: Editor State Reference
The editor maintains `hasContentChanged` state that only gets set to true on the first change. If the citation insertion doesn't trigger onChange, this flag might not be set.

## Hypothesis
The citation insertion is happening through a programmatic update that bypasses the normal change detection mechanism. The `editor.update()` call in CitationInsertPlugin might need to be followed by an explicit trigger of the onChange handler.

## Potential Solutions

### Solution 1: Force onChange After Citation Insertion
Modify CitationInsertPlugin to explicitly trigger a change event after insertion:

```typescript
editor.update(() => {
  // ... existing citation insertion code ...
}, {
  onUpdate: () => {
    // Force the onChange handler to fire
    editor.dispatchCommand(EDITOR_CONTENT_CHANGED_COMMAND, null);
  }
});
```

### Solution 2: Manual Save Trigger
Add a manual save trigger after citation insertion in the onCitationInserted callback:

```typescript
const handleCitationInserted = async (citation: CitationSuggestion) => {
  // ... existing code ...
  
  // Force a save after citation insertion
  if (editorSaveRef.current) {
    editorSaveRef.current();
  }
};
```

### Solution 3: Modify Change Detection
Update the Editor component to detect citation insertions as changes:

```typescript
// In Editor.tsx, add a flag to track citation insertions
const [citationInserted, setCitationInserted] = useState(false);

// In the citation inserted handler
onCitationInserted={(citation) => {
  setCitationInserted(true);
  // existing handler code
}}

// Use effect to trigger save when citation is inserted
useEffect(() => {
  if (citationInserted && documentId) {
    debouncedSave.flush();
    setCitationInserted(false);
  }
}, [citationInserted, documentId, debouncedSave]);
```

## Recommended Fix
The most straightforward solution is **Solution 2** - manually triggering a save after citation insertion. This ensures the document is saved without relying on the onChange mechanism which might not fire consistently for programmatic updates.

## Next Steps
1. Implement the manual save trigger in DocumentEditor.tsx
2. Test the fix with various citation insertion scenarios
3. Verify that normal typing still triggers auto-save correctly