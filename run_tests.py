#!/usr/bin/env python3
"""
Test runner script for drf_recaptcha_enterprise.

This script runs the unit tests for the package without requiring Django setup.
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Run the unit tests."""
    # Get the project root directory
    project_root = Path(__file__).parent
    tests_dir = project_root / "drf_recaptcha_enterprise" / "tests"

    # Ensure we're in the project root
    os.chdir(project_root)

    # Add the project root to Python path
    sys.path.insert(0, str(project_root))

    # Run pytest with appropriate configuration
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(tests_dir),
        "-v",
        "--tb=short",
        "--strict-markers",
        "--strict-config",
        "--cov=drf_recaptcha_enterprise",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml",
        "--cov-fail-under=80",
        "-m",
        "not integration",  # Skip integration tests by default
    ]

    print("Running unit tests for drf_recaptcha_enterprise...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print("❌ Tests failed!")
        return e.returncode
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("⚠️  Tests interrupted by user")
        return 1


if __name__ == "__main__":
    sys.exit(main())
