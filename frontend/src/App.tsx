import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import DocumentsList from './pages/DocumentsList';
import DocumentEditor from './pages/DocumentEditor';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/documents" element={<DocumentsList />} />
        <Route path="/editor" element={<DocumentEditor />} />
        <Route path="/editor/:id" element={<DocumentEditor />} />
      </Routes>
    </Router>
  );
}

export default App;