#!/usr/bin/env python3
"""
Simple test script to verify the application starts correctly.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_app():
    """Test basic application functionality."""
    try:
        # Test imports
        print("Testing imports...")
        from app.main import app
        from app.core.config import settings
        from app.core.database import engine
        from app.models.user import User
        from app.services.auth import AuthService
        
        print("✅ All imports successful")
        
        # Test configuration
        print(f"✅ App Name: {settings.app_name}")
        print(f"✅ Environment: {settings.environment}")
        print(f"✅ Debug Mode: {settings.debug}")
        
        # Test database connection (without actually connecting)
        print(f"✅ Database URL configured: {settings.database_url[:20]}...")
        
        print("\n🎉 Application structure is valid!")
        print("\nNext steps:")
        print("1. Set up MySQL database")
        print("2. Update .env file with your database credentials")
        print("3. Run: alembic upgrade head")
        print("4. Run: python run.py")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_app())
    sys.exit(0 if success else 1)
