import React from 'react';

function App() {
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
              <a href="#" className="text-gray-600 hover:text-gray-900">
                About
              </a>
              <a href="#" className="text-gray-600 hover:text-gray-900">
                Documentation
              </a>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
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
          <button className="bg-blue-600 text-white px-8 py-3 rounded-md text-lg hover:bg-blue-700">
            Try Demo
          </button>
        </div>

        {/* Features Section */}
        <div className="mt-24 grid md:grid-cols-3 gap-8">
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
      </main>
    </div>
  );
}

export default App;