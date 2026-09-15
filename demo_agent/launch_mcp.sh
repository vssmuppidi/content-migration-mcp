#!/bin/bash
# Launcher script for MCP server
cd "$(dirname "$0")/.."
exec python -m src.server

