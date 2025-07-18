#!/usr/bin/env python3
"""Run the DOI migration to fix NULL constraint issues."""
import subprocess
import sys

def main():
    """Run the alembic migration."""
    print("Running DOI constraint fix migration...")
    
    try:
        # Run the migration
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Migration completed successfully!")
            print(result.stdout)
        else:
            print("✗ Migration failed!")
            print(result.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"✗ Error running migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()