#!/usr/bin/env python3
"""
Dependency installation script for Replit environment.
Handles problematic packages that need special installation procedures.
"""

import os
import sys
import subprocess
import platform


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True,
                                check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False


def install_dependencies():
    """Install dependencies with special handling for problematic packages."""
    print("🚀 Installing dependencies for Inflection.io MCP Server")
    print("=" * 60)

    # Get system info
    print(f"📋 System: {platform.system()} {platform.release()}")
    print(f"📋 Python: {sys.version}")
    print(f"📋 Architecture: {platform.machine()}")

    # Step 1: Upgrade pip
    if not run_command("pip install --upgrade pip", "Upgrading pip"):
        print("⚠️  Pip upgrade failed, continuing anyway...")

    # Step 2: Install problematic packages first
    problematic_packages = [
        "pydantic_core",
        "rpds-py",
        "cryptography"
    ]

    for package in problematic_packages:
        if not run_command(f"pip install --no-cache-dir --force-reinstall {package}", f"Installing {package}"):
            print(
                f"⚠️  {package} installation failed, trying without force-reinstall...")
            if not run_command(f"pip install --no-cache-dir {package}", f"Installing {package} (retry)"):
                print(f"❌ Failed to install {package}")
                return False

    # Step 3: Install all requirements
    if not run_command("pip install --no-cache-dir -r requirements.txt", "Installing all requirements"):
        print("❌ Failed to install requirements")
        return False

    # Step 4: Verify critical packages
    critical_packages = [
        "fastapi",
        "pydantic",
        "mcp",
        "httpx",
        "structlog",
        "uvicorn"
    ]

    print("\n🔍 Verifying critical packages...")
    for package in critical_packages:
        try:
            __import__(package)
            print(f"✅ {package} imported successfully")
        except ImportError as e:
            print(f"❌ {package} import failed: {e}")
            return False

    print("\n🎉 All dependencies installed successfully!")
    return True


def main():
    """Main function."""
    success = install_dependencies()
    if not success:
        print("\n❌ Dependency installation failed!")
        print("💡 Try these troubleshooting steps:")
        print("   1. Restart the repl")
        print("   2. Check if all packages are compatible with Python 3.11")
        print("   3. Try installing packages one by one")
        sys.exit(1)

    print("\n✅ Ready to run the server!")


if __name__ == "__main__":
    main()
