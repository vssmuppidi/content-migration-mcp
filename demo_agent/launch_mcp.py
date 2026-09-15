#!/usr/bin/env python3
"""Python launcher for MCP server - works with MCPTools"""
import sys
import os
from pathlib import Path

# Get project root (parent of demo_agent)
project_root = Path(__file__).parent.parent
os.chdir(project_root)

# Add to path
sys.path.insert(0, str(project_root))

# Import and run server
from src.server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())

