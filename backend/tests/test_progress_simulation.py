"""
Simulate Zotero sync progress to demonstrate the progress bar functionality.
"""
import asyncio
import time
from app.services.zotero_service import ZoteroService
from unittest.mock import Mock
from uuid import uuid4


def create_progress_bar(current: int, total: int, bar_length: int = 40) -> str:
    """Create a visual progress bar."""
    if total == 0:
        return "[" + "-" * bar_length + "] 0.0%"
    
    percentage = (current / total) * 100
    filled_length = int(bar_length * current / total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    
    return f"[{bar}] {percentage:.1f}%"


async def simulate_sync_progress():
    """Simulate a Zotero sync with progress updates."""
    print("\n🔄 Simulating Zotero Sync Progress")
    print("=" * 60)
    
    # Create mock service
    mock_db = Mock()
    user_id = uuid4()
    service = ZoteroService(mock_db, user_id)
    
    # Simulate sync stages
    stages = [
        # Stage 1: Starting
        {
            "status": "starting",
            "message": "Initializing Zotero sync...",
            "duration": 1
        },
        # Stage 2: Fetching libraries
        {
            "status": "fetching",
            "message": "Fetching from 3 libraries...",
            "libraries_total": 3,
            "duration": 2,
            "substeps": [
                {"libraries_processed": 1, "message": "Fetched items from 1/3 libraries"},
                {"libraries_processed": 2, "message": "Fetched items from 2/3 libraries"},
                {"libraries_processed": 3, "message": "Fetched items from 3/3 libraries"}
            ]
        },
        # Stage 3: Processing papers
        {
            "status": "processing",
            "message": "Processing papers...",
            "total": 150,
            "duration": 5,
            "substeps": [
                {"current": 15, "message": "Processing papers... (15/150)"},
                {"current": 45, "message": "Processing papers... (45/150)"},
                {"current": 90, "message": "Processing papers... (90/150)"},
                {"current": 120, "message": "Processing papers... (120/150)"},
                {"current": 150, "message": "Processing papers... (150/150)"}
            ]
        },
        # Stage 4: Completed
        {
            "status": "completed",
            "message": "Sync completed: 25 new, 10 updated, 0 failed",
            "current": 150,
            "total": 150,
            "duration": 1
        }
    ]
    
    # Run simulation
    for stage in stages:
        print(f"\n📊 Stage: {stage['status'].upper()}")
        print("-" * 60)
        
        if "substeps" in stage:
            # Process substeps with animation
            for i, substep in enumerate(stage["substeps"]):
                # Update progress
                update_data = {
                    "status": stage["status"],
                    "message": substep["message"]
                }
                
                # Add all fields from stage and substep
                for key in ["total", "libraries_total"]:
                    if key in stage:
                        update_data[key] = stage[key]
                
                for key, value in substep.items():
                    if key != "message":
                        update_data[key] = value
                
                service._update_sync_progress(**update_data)
                
                # Get and display progress
                progress = service.get_sync_progress()
                
                # Create progress bar if applicable
                if progress.get("total", 0) > 0 and "current" in progress:
                    bar = create_progress_bar(progress["current"], progress["total"])
                    print(f"\r{bar} - {progress['message']}", end='', flush=True)
                else:
                    print(f"{progress['message']}")
                
                # Wait between updates
                await asyncio.sleep(stage["duration"] / len(stage["substeps"]))
            
            print()  # New line after progress bar
        else:
            # Simple stage update
            update_data = {
                "status": stage["status"],
                "message": stage["message"]
            }
            
            # Add any additional fields
            for key in ["current", "total", "libraries_total", "libraries_processed"]:
                if key in stage:
                    update_data[key] = stage[key]
            
            service._update_sync_progress(**update_data)
            
            # Display
            progress = service.get_sync_progress()
            
            if stage["status"] == "completed":
                print(f"✅ {progress['message']}")
            else:
                print(f"⏳ {progress['message']}")
            
            await asyncio.sleep(stage["duration"])
    
    print("\n" + "=" * 60)
    print("✅ Simulation completed!")
    
    # Show final progress state
    final_progress = service.get_sync_progress()
    print("\n📋 Final Progress State:")
    for key, value in final_progress.items():
        print(f"   {key}: {value}")


def demonstrate_progress_api():
    """Demonstrate how the progress API would be used."""
    print("\n📡 Progress API Demonstration")
    print("=" * 60)
    
    # Create mock service
    mock_db = Mock()
    user_id = uuid4()
    service = ZoteroService(mock_db, user_id)
    
    print("\n1️⃣ Initial state (idle):")
    progress = service.get_sync_progress()
    print(f"   Response: {progress}")
    
    print("\n2️⃣ During fetch:")
    service._update_sync_progress(
        status="fetching",
        libraries_processed=2,
        libraries_total=5,
        message="Fetching from library 2 of 5..."
    )
    progress = service.get_sync_progress()
    print(f"   Response: {progress}")
    
    print("\n3️⃣ During processing:")
    service._update_sync_progress(
        status="processing",
        current=75,
        total=150,
        message="Processing paper 75 of 150..."
    )
    progress = service.get_sync_progress()
    print(f"   Response: {progress}")
    bar = create_progress_bar(progress["current"], progress["total"])
    print(f"   Visual: {bar}")
    
    print("\n4️⃣ Completed:")
    service._update_sync_progress(
        status="completed",
        current=150,
        total=150,
        message="Sync completed successfully!"
    )
    progress = service.get_sync_progress()
    print(f"   Response: {progress}")
    
    print("\n📌 Frontend would poll this endpoint every 500ms during sync")
    print("📌 Progress bar updates smoothly as 'current' value increases")
    print("📌 Status changes trigger UI updates (spinner, progress bar, completion)")


if __name__ == "__main__":
    # Run demonstrations
    print("🚀 Zotero Progress Bar Functionality Test")
    
    # Show API usage
    demonstrate_progress_api()
    
    # Run animated simulation
    print("\n" + "=" * 60)
    print("Starting animated progress simulation...")
    asyncio.run(simulate_sync_progress())