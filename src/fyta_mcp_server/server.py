#!/usr/bin/env python3
"""
FYTA MCP Server - Main server setup and entry point
"""
import asyncio
import logging
import os
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .client import FytaClient
from .tools import get_tool_definitions
from .handlers import handle_tool_call

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fyta-mcp-server")


def create_fyta_server(email: str, password: str) -> Server:
    """Create and configure the FYTA MCP server"""

    server = Server("fyta-mcp-server")
    fyta_client = FytaClient(email, password)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available FYTA tools"""
        return get_tool_definitions()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls"""
        return await handle_tool_call(name, arguments, fyta_client)

    return server


async def main():
    """Main entry point"""
    # Get credentials from environment variables
    email = os.getenv("FYTA_EMAIL")
    password = os.getenv("FYTA_PASSWORD")

    if not email or not password:
        logger.error("FYTA_EMAIL and FYTA_PASSWORD environment variables must be set")
        sys.exit(1)

    logger.info("Starting FYTA MCP Server...")
    server = create_fyta_server(email, password)

    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
