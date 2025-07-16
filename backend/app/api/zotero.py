"""Zotero API endpoints."""
import json
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.models import User
from app.services.zotero_service import ZoteroService
from app.api.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/zotero", tags=["zotero"])


class ZoteroConfigRequest(BaseModel):
    """Request model for Zotero configuration."""
    api_key: Optional[str] = Field(None, description="Zotero API key (required for initial setup)")
    zotero_user_id: Optional[str] = Field(None, description="Numeric Zotero user ID (required for initial setup)")
    auto_sync_enabled: bool = Field(True, description="Enable automatic sync")
    sync_interval_minutes: int = Field(30, description="Sync interval in minutes")
    selected_groups: Optional[List[str]] = Field(None, description="List of selected group IDs")
    selected_collections: Optional[List[str]] = Field(None, description="List of selected collection keys")


class ZoteroConfigResponse(BaseModel):
    """Response model for Zotero configuration."""
    configured: bool
    auto_sync_enabled: bool
    sync_interval_minutes: int
    last_sync: Optional[str] = None
    last_sync_status: Optional[str] = None
    selected_groups: Optional[List[str]] = None
    selected_collections: Optional[List[str]] = None


class ZoteroSyncResponse(BaseModel):
    """Response model for sync operation."""
    success: bool
    new_papers: int
    updated_papers: int
    failed_papers: int
    message: str


@router.post("/configure", response_model=ZoteroConfigResponse)
async def configure_zotero(
    config: ZoteroConfigRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ZoteroConfigResponse:
    """Configure Zotero integration for the current user."""
    logger.info(f"Received config request: selected_groups={config.selected_groups}, selected_collections={config.selected_collections}")
    try:
        from sqlalchemy import select
        from app.models import ZoteroConfig
        
        # Check if config already exists
        result = await db.execute(
            select(ZoteroConfig).where(ZoteroConfig.user_id == current_user.id)
        )
        existing_config = result.scalar_one_or_none()
        
        if existing_config:
            # Update existing config
            zotero_config = existing_config
            
            # Only update API key and user ID if provided (not empty)
            if config.api_key:
                zotero_config.api_key = config.api_key
            if config.zotero_user_id:
                zotero_config.zotero_user_id = config.zotero_user_id
                
            zotero_config.auto_sync_enabled = config.auto_sync_enabled
            zotero_config.sync_interval_minutes = config.sync_interval_minutes
            
            # Update selected groups and collections
            import json
            if config.selected_groups is not None:
                logger.info(f"Updating selected_groups to: {config.selected_groups}")
                zotero_config.selected_groups = json.dumps(config.selected_groups)
            if config.selected_collections is not None:
                logger.info(f"Updating selected_collections to: {config.selected_collections}")
                zotero_config.selected_collections = json.dumps(config.selected_collections)
                
            zotero_config.updated_at = datetime.utcnow()
        else:
            # Create new config - API key and user ID are required
            if not config.api_key or not config.zotero_user_id:
                raise HTTPException(
                    status_code=400,
                    detail="API key and Zotero user ID are required for initial configuration"
                )
                
            # Create service without using context manager for initial configuration
            service = ZoteroService(db, current_user.id)
            
            # Configure (this creates the config)
            zotero_config = await service.configure(
                api_key=config.api_key,
                zotero_user_id=config.zotero_user_id
            )
            
            # Update sync settings
            zotero_config.auto_sync_enabled = config.auto_sync_enabled
            zotero_config.sync_interval_minutes = config.sync_interval_minutes
            
            # Update selected groups and collections
            import json
            if config.selected_groups is not None:
                logger.info(f"Updating selected_groups to: {config.selected_groups}")
                zotero_config.selected_groups = json.dumps(config.selected_groups)
            if config.selected_collections is not None:
                logger.info(f"Updating selected_collections to: {config.selected_collections}")
                zotero_config.selected_collections = json.dumps(config.selected_collections)
        
        await db.commit()
        
        # Test connection only if API credentials were updated
        if config.api_key or config.zotero_user_id or not existing_config:
            async with ZoteroService(db, current_user.id) as configured_service:
                connection_ok = await configured_service.test_connection()
                if not connection_ok:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid Zotero credentials or user ID"
                    )
        
        return ZoteroConfigResponse(
            configured=True,
            auto_sync_enabled=zotero_config.auto_sync_enabled,
            sync_interval_minutes=zotero_config.sync_interval_minutes,
            last_sync=zotero_config.last_sync.isoformat() if zotero_config.last_sync else None,
            last_sync_status=zotero_config.last_sync_status,
            selected_groups=json.loads(zotero_config.selected_groups) if zotero_config.selected_groups else None,
            selected_collections=json.loads(zotero_config.selected_collections) if zotero_config.selected_collections else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to configure Zotero: {e}")
        raise HTTPException(status_code=500, detail="Failed to configure Zotero")


@router.get("/status", response_model=ZoteroConfigResponse)
async def get_zotero_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ZoteroConfigResponse:
    """Get current Zotero configuration status."""
    try:
        from sqlalchemy import select
        from app.models import ZoteroConfig
        
        result = await db.execute(
            select(ZoteroConfig).where(ZoteroConfig.user_id == current_user.id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            return ZoteroConfigResponse(
                configured=False,
                auto_sync_enabled=False,
                sync_interval_minutes=0
            )
        
        return ZoteroConfigResponse(
            configured=True,
            auto_sync_enabled=config.auto_sync_enabled,
            sync_interval_minutes=config.sync_interval_minutes,
            last_sync=config.last_sync.isoformat() if config.last_sync else None,
            last_sync_status=config.last_sync_status,
            selected_groups=json.loads(config.selected_groups) if config.selected_groups else None,
            selected_collections=json.loads(config.selected_collections) if config.selected_collections else None
        )
    except Exception as e:
        logger.error(f"Failed to get Zotero status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Zotero status")


class ZoteroSyncRequest(BaseModel):
    """Request model for Zotero sync."""
    force_full_sync: bool = Field(False, description="Force a full sync ignoring last sync timestamp")


@router.post("/sync", response_model=ZoteroSyncResponse)
async def sync_zotero(
    sync_request: ZoteroSyncRequest = ZoteroSyncRequest(),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ZoteroSyncResponse:
    """Trigger a manual sync with Zotero."""
    try:
        logger.info(f"Starting Zotero sync for user {current_user.id} (force_full_sync={sync_request.force_full_sync})")
        
        # Run sync immediately (in production, this should be a background task)
        async with ZoteroService(db, current_user.id) as service:
            new_papers, updated_papers, failed_papers = await service.sync_library(
                force_full_sync=sync_request.force_full_sync
            )
        
        return ZoteroSyncResponse(
            success=True,
            new_papers=new_papers,
            updated_papers=updated_papers,
            failed_papers=failed_papers,
            message=f"Sync completed: {new_papers} new, {updated_papers} updated, {failed_papers} failed"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to sync Zotero: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync with Zotero")


@router.post("/test-connection")
async def test_zotero_connection(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Test the Zotero API connection."""
    try:
        async with ZoteroService(db, current_user.id) as service:
            connection_ok = await service.test_connection()
            
        return {
            "connected": connection_ok,
            "message": "Connection successful" if connection_ok else "Connection failed"
        }
    except ValueError as e:
        return {
            "connected": False,
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Failed to test Zotero connection: {e}")
        return {
            "connected": False,
            "message": "Connection test failed"
        }


@router.delete("/disconnect")
async def disconnect_zotero(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Disconnect Zotero integration."""
    try:
        from sqlalchemy import select, delete
        from app.models import ZoteroConfig, ZoteroSync
        
        # Delete sync records
        await db.execute(
            delete(ZoteroSync).where(ZoteroSync.user_id == current_user.id)
        )
        
        # Delete config
        await db.execute(
            delete(ZoteroConfig).where(ZoteroConfig.user_id == current_user.id)
        )
        
        await db.commit()
        
        return {"success": True, "message": "Zotero disconnected"}
    except Exception as e:
        logger.error(f"Failed to disconnect Zotero: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect Zotero")


@router.get("/groups")
async def get_zotero_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[dict]:
    """Get all Zotero groups accessible by the user."""
    try:
        async with ZoteroService(db, current_user.id) as service:
            groups = await service.fetch_groups()
        return groups
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch Zotero groups: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch groups")


@router.get("/collections")
async def get_zotero_collections(
    library_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[dict]:
    """Get all collections from a specific library or user's personal library."""
    try:
        async with ZoteroService(db, current_user.id) as service:
            collections = await service.fetch_collections(library_id)
        return collections
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch Zotero collections: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch collections")


@router.get("/sync/progress")
async def get_sync_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Get current sync progress."""
    try:
        async with ZoteroService(db, current_user.id) as service:
            progress = service.get_sync_progress()
        return progress
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get sync progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sync progress")


@router.get("/debug/config")
async def get_debug_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Get debug information about Zotero configuration."""
    try:
        from sqlalchemy import select
        from app.models import ZoteroConfig
        
        result = await db.execute(
            select(ZoteroConfig).where(ZoteroConfig.user_id == current_user.id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            return {"error": "No Zotero configuration found"}
        
        # Parse selected groups and collections
        selected_groups = []
        selected_collections = []
        
        if config.selected_groups:
            try:
                selected_groups = json.loads(config.selected_groups)
            except:
                selected_groups = ["Error parsing groups"]
                
        if config.selected_collections:
            try:
                selected_collections = json.loads(config.selected_collections)
            except:
                selected_collections = ["Error parsing collections"]
        
        return {
            "user_id": str(current_user.id),
            "zotero_user_id": config.zotero_user_id,
            "api_key_configured": bool(config.api_key),
            "auto_sync_enabled": config.auto_sync_enabled,
            "sync_interval_minutes": config.sync_interval_minutes,
            "last_sync": config.last_sync.isoformat() if config.last_sync else None,
            "last_sync_status": config.last_sync_status,
            "selected_groups": selected_groups,
            "selected_collections": selected_collections,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get debug config: {e}")
        return {"error": str(e)}