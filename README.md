# Academic Citation Assistant 📚

A real-time citation recommendation system that revolutionizes academic writing by providing intelligent, context-aware paper suggestions as you type.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-in%20development-yellow.svg)

## 🎯 Overview

The Academic Citation Assistant is a web-based tool that acts like "Grammarly for citations" - providing real-time, contextual citation recommendations as researchers write their papers. It combines local paper libraries with external academic databases to suggest the most relevant citations based on the semantic meaning of your text.

### Key Features

- ✨ **Real-time Suggestions**: Get citation recommendations as you type
- 🎯 **Context-Aware**: Understands the meaning of your text, not just keywords
- 📊 **Confidence Scoring**: See how relevant each suggestion is
- 📱 **Cross-Platform**: Works seamlessly on desktop and iPad
- 🔍 **Multi-Source Search**: Search your library and millions of papers online
- 📝 **Rich Text Editor**: Write with formatting, no LaTeX knowledge required
- 🤝 **Collaboration**: Share documents and citation libraries with your team
- 📤 **Export Flexibility**: Export to Word, LaTeX, PDF, or Markdown

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- PostgreSQL 14+ with pgvector extension
- Redis 6+
- Docker (optional, for containerized deployment)

### Installation

```bash
# Clone the repository
git clone https://github.com/prof-schacht/academic-citation-assistant.git
cd academic-citation-assistant

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env

# Run database migrations
npm run db:migrate

# Start development server
npm run dev
```

### Quick Start Guide

1. **Sign up** with your email or Google account
2. **Upload papers** to your personal library (optional)
3. **Start writing** - suggestions appear automatically
4. **Click to cite** - it's that simple!

## 📖 Documentation

Comprehensive documentation is available in the `/docs` folder:

- [Technical Architecture](./docs/technical-architecture.md)
- [User Guide](./docs/user-guide.md)
- [API Documentation](./docs/api-documentation.md)
- [Development Guide](./docs/development-guide.md)
- [Deployment Guide](./docs/deployment-guide.md)

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Web Client    │────▶│   API Gateway    │────▶│  Backend API    │
│  (React PWA)    │     │   (Nginx)        │     │  (Node.js)      │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │
                        ┌──────────────────────────────────┴────────┐
                        │                                           │
                ┌───────▼────────┐                    ┌────────────▼────────┐
                │  PostgreSQL    │                    │   External APIs     │
                │  + pgvector    │                    │  (Semantic Scholar) │
                └────────────────┘                    └─────────────────────┘
```

## 🛠️ Technology Stack

- **Frontend**: React 18, TypeScript, TailwindCSS, Lexical Editor
- **Backend**: Node.js, Express, PostgreSQL, Redis
- **AI/ML**: Sentence Transformers, pgvector
- **Infrastructure**: Docker, Nginx, WebSockets

## 🗺️ Roadmap

### Phase I (Current) - Local Library
- [x] Repository setup
- [ ] Core editor implementation
- [ ] Local paper upload and vectorization
- [ ] Real-time citation suggestions
- [ ] Basic document management

### Phase II - External Integration
- [ ] Semantic Scholar API integration
- [ ] Multi-source aggregation
- [ ] Advanced filtering and ranking
- [ ] Collaboration features

### Phase III - Advanced Features
- [ ] AI writing assistance
- [ ] Citation graph visualization
- [ ] Mobile applications
- [ ] Plugin ecosystem

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Semantic Scholar for their excellent API
- The sentence-transformers team for embedding models
- All contributors and early testers

## 📞 Contact

- **Project Lead**: [@prof-schacht](https://github.com/prof-schacht)
- **Email**: contact@academic-citation-assistant.com
- **Issues**: [GitHub Issues](https://github.com/prof-schacht/academic-citation-assistant/issues)

---

Made with ❤️ for the academic community
