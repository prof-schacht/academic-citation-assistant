import React from 'react';
import { useNavigate } from 'react-router-dom';

const HomePage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">
              Academic Citation Assistant
            </h1>
            <nav className="space-x-4">
              <a href="#features" className="text-gray-600 hover:text-gray-900">
                Features
              </a>
              <a href="/docs" className="text-gray-600 hover:text-gray-900">
                Documentation
              </a>
              <button 
                onClick={() => navigate('/documents')}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Get Started
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Real-time Citation Recommendations for Academic Writing
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Like Grammarly for citations - get intelligent paper suggestions as you type
          </p>
          <button 
            onClick={() => navigate('/editor')}
            className="bg-blue-600 text-white px-8 py-3 rounded-md text-lg hover:bg-blue-700"
          >
            Try Demo
          </button>
        </div>

        {/* Features Section */}
        <div id="features" className="mt-24 grid md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="bg-blue-100 w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center">
              <span className="text-2xl">✨</span>
            </div>
            <h3 className="text-lg font-semibold mb-2">Real-time Suggestions</h3>
            <p className="text-gray-600">
              Get citation recommendations instantly as you write your paper
            </p>
          </div>
          <div className="text-center">
            <div className="bg-blue-100 w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center">
              <span className="text-2xl">🎯</span>
            </div>
            <h3 className="text-lg font-semibold mb-2">Context-Aware</h3>
            <p className="text-gray-600">
              AI understands your content, not just keywords
            </p>
          </div>
          <div className="text-center">
            <div className="bg-blue-100 w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center">
              <span className="text-2xl">📊</span>
            </div>
            <h3 className="text-lg font-semibold mb-2">Confidence Scoring</h3>
            <p className="text-gray-600">
              See how relevant each suggestion is to your work
            </p>
          </div>
        </div>

        {/* Demo Section */}
        <div className="mt-24 bg-white rounded-lg shadow-lg p-8">
          <h3 className="text-2xl font-bold text-center mb-8">How It Works</h3>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-gray-100 rounded-lg p-6 mb-4">
                <span className="text-4xl">📝</span>
              </div>
              <h4 className="font-semibold mb-2">1. Write Your Paper</h4>
              <p className="text-gray-600">
                Start typing in our rich text editor with full formatting support
              </p>
            </div>
            <div className="text-center">
              <div className="bg-gray-100 rounded-lg p-6 mb-4">
                <span className="text-4xl">🔍</span>
              </div>
              <h4 className="font-semibold mb-2">2. Get Suggestions</h4>
              <p className="text-gray-600">
                Our AI analyzes your content and suggests relevant citations
              </p>
            </div>
            <div className="text-center">
              <div className="bg-gray-100 rounded-lg p-6 mb-4">
                <span className="text-4xl">✅</span>
              </div>
              <h4 className="font-semibold mb-2">3. Insert Citations</h4>
              <p className="text-gray-600">
                Click to insert citations with proper formatting
              </p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-24 text-center bg-blue-50 rounded-lg p-12">
          <h3 className="text-3xl font-bold mb-4">Ready to improve your academic writing?</h3>
          <p className="text-xl text-gray-600 mb-8">
            Join researchers who are already using our AI-powered citation assistant
          </p>
          <button 
            onClick={() => navigate('/documents')}
            className="bg-blue-600 text-white px-8 py-3 rounded-md text-lg hover:bg-blue-700"
          >
            Start Writing Now
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white mt-24 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p>&copy; 2025 Academic Citation Assistant. All rights reserved.</p>
            <div className="mt-4 space-x-4">
              <a href="/privacy" className="text-gray-400 hover:text-white">Privacy</a>
              <a href="/terms" className="text-gray-400 hover:text-white">Terms</a>
              <a href="/contact" className="text-gray-400 hover:text-white">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;