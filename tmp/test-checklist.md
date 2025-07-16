# Document-Centric Workflow Test Checklist

## 1. Zotero Removal Verification
- [ ] Navigate to Paper Library - verify "Zotero Sync" button is removed
- [ ] Check that `/zotero` route no longer exists
- [ ] Verify logs page no longer shows ZOTERO_SYNC category

## 2. Document Editor Tabs
- [ ] Open a document in the editor
- [ ] Verify three tabs appear: "Editor", "Bibliography", "Citations"
- [ ] Click each tab to verify they switch correctly
- [ ] Verify citation count badge appears on Citations tab when suggestions exist

## 3. Paper Assignment from Library
- [ ] Go to Paper Library
- [ ] Upload a new paper or use existing indexed paper
- [ ] Click the 📎 (paperclip) icon on an indexed paper
- [ ] Verify "Select Document Dialog" opens
- [ ] Select a document and optionally add notes
- [ ] Click "Assign to Document"
- [ ] Verify success or appropriate error message

## 4. Bibliography Management
- [ ] Open a document and go to Bibliography tab
- [ ] Verify assigned papers appear
- [ ] Test "Add Papers" button to assign more papers
- [ ] Test adding/editing notes for a paper
- [ ] Test removing a paper (🗑️ icon)
- [ ] Test drag-and-drop reordering of papers

## 5. Export Functionality
- [ ] Click Export button in document editor
- [ ] Verify new export options: BibTeX and LaTeX
- [ ] Test BibTeX export - should download .bib file
- [ ] Test LaTeX export - should download .tex file
- [ ] Verify other export formats still work

## 6. API Endpoints
- [ ] POST /api/documents/{id}/papers - Assign paper
- [ ] GET /api/documents/{id}/papers - List papers (check if working)
- [ ] POST /api/documents/{id}/papers/reorder - Reorder papers
- [ ] DELETE /api/documents/{id}/papers/{paper_id} - Remove paper
- [ ] GET /api/documents/{id}/export/bibtex - Export BibTeX
- [ ] GET /api/documents/{id}/export/latex - Export LaTeX

## Known Issues to Verify
- [ ] GET /api/documents/{id}/papers - Returns 500 error (needs investigation)
- [ ] PATCH /api/documents/{id}/papers/{paper_id} - Returns 500 error (needs investigation)