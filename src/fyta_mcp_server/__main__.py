#!/usr/bin/env python3
"""
Entry point for running fyta_mcp_server as a module
"""
import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())
