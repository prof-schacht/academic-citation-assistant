"""Zotero API endpoints."""
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
    api_key: str = Field(..., description="Zotero API key")
    zotero_user_id: str = Field(..., description="Numeric Zotero user ID")
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
                zotero_config.selected_groups = json.dumps(config.selected_groups)
            if config.selected_collections is not None:
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
                zotero_config.selected_groups = json.dumps(config.selected_groups)
            if config.selected_collections is not None:
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
            last_sync_status=zotero_config.last_sync_status
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
            last_sync_status=config.last_sync_status
        )
    except Exception as e:
        logger.error(f"Failed to get Zotero status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Zotero status")


@router.post("/sync", response_model=ZoteroSyncResponse)
async def sync_zotero(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ZoteroSyncResponse:
    """Trigger a manual sync with Zotero."""
    try:
        # Run sync immediately (in production, this should be a background task)
        async with ZoteroService(db, current_user.id) as service:
            new_papers, updated_papers, failed_papers = await service.sync_library()
        
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