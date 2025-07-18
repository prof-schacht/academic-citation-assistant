"""Main FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api import health, documents, papers, zotero, logs_simple as logs, document_papers, admin
from app.api.websocket import websocket_citation_endpoint
from app.services.background_processor import background_processor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Download NLTK data on startup
    try:
        import nltk
        nltk.download('punkt_tab', quiet=True)
        print("NLTK punkt_tab tokenizer downloaded")
    except Exception as e:
        print(f"Warning: Failed to download NLTK data: {e}")
        # Try fallback
        try:
            import nltk
            nltk.download('punkt', quiet=True)
            print("NLTK punkt tokenizer downloaded (fallback)")
        except:
            print("Warning: Failed to download any NLTK tokenizer data")
    
    # Start background PDF processor
    await background_processor.start()
    print("Background PDF processor started")
    
    yield
    
    # Shutdown
    print("Shutting down application")
    await background_processor.stop()
    print("Background PDF processor stopped")


# Create FastAPI app instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    debug=settings.debug,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return JSONResponse(
        content={
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        }
    )


# Include routers
app.include_router(health.router, prefix=f"{settings.api_prefix}/health", tags=["health"])
app.include_router(documents.router, prefix=f"{settings.api_prefix}/documents", tags=["documents"])
app.include_router(papers.router, prefix=f"{settings.api_prefix}", tags=["papers"])
app.include_router(zotero.router, prefix=f"{settings.api_prefix}", tags=["zotero"])
app.include_router(logs.router, prefix=f"{settings.api_prefix}/logs", tags=["logs"])
app.include_router(document_papers.router, prefix=f"{settings.api_prefix}", tags=["document-papers"])
app.include_router(admin.router, prefix=f"{settings.api_prefix}/admin", tags=["admin"])

# Add WebSocket endpoint
app.add_websocket_route("/ws/citations", websocket_citation_endpoint)