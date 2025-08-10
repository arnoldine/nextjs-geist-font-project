#!/usr/bin/env python3
"""
Setup script for Simply Accounting application.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_requirements():
    """Check if required software is installed."""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Check if MySQL is available
    mysql_check = subprocess.run("mysql --version", shell=True, capture_output=True)
    if mysql_check.returncode == 0:
        print("✅ MySQL detected")
    else:
        print("⚠️  MySQL not detected - you'll need to install it")
    
    return True

def setup_virtual_environment():
    """Set up Python virtual environment."""
    if os.path.exists("venv"):
        print("✅ Virtual environment already exists")
        return True
    
    return run_command("python -m venv venv", "Creating virtual environment")

def install_dependencies():
    """Install Python dependencies."""
    # Determine the correct pip path
    if os.name == 'nt':  # Windows
        pip_path = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        pip_path = "venv/bin/pip"
    
    return run_command(f"{pip_path} install -r requirements.txt", "Installing dependencies")

def setup_database():
    """Set up database configuration."""
    print("\n📋 Database Setup")
    print("Please ensure you have:")
    print("1. MySQL server running")
    print("2. Created a database named 'simply_accounting'")
    print("3. Updated the .env file with your database credentials")
    
    response = input("\nHave you completed the above steps? (y/n): ")
    if response.lower() != 'y':
        print("Please complete the database setup and run this script again.")
        return False
    
    # Determine the correct alembic path
    if os.name == 'nt':  # Windows
        alembic_path = "venv\\Scripts\\alembic"
    else:  # Unix/Linux/macOS
        alembic_path = "venv/bin/alembic"
    
    return run_command(f"{alembic_path} upgrade head", "Running database migrations")

def main():
    """Main setup function."""
    print("🚀 Simply Accounting Setup")
    print("=" * 50)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Setup virtual environment
    if not setup_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("\n⚠️  Database setup skipped. You can run migrations later with:")
        print("   alembic upgrade head")
    
    print("\n🎉 Setup completed successfully!")
    print("\nTo start the application:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("   source venv/bin/activate")
    print("   python run.py")
    
    print("\nAPI Documentation will be available at:")
    print("   http://localhost:8000/docs")

if __name__ == "__main__":
    main()
